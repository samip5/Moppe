from discord.ext import commands
import discord
import logging
from library.common import checks
import datetime
import socket


class Meta(commands.Cog):
    """Bot command utilities."""
    global logger
    logger = logging.getLogger("bot")

    def __init__(self, bot):
        self.bot = bot

    def get_bot_uptime(self):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if days:
            fmt = '{d} päivää, {h} tuntia ja {m} minuuttia'
        elif hours < 1:
            fmt = '{m} minuuttia, ja {s} sekunttia'
        else:
            fmt = '{h} tuntia, {m} minuuttia, ja {s} sekunttia'
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command()
    async def uptime(self, ctx):
        """Kertoo kuinka kauan botti on ollut päällä."""
        await ctx.send('Uptime: **{}**'.format(self.get_bot_uptime()))

    @commands.command(name="about", aliases=['tietoa'])
    async def about_me(self, ctx):
        """Kertoo botista tietoja"""
        result = ['**Tietoja botista:**']
        result.append(f'- Bot ID: {self.bot.user.name} (Discord ID: {self.bot.user.id})')
        result.append('- Aloitettu kehittämään: 04.07.2019')
        result.append(f'- Kirjasto: discord.py (Versio: {discord.__version__})')
        result.append(f'- Järjestelmän hostname: {socket.gethostname()}')
        result.append(f'- Käynnissäolo aika: {self.get_bot_uptime()}')
        await ctx.send('\n'.join(result))

    @commands.command(hidden=True)
    async def hello(self, ctx):
        """Displays my intro message."""
        await ctx.send('Hei!')

    @commands.command(hidden=True)
    @checks.is_staff()
    async def hello_staff(self, ctx):
        """Displays an test message for staff."""
        await ctx.send('Hei Staffilainen! :)')

    @commands.command(enabled=False)
    async def test_command(self, ctx):
        await ctx.send("Hei.")


def setup(bot):
    bot.add_cog(Meta(bot))