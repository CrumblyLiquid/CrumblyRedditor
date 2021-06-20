import discord
from discord.ext import commands

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['set'],
                    brief="Customize the bot",
                    short_doc="Allows you to change settings",
                    description="Allows you to customize various aspects of Redditor")
    @commands.cooldown(4, 30, commands.BucketType.user)
    async def settings(self, ctx):
        pass

    @settings.command(name="prefix",
                      brief="Set command prefix",
                      short_doc="Allows you to view or set command prefix",
                      description="Allows you to customize or view your Redditor's command prefix.")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def prefix(self, ctx, p: str = None):
        if p is None:
            p = await self.bot.pm.a_get(ctx.guild.id)
            embed = discord.Embed(title=f"Prefix for {ctx.guild.name}", description=f"Prefix: `{p}`", color=self.bot.main_colour)
            return await ctx.reply(embed=embed, mention_author=False)
        await self.bot.pm.a_set(ctx.guild.id, p)
        embed = discord.Embed(title=f"Prefix for {ctx.guild.name}", description=f"Prefix: `{p}`", color=self.bot.main_colour)
        return await ctx.reply(embed=embed, mention_author=False)

    # So we can use r/prefix instead of r/settings prefix
    @commands.command(name="prefix",
                      hidden=True,
                      brief=f"Shortcut for r/settings prefix",
                      short_doc="Shortcut for r/settings prefix",
                      description="Shortcut for r/settings prefix")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(2, 60, commands.BucketType.user)
    async def prefix_alias(self, ctx, p: str = None):
        await ctx.invoke(self.bot.get_command("settings prefix"), p)

def setup(bot):
    bot.add_cog(Settings(bot))