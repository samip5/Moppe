from discord.ext import commands
from twitch import TwitchClient

import discord
import datetime
import asyncio
import urllib.request
import json
import pickle

import config

from library import sources

#TODO: https://dev.twitch.tv/docs/v5/#translating-from-user-names-to-user-ids
#TODO: https://github.com/tsifrer/python-twitch-client/blob/master/twitch/api/base.py

f_name = "twitch_channels.picle"
f_json = "twitch_channels.json"

class Watch(commands.Cog):
    """Bot utilities for twitch integration."""
    def __init__(self, bot):
        self.bot = bot
        self.poll_delay = 15*60
        self.channels = [227024705, 54693094, 87740957]
        self.active_streams = []
        self.twitch = TwitchClient(client_id=config.twitch_client_id)
        self.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        #possibly crates multiple tasks when reloaded
        self.heartbeat_task = self.bot.loop.create_task(self.poll_channels())

        #self.save_channels()
        self.load_channels()

    @commands.group()
    async def twitch(self, ctx):
        if ctx.invoked_subcommand is None:
            try:
                embed = discord.Embed(colour=0x000000, title=f'Twitch kanavat')
                embed.add_field(name='Lista',
                            value=f"Lista seuratuista kanavista: ?twitch lista\n",
                            inline=True)
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("Ei oikeuksia.")

    @twitch.group(name="lista", aliases=['list'])
    async def dispaly_follow_list(self, ctx):
        """List channels we are following"""
        #print(self.twitch.channels.get_by_id(self.channels[0]))
        #listed_channels = "\n"
        for c_id in self.channels:
            channel = self.twitch.channels.get_by_id(c_id)

            embed = discord.Embed(colour=0x00FF00,
                        title = channel.display_name,
                        url = channel.url,
                        description = f"{channel.status}\nSeuraajia: {channel.followers}",)
            embed.set_thumbnail(url=channel.logo)

            #listed_channels += f'{channel.name} \n'
            await ctx.send(embed = embed)
        #print (listed_channels)

    @twitch.group(name="video")
    async def dispaly_channel_videos(self, ctx, cid: int):
        """List latest videos in channels"""
        #TODO: get videos by name instead cid
        try:
            videos = self.twitch.channels.get_videos(cid, limit=5, broadcast_type='archive,upload')
            #print(len(videos))
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
            print ('Error on twitch video:\n', e)


    @twitch.group(name="lisaa", aliases=['add'])
    async def video_id_to_channel_id(self, ctx, vid: int):
        """Add channel to follow list"""
        #TODO: add user restriciotn!
        #TODO: add failed notification to user
        #TODO: add channel by id
        message = ''
        try:
            video = self.twitch.videos.get_by_id(vid)
            if video:
                if video.channel.id in self.channels:
                    await ctx.send("That channel is allready added")
                else:
                    message += str(video.channel.id) + ' ' + video.channel.name + ' ' + video.channel.status
                    self.channels.append(video.channel.id)
                    self.save_channels()

                    channel = video.channel
                    embed = discord.Embed(colour=0xFF0000,
                                title = channel.display_name,
                                url = channel.url,
                                description = f"{channel.status}\nSeuraajia: {channel.followers}",)
                    embed.set_thumbnail(url=channel.logo)
                    await ctx.send(embed = embed)
            print(message)
        except Exception as e:
            print ('Error on twitch lisaa:\n', e)

    @twitch.group(name="poista", aliases=['remove'])
    async def remove_from_list(self, ctx, c_name: str):
        """Remove a channel from followin list by channel name"""
        remove = None
        for c_id in self.channels:
            channel = self.twitch.channels.get_by_id(c_id)
            if channel.name == c_name or channel.display_name == c_name:
                ermove = channel.id
        if remove:
            embed = discord.Embed(colour=0xFF0000,
                        title = f"Poistetaan seurannasta: {channel.display_name}",
                        url = channel.url,
                        description = f"{channel.status}\nSeuraajia: {channel.followers}",)
            embed.set_thumbnail(url=channel.logo)
            await ctx.send(embed = embed)
            print(f"Poistetaan seurannasta: {channel.display_name}")

            self.channels.remove(c_id)
            self.save_channels()
        else:
            await ctx.send(f"Not found channel: {c_name}")


    '''
    @commands.command(hidden=True)
    '''

    def save_channels(self):
        with open(f_name, 'wb') as fp:
            pickle.dump(self.channels, fp)
        with open(f_json, 'w') as fp:
            json.dump(self.channels, fp, indent=4)
        print(f"saved channels {len(self.channels)}")

    def load_channels(self):
        try:
            with open(f_name, 'rb') as fp:
                self.channels = pickle.load(fp)
            with open(f_json, 'r') as fp:
                self.channels = json.load(fp)
        except:
            self.channels = []
        print(f"channels loaded: {len(self.channels)}\n{self.channels}")


    async def poll_new_videos(self, reciever):
        time = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(seconds=self.poll_delay)
        #time = datetime.datetime.now().replace(microsecond=0) - datetime.timedelta(hours=24)
        for cid in self.channels:
            try:
                videos = self.twitch.channels.get_videos(cid, limit=1, broadcast_type='archive,upload')
                if videos and videos[0]['published_at'] > time:
                    embed = discord.Embed(colour=0x0000FF,
                                title = f"Video: {videos[0].channel.display_name}",
                                url = videos[0].url,
                                description = f"{videos[0].title}\nat: {videos[0].game}",)
                    embed.set_thumbnail(url = videos[0].channel.logo)
                    await reciever.send(embed=embed)
            except Exception as e:
                print ('Error on twitch poll videos.:\n', e)

    async def send_stream_notification(self, reciever, stream):
        try:
            embed = discord.Embed(colour=0xFF0000,
                        title = f"Stream: {stream.channel.display_name}",
                        url = stream.channel.url,
                        description = f"{stream.channel.status}\nat: {stream.channel.game}",)
            embed.set_thumbnail(url = stream.channel.logo)
            await reciever.send(embed=embed)
        except Exception as e:
            print ('Error on twitch stream notif.:\n', e)

    async def poll_channels(self):
        await self.bot.wait_until_ready()
        while True:
            if len(self.channels):
                # Returns most popular streams when queried with empty list
                streams = self.twitch.streams.get_live_streams(self.channels, limit=100)
            else:
                streams = []

            message = f'{datetime.datetime.now().replace(microsecond=0)}, {len(streams)} streams active out of {len(self.channels)}: {[s.channel.display_name for s in streams]}'

            print(message)
            if hasattr(config, "my_master_id") and config.my_master_id:
                user = self.bot.get_user(config.my_master_id)
                await user.send(message)
                new_active = []
                for s in streams:
                    new_active.append(s.id)
                    if s.id not in self.active_streams:
                        await self.send_stream_notification(user, s)
            self.active_streams = new_active.copy()

            await self.poll_new_videos(user)

            await asyncio.sleep(self.poll_delay)

#DONE: save streams status and send only starting streams
#TODO: live stream posts handle, when stream is over, del post
#TODO: get latest videos and notify new videos

def setup(bot):
    bot.add_cog(Watch(bot))
