from discord.ext import commands
import discord
from library.common import checks


class Meta(commands.Cog):
    """Bot command utilities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def hello(self, ctx):
        """Displays my intro message."""
        await ctx.send('Hei!')

    @commands.command(hidden=True)
    @checks.is_staff()
    async def hello_staff(self, ctx):
        """Displays an test message for staff."""
        await ctx.send('Hei Staffilainen! :)')


def setup(bot):
    bot.add_cog(Meta(bot))