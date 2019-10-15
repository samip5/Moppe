from discord.ext import commands
import discord
import aiohttp
import arrow
import random


class Random(commands.Cog):
    """Random bot functions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['kissa', 'kisu'])
    async def cat(self, ctx):
        async with aiohttp.ClientSession() as ses:
            async with ses.get('https://aws.random.cat/meow') as response:
                ret = await response.json()
        e = discord.Embed(color=random.randint(1, 255 ** 3 - 1))
        e.set_image(url=ret['file'])
        e.set_author(name="Random.cat", url='https://random.cat')
        e.set_footer(text=f'Powered by random.cat.')
        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Random(bot))
