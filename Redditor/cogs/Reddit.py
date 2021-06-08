import discord
from discord.ext import commands, tasks
import apraw as r

class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.r = r.Reddit(client_id=self.bot.config.reddit.client_id,
                          client_secret=self.bot.config.reddit.client_secret,
                          user_agent=self.bot.config.reddit.user_agent)

        # Start post loop
        # Posts some stuff every day
        self.post.start()

    @tasks.loop(hours=24)
    async def post(self):
        pass


    @commands.group(name="reddit", aliases=['r'])
    async def reddit_cmd(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.bot.get_command("reddit"))

    @reddit_cmd.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        pass

    @reddit_cmd.group()
    async def subreddit(self, ctx):
        pass

    @subreddit.command()
    async def add(self, ctx, sub: str):
        pass

    @subreddit.command()
    async def remove(self, ctx, sub: str):
        pass

def setup(bot):
    bot.add_cog(Reddit(bot))