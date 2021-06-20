import asyncio
import discord
from discord import guild
from discord.ext import commands, tasks
from os import listdir, makedirs, getenv, walk, sep, path as ospath
from sys import path as syspath
from pathlib import Path
import aiosqlite as asql
import sqlite3 as sql
from typing import Union
import logging
import sys

# Fix relative imports
# https://stackoverflow.com/a/65780624/12769729
if __package__ is None:
    DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(DIR.parent))
    __package__ = DIR.name

from .settings import *
from .core.prefix import PrefixManager
from .core.config import ConfigManager
from .help import RedditorHelp

class Redditor(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, help_command=RedditorHelp())
        # Setup all the basic stuff
        self.setup()

        # Create attribute for PrefixManager
        self.pm = None
        # Create ConfigManager
        self.cm = ConfigManager(path=self.CONFIG_PATH)

        # Not really necessary, might delete later
        self.version = '0.2'
        # Colour for embeds 'n stuff
        self.main_colour = 0xED001C

        self.guild_count = 0
        self.member_count = 0

        self.loop.create_task(self.setup_func())

    # Call all the necessary setup functions
    def setup(self):
        self.setup_settings()
        self.setup_folders()
        self.setup_db()
        self.loop.create_task(self.setup_adb())

    def setup_settings(self):
        self.FILE_PATH = FILE_PATH
        self.CONFIG_PATH = CONFIG_PATH
        self.DB_NAME = DB_NAME
        self.DB_FOLDER = DB_FOLDER
        self.DB_PATH = DB_PATH
        self.COGS_NAME = COGS_NAME
        self.COGS_FOLDER = COGS_FOLDER
        self.LOGS_FOLDER = LOGS_FOLDER

    def setup_db(self):
        self.DB = sql.connect(self.DB_PATH)

    async def setup_adb(self):
        self.aDB = await asql.connect(self.DB_PATH)

    def setup_folders(self):
        if not ospath.exists(self.DB_FOLDER):
            makedirs(self.DB_FOLDER)

        if not ospath.exists(self.LOGS_FOLDER):
            makedirs(self.LOGS_FOLDER)

    async def close(self):
        # Close DB connections first
        self.DB.close()
        await self.aDB.close()
        await super().close()

    async def load_cogs(self):
        # Load Base
        base_str = f"{self.COGS_NAME}.Base"
        self.load_extension(base_str)

        # Loads cogs
        for subdir, dirs, files in walk(self.COGS_FOLDER):
            for filename in files:
                cog_path = subdir + sep + filename
                if cog_path.endswith(".py"):
                    cog_name = filename[:-3].split('\\')[-1]
                    load_str = f"{self.COGS_NAME}.{cog_name}"
                    if (load_str != base_str):
                        self.load_extension(load_str)

    async def get_prefix(self, message: discord.Message):
        if message.guild != None:
            if (self.pm is None):
                prefix = self.cm.prefix
            else:
                prefix = await self.pm.a_get(message.guild.id)
        else:
            if (self.pm is None):
                prefix = self.cm.prefix
            else:
                prefix = self.pm.default
        return [prefix, f'<@!{self.user.id}>', f'@{self.user.id}']

    # Loads what is needed, updates guild/prefix DB, etc.
    async def setup_func(self):
        await self.wait_until_ready()

        self.pm = PrefixManager(DB=self.DB, aDB=self.aDB, default=self.cm.prefix)

        # Gets every guild in our DB
        cursor = await self.aDB.cursor()
        await cursor.execute('SELECT * FROM prefixes')
        guildIDs = []
        async for row in cursor:
            guildIDs.append(row[0])
        await cursor.close()

        # Checks if it has guild in DB, if it isn't it will insert it into DB
        for guild in self.guilds:
            self.guild_count += 1
            self.member_count += guild.member_count
            if guild.id not in guildIDs:
                await self.pm.a_add(guild.id)

        # Checks for guilds that the bot is no longer in
        for guildID in guildIDs:
            if self.get_guild(guildID) not in self.guilds:
                await self.pm.a_remove(guildID)

        # Load cogs
        await self.load_cogs()

    async def on_ready(self):
        print(f"Logged in as {self.user.name}#{self.user.discriminator}\nReady signal recieved!")

    # Hooks into PrefixManager
    async def on_guild_join(self, guild):
        # Add prefix
        await self.pm.a_add(guild.id)
        self.guild_count += 1
        self.member_count += guild.member_count

    async def on_guild_remove(self, guild):
        # Remove prefix
        await self.pm.a_remove(guild.id)
        self.guild_count -= 1
        self.member_count -= guild.member_count

if __name__ == "__main__":
    bot = Redditor()
    bot.run(bot.cm.token)