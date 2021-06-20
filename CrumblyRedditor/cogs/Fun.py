import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(2, 240, commands.BucketType.user)
    @commands.command(brief="Redditor's latency",
                      short_doc="Get Redditor's latency to Discord servers",
                      description="Allows you to get Redditor's latency to Discord servers. Doesn't take in account your latency!")
    async def ping(self, ctx):
        embed = discord.Embed(title="Pong!", description=f"Ping: {round(self.bot.latency * 1000)}ms", color=self.bot.main_colour)
        return await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.command(hidden=True,
                      brief="Prints text into chat",
                      short_doc="Just prints text into chat",
                      description="Only prints text into chat. Why did I add this? Sometimes I wonder too...")
    async def print(self, ctx, *, text):
        embed = discord.Embed(title="Print", description=f"Text: {text}", color=self.bot.main_colour)
        embed.set_footer(text="Why did I add this?")
        return await ctx.reply(embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Fun(bot))