import traceback
import sys
import config
from discord.ext import commands
import discord
import logging


class CommandErrorHandler(commands.Cog):
    global logger
    logger = logging.getLogger("bot")

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception"""
        if config.in_production:
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
            logger.info(f"{ctx.command} on poistettu käytöstä, mutta sitä yritettiin silti käyttää.")
            return await ctx.send(f'{ctx.command} on poistettu käytöstä.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                logger.info(f"Komentoa {ctx.command} yritettiin käyttää yksityisviestissä käyttäjän {ctx.author.display_name} "
                            f"(Käyttäjän ID: {ctx.author.id}) toimesta, mutta sitä ei ole sallittu.")
                return await ctx.author.send(f'{ctx.command} ei voida käyttää yksityisviesteissä.')
            except:
                pass

        elif isinstance(error, commands.NotOwner):
            logger.info(f"Komentoa {ctx.command} yritettiin käyttää vaikka ei ole Botin omistaja. "
                        f"Käyttäjä oli {ctx.author.display_name} (ID: {ctx.author.id}).")
            return await ctx.send(f'Tämä komento on ainoastaan botin omistajalle, joka sinä et valitettavasti ole.')

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(f'Tämä komento vaatii oikeuksia, mitä sinulla ei valitettavasti ole.')

        elif isinstance(error, commands.CheckFailure):
            logger.warning(f"Komennon {ctx.command} oikeuksien tarkistuksessa tapahtui virhe.")
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
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            print(traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr))


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
