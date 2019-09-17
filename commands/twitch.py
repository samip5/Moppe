from discord.ext import tasks, commands
from twitch import TwitchClient

import discord
import datetime
import asyncio
import json
import logging

import config

#!!!!!!!https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html read before banging your head too long!

f_json = "twitch_channels.json"

poll_delay = 15*60

class Twitch(commands.Cog):
    """Bot utilities for twitch integration."""

    global logger
    logger = logging.getLogger("bot")

    def __init__(self, bot):
        self.bot = bot
        #self.poll_delay = 15*60
        self.channels = []
        self.active_streams = []
        self.module_ready = False

        self.notification_reciever = None

        self.twitch = TwitchClient(client_id=config.twitch_client_id)
        self.poll_channels.start()

    def cog_unload(self):
        self.poll_channels.cancel()
        logger.info(f"Unloading Twitch poll module")

    @commands.group()
    async def twitch(self, ctx):
        if ctx.invoked_subcommand is None:
            try:
                embed = discord.Embed(colour=0x000000, title=f'Twitch kanavat')
                embed.add_field(name = 'Lista',
                            value = f"Lista seuratuista kanavista: ?twitch lista\n",
                            inline = True)
                await ctx.send(embed = embed)
            except discord.Forbidden:
                await ctx.send("Ei oikeuksia.")

    @twitch.group(name="lista", aliases=['list'])
    async def dispaly_follow_list(self, ctx):
        """List channels we are following"""
        for c_id in self.channels:
            channel = self.twitch.channels.get_by_id(c_id)
            embed = discord.Embed(colour=0x00FF00,
                    title = channel.display_name,
                    url = channel.url,
                    description = f"{channel.status}\nSeuraajia: {channel.followers}",)
            embed.set_thumbnail(url = channel.logo)
            await ctx.send(embed = embed)

    @twitch.group(name="video")
    async def dispaly_channel_videos(self, ctx, cid: int):
        """List latest videos in channels"""
        #TODO: get videos by name instead cid
        try:
            videos = self.twitch.channels.get_videos(cid, limit=5, broadcast_type='archive,upload')
            if videos:
                embed = discord.Embed(colour=0x00FF00,
                        title = f"{videos[0].channel.display_name}",
                        url = f"{videos[0].channel.url}")
                for v in videos:
                    embed.add_field(name = f"{v.title}",
                            value = f"{v.url}",
                            inline = True)
                await ctx.send(embed = embed)
            else:
                await ctx.send(f"No videos found in channel id {cid}")
        except Exception as e:
            logger.warning(f"Error on twitch video: {e}")


    @twitch.group(name="lisaa_video", aliases=['add_video'])
    async def video_id_to_channel_id(self, ctx, v_id: int):
        """Add channel to follow list from video id"""
        #TODO: add user restriciotn!
        try:
            video = self.twitch.videos.get_by_id(v_id)
            if video:
                if int(video.channel.id) in self.channels:
                    await ctx.send("Kanava on jo listalla")
                else:
                    self.channels.append(video.channel.id)
                    self.save_channels()

                    embed = discord.Embed(colour=0xFF0000,
                            title = video.channel.display_name,
                            url = video.channel.url,
                            description = f"{video.channel.status}\nSeuraajia: {video.channel.followers}",)
                    embed.set_thumbnail(url = video.channel.logo)
                    await ctx.send(embed = embed)
                    logger.info(f"Käyttäjä {ctx.author.display_name} (Käyttäjän ID: {ctx.author.id}) lisäsi kanavan: {video.channel.name} (ID:{video.channel.id})")
            else:
                await ctx.send("Videota ei löytynyt")
        except Exception as e:
            logger.warning(f"Error on twitch lisaa: {e}")
            await ctx.send(f"Kanavan lisääminen ei onnistunut")

    @twitch.group(name="lisaa", aliases=['add'])
    async def name_to_channel_id(self, ctx, name: str):
        """Add channel to follow list from channel name"""
        #TODO: add user restriciotn!
        try:
            search = name.split("/")[-1:] #Jos url, otetaan lopusta kanavan nimi
            users = self.twitch.users.translate_usernames_to_ids(search)

            if len(users) == 1:
                if int(users[0].id) in self.channels:
                    await ctx.send("Kanava on jo listalla")
                else:
                    self.channels.append(users[0].id)
                    self.save_channels()

                    embed = discord.Embed(colour=0xFF0000,
                            title = users[0].display_name,
                            url = f"https://www.twitch.tv/{users[0].name}",
                            description = f"{users[0].bio}",)
                    embed.set_thumbnail(url = users[0].logo)
                    await ctx.send(embed = embed)
                    logger.info(f"Käyttäjä {ctx.author.display_name} (Käyttäjän ID: {ctx.author.id}) lisäsi kanavan: {users[0].name} (ID:{users[0].id})")
            else:
                await ctx.send(f"Haulla {search} löytyi {len(users)} käyttäjää.\n{[u for u in users]}")
        except Exception as e:
            logger.warning(f"Error on twitch lisaa: {e}")
            await ctx.send(f"Kanavan lisääminen ei onnistunut")

    @twitch.group(name="poista", aliases=['remove'])
    async def remove_from_list(self, ctx, c_name: str):
        """Remove a channel from followin list by channel name"""
        #should this be done with twitch.users.translate_usernames_to_ids ??
        #TODO: add user restriciotn!
        remove = None
        for c_id in self.channels:
            channel = self.twitch.channels.get_by_id(c_id)
            if channel.name == c_name or channel.display_name == c_name:
                remove = channel.id
                break
        if remove:
            embed = discord.Embed(colour=0xFF0000,
                    title = f"Poistetaan seurannasta: {channel.display_name}",
                    url = channel.url,
                    description = f"{channel.status}\nSeuraajia: {channel.followers}",)
            embed.set_thumbnail(url = channel.logo)
            await ctx.send(embed = embed)
            logger.info(f"Käyttäjä {ctx.author.display_name} (Käyttäjän ID: {ctx.author.id}) poisti kanavan: {channel.name} (ID:{channel.id})")

            self.channels.remove(c_id)
            self.save_channels()
        else:
            await ctx.send(f"Ei löydetty kanavaa: {c_name}")


    def save_channels(self):
        with open(f_json, 'w') as fp:
            json.dump(self.channels, fp, indent=4)
        logger.info(f"Tallennettu {len(self.channels)} kanavaa")

    def load_channels(self):
        try:
            with open(f_json, 'r') as fp:
                self.channels = json.load(fp)
        except:
            self.channels = []
        logger.info(f"Ladattu {len(self.channels)} kanavaa\n{self.channels}")


    async def poll_new_videos(self):
        global poll_delay
        time = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(seconds=poll_delay)
        #time = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(hours=24)
        logger.info(f"Tarkistetaan viimeisimpiä Twitch videoita...")
        for cid in self.channels:
            try:
                videos = self.twitch.channels.get_videos(cid, limit=1, broadcast_type='archive,upload')
                if videos and videos[0]['published_at'] > time:
                    embed = discord.Embed(colour=0x0000FF,
                            title = f"Video: {videos[0].channel.display_name}",
                            url = videos[0].url,
                            description = f"{videos[0].title}\nat: {videos[0].game}",)
                    embed.set_thumbnail(url = videos[0].channel.logo)
                    await self.notification_reciever.send(embed=embed)
            except Exception as e:
                logger.warning(f"Error on twitch poll videos: {e}")

    async def poll_active_streams(self):
        if len(self.channels):
            # Returns most popular streams when queried with empty list
            streams = self.twitch.streams.get_live_streams(self.channels, limit=100)
        else:
            streams = []

        new_active = []
        for stream in streams:
            new_active.append(stream.id)
            if stream.id not in self.active_streams:
                embed = discord.Embed(colour=0xFF0000,
                        title = f"Stream: {stream.channel.display_name}",
                        url = stream.channel.url,
                        description = f"{stream.channel.status}\nat: {stream.channel.game}",)
                embed.set_thumbnail(url = stream.channel.logo)
                await self.notification_reciever.send(embed=embed)
        self.active_streams = new_active.copy()
        logger.info(f"Tarkistetaan aktiivisia Twitch streameja: {[s.channel.display_name for s in streams]}")

    @tasks.loop(seconds = poll_delay)
    async def poll_channels(self):
        if self.module_ready:
            await self.poll_active_streams()
            await self.poll_new_videos()
        else:
            logger.info(f"Twitch poll module not yet fully loaded")

    @poll_channels.before_loop
    async def before_poll_channels(self):
        await self.bot.wait_until_ready()
        self.load_channels()
        logger.info(f"Preloading Twitch poll module")
        self.module_ready = True
        if hasattr(config, "my_master_id") and config.my_master_id:
            self.notification_reciever = self.bot.get_user(config.my_master_id)
            #print(self.notification_reciever)


#DONE: save streams status and send only starting streams
#TODO: live stream posts handle, when stream is over, del post
#DONE: get latest videos and notify new videos

def setup(bot):
    bot.add_cog(Twitch(bot))
