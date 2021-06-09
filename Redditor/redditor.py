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
from .core.db import DB
from .core.prefix import PrefixManager
from .core.config import ConfigManager
from .help import RedditorHelp

class Redditor(commands.Bot):
    def __init__(self):
        self.setup_settings()
        self.setup_folders()
        self.setup_db()
        self.pm = None
        super().__init__(command_prefix=self.get_prefix, help_command=RedditorHelp())
        self.loop.create_task(self.setup_adb())
        self.config = ConfigManager(path=self.CONFIG_PATH)

        self.version = '0.1'
        self.main_colour = 0x00A8B5

        self.guild_count = 0
        self.member_count = 0

        self.load_cogs()
        self.loop.create_task(self.setup_func())

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
        conn = sql.connect(self.DB_PATH)
        cursor = conn.cursor()
        self.DB = DB(conn, cursor)

    async def setup_adb(self):
        conn = await asql.connect(self.DB_PATH)
        cursor = await conn.cursor()
        self.aDB = DB(conn, cursor)

    def setup_folders(self):
        if not ospath.exists(self.DB_FOLDER):
            makedirs(self.DB_FOLDER)

        if not ospath.exists(self.LOGS_FOLDER):
            makedirs(self.LOGS_FOLDER)

    async def close(self):
        self.DB.connection.close()
        await self.aDB.connection.close()
        await super().close()

    def load_cogs(self):
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
                prefix = self.config.prefix
            else:
                prefix = await self.pm.a_get(message.guild.id)
        else:
            if (self.pm is None):
                prefix = self.config.prefix
            else:
                prefix = self.pm.default
        return [prefix, f'<@!{self.user.id}>', f'@{self.user.id}']

    # Loads what is needed, updates guild/prefix DB, etc.
    async def setup_func(self):
        await self.wait_until_ready()

        self.pm = PrefixManager(DB=self.DB, aDB=self.aDB, default=self.config.prefix)

        # Gets every guild in our DB
        await self.aDB.cursor.execute('SELECT * FROM prefixes')
        guildIDs = []
        async for row in self.aDB.cursor:
            guildIDs.append(row[0])

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

        await self.aDB.connection.commit()

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
    bot.run(bot.config.token)