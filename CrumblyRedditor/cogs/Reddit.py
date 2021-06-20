import discord
from discord.ext import commands, tasks
import apraw as r
from asyncio import sleep
from datetime import datetime
from typing import Union, List, Tuple

class Post:
    def __init__(self, embed: discord.Embed, video: Union[str, None], is_nsfw: bool) -> None:
        self.embed = embed
        self.video = video
        self.is_nsfw = is_nsfw

    # Returns True if it actually sent the message
    async def send(self, channel: discord.TextChannel) -> bool:
        # Don't send NSFW image into non-NSFW channel
        if self.is_nsfw:
            if channel.is_nsfw():
                await channel.send(embed=self.embed)
                if self.video is not None:
                    await channel.send(self.video)
                return True
            return False
        else:
            await channel.send(embed=self.embed)
            if self.video is not None:
                await channel.send(self.video)
            return True

# I should maybe migrate more stuff to RedditManager
class RedditManager:
    def __init__(self, bot, r) -> None:
        self.bot = bot
        self.r = r

        self.reddit_colour = 0xFF4500

    async def is_sub(self, sub: str) -> bool:
        s = await self.r.subreddit(sub)
        return hasattr(s, "id")


    async def get_subs(self, guild: Union[discord.Guild, int]) -> Union[List[Tuple[str, str, int]], None]:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT subreddit, mode, amount FROM reddit_subs WHERE guild=?", (guild, ))
        subs = await cursor.fetchall()
        await cursor.close()
        return subs

    async def get_sub(self, guild: Union[discord.Guild, int], sub: str) -> Union[Tuple[str, str, int], None]:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT subreddit, mode, amount FROM reddit_subs WHERE guild=? AND subreddit=?", (guild, sub))
        s = await cursor.fetchone()
        await cursor.close()
        return s

    async def add_sub(self, guild: Union[discord.Guild, int], sub: str, mode: str, amount: int) -> None:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        await self.bot.aDB.execute("INSERT INTO reddit_subs (guild, subreddit, mode, amount) VALUES(?,?,?,?)", (guild, sub, mode, amount))
        await self.bot.aDB.commit()

    async def set_sub(self, guild: Union[discord.Guild, int], sub: str, mode: str, amount: int) -> None:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        await self.bot.aDB.execute("UPDATE reddit_subs SET mode=?, amount=? WHERE guild=? AND subreddit=?", (mode, amount, guild, sub))
        await self.bot.aDB.commit()

    async def del_sub(self, guild: Union[discord.Guild, int], sub: str) -> None:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        await self.bot.aDB.execute("DELETE FROM reddit_subs WHERE guild=? AND subreddit=?", (guild, sub))
        await self.bot.aDB.commit()

    async def get_channels(self, guild: Union[discord.Guild, int]) -> List[int]:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=?", (guild, ))
        channel_ids = await cursor.fetchall()
        await cursor.close()
        channels = [channel[0] for channel in channel_ids]
        return channels

    async def get_discord_channel(self, channel_id: int) -> discord.TextChannel:
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)
        return channel

    async def get_channel(self, channel: Union[discord.TextChannel, int], guild: Union[discord.Guild, int] = None) -> Union[Tuple[int], None]:
        if isinstance(channel, discord.TextChannel):
                channel = channel.id
        if guild is not None:
            if isinstance(guild, discord.Guild):
                guild = guild.id
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT channel, guild FROM reddit_channels WHERE guild=? AND channel=?", (guild, channel))
            c = await cursor.fetchone()
            await cursor.close()
        else:
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT channel, guild FROM reddit_channels WHERE channel=?", (channel, ))
            c = await cursor.fetchone()
            await cursor.close()
        return c

    async def add_channel(self, guild: Union[discord.Guild, int], channel: Union[discord.TextChannel, int]) -> None:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        if isinstance(channel, discord.TextChannel):
            channel = channel.id
        await self.bot.aDB.execute("INSERT INTO reddit_channels (guild, channel) VALUES(?,?)", (guild, channel))
        await self.bot.aDB.commit()

    async def del_channel(self, channel: Union[discord.TextChannel, int], guild: Union[discord.Guild, int] = None) -> None:
        if isinstance(channel, discord.TextChannel):
            channel = channel.id
        if guild is not None:
            if isinstance(guild, discord.Guild):
                guild = guild.id
            await self.bot.aDB.execute("DELETE FROM reddit_channels WHERE guild=? AND channel=?", (guild, channel))
            await self.bot.aDB.commit()
        else:
            await self.bot.aDB.execute("DELETE FROM reddit_channels WHERE channel=?", (channel, ))
            await self.bot.aDB.commit()

    async def get_discord_channels_from_list(self, channel_list: List[int]) -> List[discord.TextChannel]:
        channels = []
        for channel_id in channel_list:
            channel = await self.get_discord_channel(channel_id)
            channels.append(channel)
        return channels

    async def get_discord_channels(self, guild: Union[discord.Guild, int]) -> List[discord.TextChannel]:
        if isinstance(guild, discord.Guild):
            guild = guild.id
        channel_list = await self.get_channels(guild)
        channels = await self.get_discord_channels_from_list(channel_list)
        return channels

    async def get_post(self, sub: r.models.Subreddit, submission: r.models.Submission) -> Post:
        # Limit the amount of text to not exceed the embed limit
        if len(submission.selftext) < 2048:
            descr = submission.selftext
        else:
            descr = submission.selftext[:2045] + "..."
        embed = discord.Embed(title=submission.title, description=descr, url="https://www.reddit.com"+submission.permalink, colour=self.reddit_colour)

        author = await submission.author()
        embed.set_author(name=f"by u/{author.name}", icon_url=author.icon_img)
        embed.set_footer(text=f"{sub.display_name_prefixed}", icon_url=sub.icon_img)

        if submission.url.endswith(".png") or submission.url.endswith(".jpg") or submission.url.endswith(".jpeg") or submission.url.endswith(".gif"):
            embed.set_image(url=submission.url)

        if submission.is_video:
            video = submission.media['reddit_video']['fallback_url']
        else:
            video = None

        return Post(embed=embed, video=video, is_nsfw=submission.over_18)

    async def post(self, guild: Union[discord.Guild, int]):
        if isinstance(guild, discord.Guild):
            guild = guild.id

        # Get subreddit bundles
        subs = await self.get_subs(guild)

        # Store channels
        channels = await self.get_discord_channels(guild)

        # Maybe implement some subreddit/submission caching (not really necessary now since we only work with text)
        for sub in subs:
            subreddit = await self.r.subreddit(sub[0])
            if sub[1] == "top":
                async for submission in subreddit.top(limit=sub[2]):
                    post = await self.get_post(subreddit, submission)
                    for channel in channels:
                        await post.send(channel)

class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.reddit_colour = 0xFF4500
        self.subreddit_modes = ["top"]
        self.subreddit_limit = 15

        # Create table
        self.bot.DB.execute("CREATE TABLE IF NOT EXISTS reddit_subs (id INTEGER PRIMARY KEY, guild INTEGER, subreddit TEXT, mode TEXT, amount INTEGER)")
        self.bot.DB.execute("CREATE TABLE IF NOT EXISTS reddit_channels (id INTEGER PRIMARY KEY, guild INTEGER, channel INTEGER)")
        self.bot.DB.commit()

        # List of guild ids who have subreddits registered
        self.guilds = []

        # Check for subreddits in database
        cursor = self.bot.DB.cursor()
        for guild in self.bot.guilds:
            cursor.execute("SELECT reddit_subs.id, reddit_channels.id FROM reddit_subs JOIN reddit_channels ON reddit_subs.guild=reddit_channels.guild WHERE reddit_subs.guild=?", (guild.id, ))
            res = cursor.fetchone()
            if res is not None:
                self.guilds.append(guild.id)
        cursor.close()

        # Create reddit client
        self.r = r.Reddit(username=self.bot.cm.reddit.username,
                          password=self.bot.cm.reddit.password,
                          client_id=self.bot.cm.reddit.client_id,
                          client_secret=self.bot.cm.reddit.client_secret,
                          user_agent=self.bot.cm.reddit.user_agent)

        self.rm = RedditManager(bot=self.bot, r=self.r)

        # Start post loop
        # Posts some stuff every day
        # self.post_loop.start()
        self.bot.loop.create_task(self.start_post_loop())

    def cog_unload(self):
        # Close reddit instance
        self.bot.loop.create_task(self.r.close())

    # Start the post loop at a certain time
    async def start_post_loop(self):
        now = datetime.now()
        if now.hour < 17:
            then = datetime.today().replace(hour=17)
        else:
            then = datetime.today().replace(day=now.day+1, hour=17)
        delta = then - now
        await sleep(delta.seconds)
        self.post_loop.start()

    @tasks.loop(hours=24)
    async def post_loop(self):
        for guild in self.guilds:
            await self.rm.post(guild)

    @commands.group(name="reddit", aliases=['r'])
    async def reddit_cmd(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help("reddit")

    @reddit_cmd.group(name="run", aliases=["r", "post", "p"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def run_post(self, ctx):
        return await self.rm.post(ctx.guild)

    @reddit_cmd.group(aliases=["channels", "c"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def channel(self, ctx):
        # List all channels
        if ctx.invoked_subcommand is None:
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=?", (ctx.guild.id, ))
            channelids = await cursor.fetchall()
            await cursor.close()

            async def get_channel(cid: int) -> discord.TextChannel or None:
                c = self.bot.get_channel(cid)
                if c is None:
                    c =  await self.bot.fetch_channel(cid)
                return c

            channels = []
            for cid in channelids:
                c = await get_channel(cid[0])
                channels.append(f"- {c.mention}")
            embed = discord.Embed(title=f"Reddit channels for {ctx.guild.name}", description='\n'.join(channels), colour=self.reddit_colour)
            await ctx.send(embed=embed)

    @channel.command(name="add", aliases=["a"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, channel: discord.TextChannel):
        c = await self.rm.get_channel(channel, ctx.guild)
        if c is None:
            await self.bot.aDB.execute("INSERT INTO reddit_channels (guild, channel) VALUES(?,?)", (ctx.guild.id, channel.id))
            await self.bot.aDB.commit()
            if ctx.guild.id not in self.guilds:
                self.guilds.append(ctx.guild.id)
            embed = discord.Embed(title=f"Channel {channel.name} was added", description=f"Channel {channel.name} was added! I will start sending posts to that channel :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"Channel {channel.name} is already added", description=f"I'm already sending posts into that channel. No need to add it twice :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

    @channel.command(name="remove", aliases=["r"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remove_channel(self, ctx, channel: discord.TextChannel):
        c = await self.rm.get_channel(channel, ctx.guild)
        if c is not None:
            # Delete the channel
            await self.rm.del_channel(channel, ctx.guild)

            # Check if there are any other channels, if no, delete the guild from self.guilds
            c = await self.rm.get_channels(ctx.guild)
            if ctx.guild.id in self.guilds and c == []:
                self.guilds.remove(ctx.guild.id)
            embed = discord.Embed(title=f"Channel {channel.name} was removed", description=f"Channel {channel.name} was removed! I will no longer send posts to that channel :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"Channel {channel.name} was never added", description=f"I can't delete a channel that was never registered.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

    @reddit_cmd.group(aliases=["sub", "subs", "subreddits", "s"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def subreddit(self, ctx):
        # List all subreddits
        if ctx.invoked_subcommand is None:
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT subreddit, mode, amount FROM reddit_subs WHERE guild=?", (ctx.guild.id, ))
            bundles = await cursor.fetchall()
            await cursor.close()
            subs = []
            for bundle in bundles:
                subs.append(f"- r/{bundle[0]} | {bundle[1]} | {bundle[2]}")
            embed = discord.Embed(title=f"Subreddits for {ctx.guild.name}", description="Subreddit | Mode | Amount\n" + '\n'.join(subs), colour=self.reddit_colour)
            await ctx.send(embed=embed)

    @subreddit.command(name="add", aliases=["a"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add_subreddit(self, ctx, sub: str, mode: str = "top", amount: int = 5):
        if mode not in self.subreddit_modes:
            embed = discord.Embed(title=f"Mode {mode} isn't a valid mode.", description=f"Mode {mode} either doesn't exist or we don't support it.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        if amount > self.subreddit_limit:
            embed = discord.Embed(title=f"I can't post {amount} posts every day.", description=f"I can't post more than {self.subreddit_limit} posts every day.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        is_sub = await self.rm.is_sub(sub)
        if is_sub == False:
            embed = discord.Embed(title=f"Subreddit r/{sub} doesn't exist.", description=f"Couldn't find r/{sub}. Maybe you should create it!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        s = await self.rm.get_sub(ctx.guild, sub)
        # Subreddit doesn't exist
        if s is None:
            # Add the subreddit
            await self.rm.add_sub(ctx.guild, sub, mode, amount)

            # Add to guilds
            if ctx.guild.id not in self.guilds:
                self.guilds.append(ctx.guild.id)
            embed = discord.Embed(title=f"Subreddit r/{sub} was added", description=f"Subreddit r/{sub} was added! I will start sending posts from that subreddit :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        # Subreddit exists
        else:
            embed = discord.Embed(title=f"Subreddit r/{sub} is already added", description=f"I'm already sending posts from this subreddit. No need to add it twice :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

    @subreddit.command(name="set", aliases=["s"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set_subreddit(self, ctx, sub: str, mode: str = "top", amount: int = 5):
        if mode not in self.subreddit_modes:
            embed = discord.Embed(title=f"Mode {mode} isn't a valid mode.", description=f"Mode {mode} either doesn't exist or we don't support it.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        if amount > self.subreddit_limit:
            embed = discord.Embed(title=f"I can't post {amount} posts every day.", description=f"I can't post more than {self.subreddit_limit} posts every day.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        is_sub = await self.rm.is_sub(sub)
        if is_sub == False:
            embed = discord.Embed(title=f"Subreddit r/{sub} doesn't exist.", description=f"Couldn't find r/{sub}. Maybe you should create it!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        s = await self.rm.get_sub(ctx.guild, sub)

        # Subreddit doesn't exist
        if s is None:
            # Add the subreddit
            await self.rm.add_sub(ctx.guild, sub, mode, amount)

            # Add to guilds
            if ctx.guild.id in self.guilds:
                self.guilds.append(ctx.guild)
            embed = discord.Embed(title=f"Subreddit r/{sub} was added", description=f"Subreddit r/{sub} was added! I will start sending posts from that subreddit :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        # Subreddit exists
        else:
            # Add the subreddit
            await self.rm.set_sub(ctx.guild, sub, mode, amount)
            embed = discord.Embed(title=f"Subreddit r/{sub}'s updated", description=f"The settings for r/{sub} are now updated! I will use the new settings from this point onwards!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

    @subreddit.command(name="remove", aliases=["r"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def remove_subreddit(self, ctx, sub: str):
        is_sub = await self.rm.is_sub(sub)
        if is_sub == False:
            embed = discord.Embed(title=f"Subreddit r/{sub} doesn't exist.", description=f"Couldn't find r/{sub}. Maybe you should create it!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        s = await self.rm.get_sub(ctx.guild, sub)
        if s is not None:
            # Delete the channel
            await self.rm.del_sub(ctx.guild, sub)

            # Check if there are any other subs, if no, delete the guild from self.guilds
            s = await self.rm.get_subs(ctx.guild)
            if ctx.guild.id in self.guilds and s == [] or s is None:
                self.guilds.remove(ctx.guild.id)
            embed = discord.Embed(title=f"Subreddit r/{sub} was removed", description=f"Subreddit r/{sub} was removed! I will no longer send posts from that subreddit :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"Subreddit r/{sub} was never added", description=f"I can't delete a subreddit that was never registered.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Reddit(bot))