from typing import Union
import discord

class PrefixManager():
    def __init__(self, DB, aDB, default: str) -> None:
        self.DB = DB
        self.DB.cursor.execute('CREATE TABLE IF NOT EXISTS prefixes (id INTEGER PRIMARY KEY, prefix TEXT)')
        self.DB.connection.commit()
        self.aDB = aDB
        self.default = default

    def get(self, guild: Union[discord.Guild, int]) -> str:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        self.DB.cursor.execute('SELECT prefix FROM prefixes WHERE id=?', (guild, ))
        result = self.DB.cursor.fetchone()
        if (result is None):
            return self.default
        return result[0]

    async def a_get(self, guild: Union[discord.Guild, int]) -> str:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        await self.aDB.cursor.execute('SELECT prefix FROM prefixes WHERE id=?', (guild, ))
        result = await self.aDB.cursor.fetchone()
        if (result is None):
            return self.default
        return result[0]

    def set(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        self.DB.cursor.execute('UPDATE prefixes SET prefix=? WHERE id=?', (prefix, guild))
        self.DB.connection.commit()

    async def a_set(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        await self.aDB.cursor.execute('UPDATE prefixes SET prefix=? WHERE id=?', (prefix, guild))
        await self.aDB.connection.commit()

    def add(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        self.DB.cursor.execute('INSERT INTO prefixes (id, prefix) VALUES(?,?)', (guild, prefix))
        self.DB.connection.commit()

    async def a_add(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        await self.aDB.cursor.execute('INSERT INTO prefixes (id, prefix) VALUES(?,?)', (guild, prefix))
        await self.aDB.connection.commit()

    def remove(self, guild: Union[discord.Guild, int]) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        self.DB.cursor.execute('DELETE FROM prefixes WHERE id=?', (guild, ))
        self.DB.connection.commit()

    async def a_remove(self, guild: Union[discord.Guild, int]) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        await self.aDB.cursor.execute('DELETE FROM prefixes WHERE id=?', (guild, ))
        await self.aDB.connection.commit()