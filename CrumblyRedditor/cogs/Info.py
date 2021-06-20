import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(aliases=['announce'], hidden=True)
    async def announcement(self, ctx, *, message):
        embed=discord.Embed(title='**Announcement**', description=message, color=0x1c84ce)
        embed.set_footer(text=f'{self.bot.user.name} by Jaro#5648')
        owners = []
        for guild in self.bot.guilds:
            if guild.owner is None:
                owner = self.bot.get_user(guild.owner_id)
                if owner is None:
                    owner = await self.bot.fetch_user(guild.owner_id)
            else:
                owner = guild.owner
            if owner not in owners:
                owners.append(owner)
        for owner in owners:
            await owner.send(embed=embed)
        await ctx.reply(embed=embed, mention_author=False)

def setup(bot):
    bot.add_cog(Info(bot))