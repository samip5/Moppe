import traceback
import sys
from discord.ext import commands
import discord


class CommandErrorHandler(commands.Cog):
    global logger

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""

        automation_channel = self.bot.get_channel(532946068967784508)
        terminal_channel = self.bot.get_channel(538343157788704768)

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound, commands.UserInputError)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} on poistettu käytöstä.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass
        elif isinstance(error, commands.NotOwner):
            return await ctx.send(f'Tämä komento on ainoastaan botin omistajalle, joka sinä et valitettavasti ole.')
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(f'Tämä komento vaatii oikeuksia, mitä sinulla ei valitettavasti ole.')
        elif isinstance(error, commands.CheckFailure):
            await ctx.message.delete()
            return await ctx.send(f'Komennon oikeuksien tarkistuksessa tapahtui virhe, tarkista oletko oikealla '
                                  f'kanavalla sekä onko sinulla siihen oikeuksia.',
                                  delete_after=5)
        elif isinstance(error, commands.CommandInvokeError):
            logger.exception("Tapahtui virhe komennossa '{}'".format(
                ctx.command.qualified_name), exc_info=error.original)
            oneliner = "Virhe komennossa '{}' - {}: {}".format(
                ctx.command.qualified_name, type(error.original).__name__,
                str(error.original))
            await ctx.send(oneliner)
            await automation_channel.send(oneliner)

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            print(traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr))


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
