import discord
from discord.ext import commands

class RedditorHelp(commands.HelpCommand):
    def __init__(self):
        self.main_colour = 0xFF4500
        super().__init__()

    def get_command_signature(self, command):
        return f"{self.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", description=f"General help", colour=self.main_colour)
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = []
            for c in filtered:
                if c.brief is None:
                    brief = ""
                else:
                    brief = " - " + c.brief
                cmd = self.get_command_signature(c) + brief
                command_signatures.append(cmd)
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        commands = ""
        for command in cog.commands:
            if command.brief != "":
                commands += f"{self.get_command_signature(command)} - {command.brief}\n"
            else:
                commands += f"{self.get_command_signature(command)}\n"
        embed = discord.Embed(title=f"Cog {cog.qualified_name}", description=f"{cog.description}\n{commands}", colour=self.main_colour)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        commands = ""
        for command in group.commands:
            if command.short_doc != "":
                commands += f"{self.get_command_signature(command)} - {command.short_doc}\n"
            else:
                commands += f"{self.get_command_signature(command)}\n"
        embed = discord.Embed(title=f"Command group {self.clean_prefix}{group.qualified_name}", description=f"{group.description}\n{commands}", colour=self.main_colour)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f"Command {self.clean_prefix}{command.qualified_name}", description=f"{command.description}\n{self.get_command_signature(command)}", colour=self.main_colour)
        channel = self.get_destination()
        await channel.send(embed=embed)