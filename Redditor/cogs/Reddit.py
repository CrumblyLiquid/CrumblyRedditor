import discord
from discord.ext import commands, tasks
import apraw as r
from asyncio import sleep
from datetime import datetime

# I should maybe migrate more stuff to RedditManager
class RedditManager:
    def __init__(self, r) -> None:
        self.r = r

    async def is_sub(self, sub: str) -> bool:
        s = await self.r.subreddit(sub)
        return hasattr(s, "id")

class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.reddit_colour = 0xFF4500

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

        self.rm = RedditManager(r=self.r)

        # Start post loop
        # Posts some stuff every day
        self.post.start()
        # self.bot.loop.create_task(self.start_post())

    def cog_unload(self):
        # Close reddit instance
        self.bot.loop.create_task(self.r.close())

    async def start_post(self):
        now = datetime.now()
        if now.hour < 17:
            then = datetime.today().replace(hour=17)
        else:
            then = datetime.today().replace(day=now.day+1, hour=17)
        delta = then - now
        await sleep(delta.seconds)
        self.post.start()

    @tasks.loop(hours=24)
    async def post(self):
        for guild in self.guilds:
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT subreddit, mode, amount FROM reddit_subs WHERE guild=?", (guild, ))
            subs = await cursor.fetchall()
            await cursor.close()
            # Get channel settings
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=?", (guild, ))
            channel_ids = await cursor.fetchall()
            await cursor.close()
            # Cache channels
            channels = []
            for channel_id in channel_ids:
                channel = self.bot.get_channel(channel_id[0])
                if channel is None:
                    channel = await self.bot.fetch_channel(channel_id[0])
                channels.append(channel)
            for sub in subs:
                subreddit = await self.r.subreddit(sub[0])
                if sub[1] == "top":
                    async for post in subreddit.top(limit=sub[2]):
                        # Should also add link to the original post on reddit
                        author = await post.author()
                        if len(post.selftext) < 2048:
                            descr = post.selftext
                        else:
                            descr = post.selftext[:2045] + "..."
                        embed = discord.Embed(title=post.title, description=descr, url="https://www.reddit.com"+post.permalink, colour=self.reddit_colour)
                        embed.set_author(name=f"by u/{author.name}", icon_url=author.icon_img)
                        embed.set_footer(text=f"r/{sub[0]}", icon_url=subreddit.icon_img)
                        if post.url.endswith(".png") or post.url.endswith(".jpg") or post.url.endswith(".jpeg") or post.url.endswith(".gif"):
                            embed.set_image(url=post.url)
                        for channel in channels:
                            # Don't send NSFW image into non-NSFW channel
                            if post.over_18:
                                if channel.is_nsfw():
                                    await channel.send(embed=embed)
                                    if post.is_video:
                                        await channel.send(post.media['reddit_video']['fallback_url'])
                            else:
                                await channel.send(embed=embed)
                                if post.is_video:
                                    await channel.send(post.media['reddit_video']['fallback_url'])

    @commands.group(name="reddit", aliases=['r'])
    async def reddit_cmd(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help("reddit")

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
        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=? AND channel=?", (ctx.guild.id, channel.id))
        c = await cursor.fetchone()
        await cursor.close()
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
        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=? AND channel=?", (ctx.guild.id, channel.id))
        c = await cursor.fetchone()
        await cursor.close()
        if c is not None:
            # Delete the channel
            await self.bot.aDB.execute("DELETE FROM reddit_channels WHERE guild=? AND channel=?", (ctx.guild.id, channel.id))
            await self.bot.aDB.commit()

            # Check if there are any other channels, if no, delete the guild from self.guilds
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT channel FROM reddit_channels WHERE guild=? AND channel=?", (ctx.guild.id, channel.id))
            c = await cursor.fetchone()
            await cursor.close()
            if ctx.guild.id in self.guilds and c is None:
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
    async def add_subreddit(self, ctx, sub: str, mode: str = "top", amount: int = 10):
        is_sub = await self.rm.is_sub(sub)
        if is_sub == False:
            embed = discord.Embed(title=f"Subreddit r/{sub} doesn't exist.", description=f"Couldn't find r/{sub}. Maybe you should create it!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT subreddit FROM reddit_subs WHERE guild=? AND subreddit=?", (ctx.guild.id, sub))
        s = await cursor.fetchone()
        await cursor.close()

        # Subreddit doesn't exist
        if s is None:
            # Add the subreddit
            await self.bot.aDB.execute("INSERT INTO reddit_subs (guild, subreddit, mode, amount) VALUES(?,?,?,?)", (ctx.guild.id, sub, mode, amount))
            await self.bot.aDB.commit()

            # Add to guilds
            if ctx.guild.id in self.guilds:
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
    async def set_subreddit(self, ctx, sub: str, mode: str = "top", amount: int = 10):
        is_sub = await self.rm.is_sub(sub)
        if is_sub == False:
            embed = discord.Embed(title=f"Subreddit r/{sub} doesn't exist.", description=f"Couldn't find r/{sub}. Maybe you should create it!", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT subreddit FROM reddit_subs WHERE guild=? AND subreddit=?", (ctx.guild.id, sub))
        s = await cursor.fetchone()
        await cursor.close()

        # Subreddit doesn't exist
        if s is None:
            # Add the subreddit
            await self.bot.aDB.execute("INSERT INTO reddit_subs (guild, subreddit, mode, amount) VALUES(?,?,?,?)", (ctx.guild.id, sub, mode, amount))
            await self.bot.aDB.commit()

            # Add to guilds
            if ctx.guild.id in self.guilds:
                self.guilds.append(ctx.guild.id)
            embed = discord.Embed(title=f"Subreddit r/{sub} was added", description=f"Subreddit r/{sub} was added! I will start sending posts from that subreddit :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

        # Subreddit exists
        else:
            # Add the subreddit
            await self.bot.aDB.execute("UPDATE reddit_subs mode=?, amount=? WHERE guild=? AND subreddit=?", (mode, amount, ctx.guild.id, sub))
            await self.bot.aDB.commit()
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

        cursor = await self.bot.aDB.cursor()
        await cursor.execute("SELECT subreddit FROM reddit_subs WHERE guild=? AND subreddit=?", (ctx.guild.id, sub))
        s = await cursor.fetchone()
        await cursor.close()
        if s is not None:
            # Delete the channel
            await self.bot.aDB.execute("DELETE FROM reddit_subs WHERE guild=? AND subreddit=?", (ctx.guild.id, sub))
            await self.bot.aDB.commit()

            # Check if there are any other subs, if no, delete the guild from self.guilds
            cursor = await self.bot.aDB.cursor()
            await cursor.execute("SELECT subreddit FROM reddit_subs WHERE guild=? AND subreddit=?", (ctx.guild.id, sub))
            s = await cursor.fetchone()
            await cursor.close()
            if ctx.guild.id in self.guilds and s is None:
                self.guilds.remove(ctx.guild.id)
            embed = discord.Embed(title=f"Subreddit r/{sub} was removed", description=f"Subreddit r/{sub} was removed! I will no longer send posts from that subreddit :)", colour=self.reddit_colour)
            return await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"Subreddit r/{sub} was never added", description=f"I can't delete a subreddit that was never registered.", colour=self.reddit_colour)
            return await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Reddit(bot))