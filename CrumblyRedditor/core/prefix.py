from typing import Union
import discord

class PrefixManager():
    def __init__(self, DB, aDB, default: str) -> None:
        self.DB = DB
        self.DB.execute('CREATE TABLE IF NOT EXISTS prefixes (id INTEGER PRIMARY KEY, prefix TEXT)')
        self.DB.commit()
        self.aDB = aDB
        self.default = default

    def get(self, guild: Union[discord.Guild, int]) -> str:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        cursor = self.DB.cursor()
        cursor.execute('SELECT prefix FROM prefixes WHERE id=?', (guild, ))
        result = cursor.fetchone()
        cursor.close()
        if (result is None):
            return self.default
        return result[0]

    async def a_get(self, guild: Union[discord.Guild, int]) -> str:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        cursor = await self.aDB.cursor()
        await cursor.execute('SELECT prefix FROM prefixes WHERE id=?', (guild, ))
        result = await cursor.fetchone()
        await cursor.close()
        if (result is None):
            return self.default
        return result[0]

    def set(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        self.DB.execute('UPDATE prefixes SET prefix=? WHERE id=?', (prefix, guild))
        self.DB.commit()

    async def a_set(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        await self.aDB.execute('UPDATE prefixes SET prefix=? WHERE id=?', (prefix, guild))
        await self.aDB.commit()

    def add(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        self.DB.execute('INSERT INTO prefixes (id, prefix) VALUES(?,?)', (guild, prefix))
        self.DB.commit()

    async def a_add(self, guild: Union[discord.Guild, int], prefix: str = None) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        if (prefix is None):
            prefix = self.default
        await self.aDB.execute('INSERT INTO prefixes (id, prefix) VALUES(?,?)', (guild, prefix))
        await self.aDB.commit()

    def remove(self, guild: Union[discord.Guild, int]) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        self.DB.execute('DELETE FROM prefixes WHERE id=?', (guild, ))
        self.DB.commit()

    async def a_remove(self, guild: Union[discord.Guild, int]) -> None:
        if (isinstance(guild, discord.Guild)):
            guild = guild.id
        await self.aDB.execute('DELETE FROM prefixes WHERE id=?', (guild, ))
        await self.aDB.commit()