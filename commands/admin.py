from discord.ext import commands

class Util(commands.Cog):
    """Utility commands for bot management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, ext: str):
        """Restart given extension if found"""
        try:
            extension = 'commands.' + ext
            self.bot.reload_extension(extension)
            #print(f"Reloaded extension: {extension}")
            await ctx.author.send(f"Reloaded extension: {extension}")
        except Exception as e:
            error_message = f"Error on reloading extension: {e}"
            #print(error_message)
            await ctx.author.send(error_message)



def setup(bot):
    bot.add_cog(Util(bot))
