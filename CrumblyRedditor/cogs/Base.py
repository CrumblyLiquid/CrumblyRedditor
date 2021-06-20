import discord
from discord.ext import commands
from os import walk, sep
from typing import Optional

class CogManager():
    def __init__(self, bot) -> None:
        self.bot = bot

        self.all_list = self.all(full=True)
        self.loaded_list = self.loaded(full=True)
        self.unloaded_list = self.unloaded(full=True)

    def get_cog(self, name: str) -> str:
        return name.split(".")[-1]

    def get_full_cog(self, name: str) -> Optional[str]:
        for subdir, dirs, files in walk(self.bot.COGS_FOLDER):
            for filename in files:
                cog_path = subdir + sep + filename
                if cog_path.endswith(".py"):
                    if (filename[:-3] == name):
                        # Get relative path
                        cog_name = cog_path.replace(str(self.bot.COGS_FOLDER), "")
                        # Remove first slash and .py
                        cog_name = cog_name[1:-3]
                        cog_name = "cogs." + cog_name
                        return cog_name
        return None

    def all(self, full: bool = False) -> list:
        cogs = []
        for subdir, dirs, files in walk(self.bot.COGS_FOLDER):
            for filename in files:
                cog_path = subdir + sep + filename
                if cog_path.endswith(".py"):
                    if (full is True):
                        # Get relative path
                        cog_name = cog_path.replace(str(self.bot.COGS_FOLDER), "")
                        # Remove first slash and .py
                        cog_name = cog_name[1:-3]
                        cog_name = "cogs." + cog_name
                    else:
                        cog_name = filename[:-3]
                    cogs.append(cog_name)
        return cogs

    def loaded(self, full: bool = False) -> list:
        cogs = []
        if (full is False):
            cogs = self.bot.cogs
        else:
            for subdir, dirs, files in walk(self.bot.COGS_FOLDER):
                for filename in files:
                    cog_path = subdir + sep + filename
                    if cog_path.endswith(".py") and filename[:-3] in self.bot.cogs:
                        # Get relative path
                        cog_name = cog_path.replace(str(self.bot.COGS_FOLDER), "")
                        # Remove first slash and .py
                        cog_name = cog_name[1:-3]
                        cog_name = "cogs." + cog_name
                        cogs.append(cog_name)
        return cogs

    def unloaded(self, full: bool = False) -> list:
        cogs = []
        for subdir, dirs, files in walk(self.bot.COGS_FOLDER):
            for filename in files:
                cog_path = subdir + sep + filename
                if cog_path.endswith(".py") and filename[:-3] not in self.bot.cogs:
                    if (full is True):
                        # Get relative path
                        cog_name = cog_path.replace(str(self.bot.COGS_FOLDER), "")
                        # Remove first slash and .py
                        cog_name = cog_name[1:-3]
                        cog_name = "cogs." + cog_name
                    else:
                        cog_name = filename[:-3]
                    cogs.append(cog_name)
        return cogs

    async def load(self, cog: str) -> None:
        self.bot.load_extension(cog)
        self.unloaded_list.remove(cog)
        self.loaded_list.append(cog)

    async def unload(self, cog: str) -> None:
        self.bot.unload_extension(cog)
        self.loaded_list.remove(cog)
        self.unloaded_list.append(cog)

    async def reload(self, cog: str) -> None:
        self.bot.reload_extension(cog)

class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cgm = CogManager(self.bot)

    @commands.command(name="h", hidden=True)
    @commands.cooldown(6, 60, commands.BucketType.user)
    async def help_alias(self, ctx, *, command: str = None):
        if command is None:
            return await ctx.send_help()
        return await ctx.send_help(command)

    # Commads for managing cogs: /cogs <load/unload/reload> <cog/all> or /cogs list <all/loaded/unloaded>
    @commands.group(aliases = ['cog', 'c'], hidden=True)
    @commands.is_owner()
    async def cogs(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.all(ctx)

    @cogs.command(hidden=True)
    @commands.is_owner()
    async def debug(self, ctx):
        self.cgm.all_list = self.cgm.all(full=True)
        self.cgm.loaded_list = self.cgm.loaded(full=True)
        self.cgm.unloaded_list = self.cgm.unloaded(full=True)

    # Load unload and reload: maybe replace searching for .py file with exception Extension.NotFound, etc.
    @cogs.command(aliases = ['l'], hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, specified_cog = None):
        if specified_cog in ['all', 'a', None]:
            message = '```fix\nCogs succesfully loaded:```'
            loadedcogs = []
            for cog in self.cgm.unloaded(True):
                self.bot.load_extension(cog)
                loadedcogs.append(self.cgm.get_cog(cog))
            message += '```diff\n'
            for lcog in loadedcogs:
                message += f'+ {lcog}\n'
            message += '```'
            return await ctx.send(message)
        else:
            if specified_cog in self.cgm.unloaded():
                self.bot.load_extension(self.cgm.get_full_cog(specified_cog))
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' succesfully loaded.```')
            elif specified_cog in self.cgm.all():
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' already loaded.```')
            else:
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' not found.```')

    @cogs.command(aliases = ['unl', 'ul', 'un', 'u'], hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, *, specified_cog = None):
        if specified_cog in ['all', 'a', None]:
            message = '```fix\nCogs succesfully unloaded:```'
            unloadedcogs = []
            for cog in self.cgm.loaded(True):
                self.bot.unload_extension(cog)
                unloadedcogs.append(self.cgm.get_cog(cog))
            message += '```diff\n'
            for ulcog in unloadedcogs:
                message += f'- {ulcog}\n'
            message += '```'
            return await ctx.send(message)
        else:
            if specified_cog in self.cgm.loaded():
                self.bot.unload_extension(self.cgm.get_full_cog(specified_cog))
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' succesfully unloaded.```')
            elif specified_cog in self.cgm.all():
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' isn\'t loaded.```')
            else:
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' not found.```')

    @cogs.command(aliases = ['rel', 're', 'r'], hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, specified_cog = None):
        if specified_cog in ['all', 'a', None]:
            message = '```fix\nCogs succesfully reloaded:```'
            reloadedcogs = []
            for cog in self.cgm.loaded(True):
                self.bot.reload_extension(cog)
                reloadedcogs.append(self.cgm.get_cog(cog))
            message += '```diff\n'
            for rcog in reloadedcogs:
                message += f'+ {rcog}\n'
            message += '```'
            return await ctx.send(message)
        else:
            if specified_cog in self.cgm.loaded():
                self.bot.reload_extension(self.cgm.get_full_cog(specified_cog))
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' succesfully reloaded.```')
            elif specified_cog in self.cgm.all():
                self.bot.load_extension(self.cgm.get_full_cog(specified_cog))
                return await ctx.send(f'```fix\nCan\'t reload something which isn\'t loaded. Loading \'{specified_cog}\'```')
            else:
                return await ctx.send(f'```fix\nCog \'{specified_cog}\' not found.```')

    @cogs.group(aliases = ['li'], hidden=True)
    @commands.is_owner()
    async def list(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.all(ctx)

    @list.command(aliases=['a'], hidden=True)
    @commands.is_owner()
    async def all(self, ctx):
        loadedcogs = self.cgm.loaded()
        unloadedcogs = self.cgm.unloaded()

        coglen = 0 # Len of the logest cog name (we'll use that later)
        for acog in list(loadedcogs) + list(unloadedcogs):
            if len(acog) > coglen:
                coglen = len(acog)

        message = '```fix\nAvailable cogs:```'

        if loadedcogs == [] and unloadedcogs == []:
            message += '```cs\n# No cogs found.'
        else:
            message += '```diff\n'

        for lcog in loadedcogs:
            spaces = ' '*(coglen - len(lcog))
            message += f'+ {spaces}{lcog} | Active\n'

        for ucog in unloadedcogs:
            spaces = ' '*(coglen - len(ucog))
            message += f'- {spaces}{ucog} | Inactive\n'

        message += '```'

        await ctx.send(message)

    @list.command(aliases=['load', 'l'], hidden=True)
    @commands.is_owner()
    async def loaded(self, ctx):
        loadedcogs = self.cgm.loaded()
        coglen = 0
        for lcog in loadedcogs:
            if len(lcog) > coglen:
                coglen = len(lcog)

        message = '```fix\nLoaded cogs:```'

        if loadedcogs == {}:
            message += '```cs\n# No cogs found.'
        else:
            message += '```diff\n'

        for lcog in loadedcogs:
            spaces = ' '*(coglen - len(lcog))
            message += f'+ {spaces}{lcog} | Active\n'

        message += '```'

        await ctx.send(message)

    @list.command(aliases=['unload', 'unl', 'ul', 'un', 'u'], hidden=True)
    @commands.is_owner()
    async def unloaded(self, ctx):
        unloadedcogs = self.cgm.unloaded()

        coglen = 0
        for unlcog in unloadedcogs:
            if len(unlcog) > coglen:
                coglen = len(unlcog)

        message = '```fix\nUnloaded cogs:```'

        if unloadedcogs == []:
            message += '```cs\n# No cogs found.'
        else:
            message += '```diff\n'

        for unlcog in unloadedcogs:
            spaces = ' '*(coglen - len(unlcog))
            message += f'- {spaces}{unlcog} | Inactive\n'

        message += '```'

        await ctx.send(message)

def setup(bot):
    bot.add_cog(Base(bot))