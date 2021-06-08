import discord
from discord.ext import commands
from time import strftime
from sys import stderr
from traceback import print_exception, format_exception

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    def get_error_embed(self, ctx):
        embed=discord.Embed(title='An error occured while trying to execute this command', description=f'My brain stopped working while performing your command.\n\nThis error has been reported and will be hopefully resolved shortly. Excuse the inconvinience.\nIf this issue persists contact Jaro#5648.', color=0xff0000)
        embed.set_footer(text=f'{self.bot.user.name} by Jaro#5648')
        return embed

    def get_report_embed(self, ctx, error):
        if ctx.cog is None:
            cog_quialified_name = "None"
        else:
            cog_quialified_name = ctx.cog.qualified_name
        if (ctx.guild is None):
            guild_name = "None"
            guild_id = "None"
            channel_name = "None"
        else:
            guild_name = ctx.guild.name
            guild_id = ctx.guild.id
            channel_name = ctx.channel.name

        message = f'**Cog:** {cog_quialified_name}\n**Guild:** {guild_name}\n**Guild ID:** {guild_id}\n**Channel:** {channel_name}\n**Channel ID:** {ctx.channel.id}\n**Message:** {ctx.message.content}\n**Message ID:** {ctx.message.id}\n**Message sent at:** {ctx.message.created_at.strftime("%H:%M:%S %d.%m.%Y")}\n**Author:** {ctx.author.name}#{ctx.author.discriminator}\n**Author ID:** {ctx.author.id}'
        embed=discord.Embed(title=f'{type(error).__name__}', description=message, color=0xff0000)
        error_msg = f'Ignoring exception in command {ctx.command}:\n{"".join(format_exception(type(error), error, error.__traceback__))}'
        if len(error_msg) < 1019:
            embed.add_field(name='\u200b', value=f'```{error_msg}```', inline=False)
        elif len(error_msg) > 1018*25:
            embed.add_field(name='\u200b', value=f'```See stderr```', inline=False)
        else:
            error_list = [error_msg[i:i+1018] for i in range(0, len(error_msg), 1018)]
            for err in error_list:
                embed.add_field(name='\u200b', value=f'```{err}```', inline=False)
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        error = getattr(error, 'original', error)

        ignored = ()
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'I was told I can\'t perform this command for now.')

        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f'Command is on cooldown. Timeout: {round(error.retry_after)}sec')

        elif isinstance(error, commands.CommandNotFound):
            return await ctx.send(f'I don\'t know this command... maybe you misspelled it?')

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f'Missing argument... dunno what to do :/')

        elif isinstance(error, commands.TooManyArguments):
            return await ctx.send(f'WOAH! Too many arguments!')

        elif isinstance(error, commands.BadArgument):
            return await ctx.send(f'Invalid argument... dunno what to do :/')

        elif isinstance(error, commands.NotOwner):
            return await ctx.send(f'Only my owner can do that :D')

        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(f'You don\'t have permissions to do that. Good try :D')

        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(f'I don\'t have permissions to do that :/')

        elif isinstance(error, commands.MissingRole):
            if type(error.missing_role) is str:
                message = f'You can\'t do that :/ (Insufficient role: {error.missing_role}'
            elif type(error.missing_roles) is list:
                message = f'You can\'t do that :/ (Insufficient roles: {error.missing_role}'
            return await ctx.send(message)

        elif isinstance(error, commands.CommandError):
            return await ctx.send(f'Something went wrong while executing this command.')

        elif isinstance(error, commands.CommandInvokeError):
            return await ctx.send(f'Something went wrong while invoking this command')

        elif isinstance(error, commands.ExtensionFailed):
            return await ctx.send(f'{error.name}: {error.original}')

        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send('This command can not be used in Private Messages.')

        appinfo = await self.bot.application_info()
        owner = appinfo.owner
        await owner.send(embed=self.get_report_embed(ctx, error))
        await ctx.send(embed=self.get_error_embed(ctx))

        print('Ignoring exception in command {}:'.format(ctx.command), file=stderr)
        print_exception(type(error), error, error.__traceback__, file=stderr)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))