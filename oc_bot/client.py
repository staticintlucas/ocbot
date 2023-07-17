import logging
from typing import Any, NamedTuple

import discord
from discord import app_commands

from .command import Command, CommandConfig

class RolesConfig(NamedTuple):
    message_id: int
    from_emoji: dict[int, int]

class Client(discord.Client):

    def _load_config(self, config: dict[str, Any]):
        try:
            # Server id
            self.server_id = int(config["server"])

            # Roles configuration
            self.roles = RolesConfig(
                message_id=config["roles"]["message"],
                from_emoji={
                    item["emoji"]: item["role"] for item in config["roles"]["list"]
                },
            )

            # Slash command configuration
            self.commands = [
                CommandConfig(
                    command=item["command"],
                    description=item["description"],
                    text=item.get("text"),
                    file=item.get("file"),
                )
                for item in config["commands"]
            ]

        except KeyError as e:
            raise ValueError(f"{e.args[0]!r} not set in config") from None


    def __init__(self, config: dict[str, Any], /, **kwargs):

        # Don't warn about missing PyNaCL dependency, we don't use voice anyway
        discord.VoiceClient.warn_nacl = False

        # Set up logging using discord.py's logger even in our own code
        discord.utils.setup_logging(root=False)
        root_log = logging.getLogger("discord")

        self.log = logging.getLogger(__name__)
        self.log.setLevel(root_log.level)
        for handler in root_log.handlers:
            self.log.addHandler(handler)

        # Config
        self._load_config(config)

        # Call discord client's __init__
        default_intents = discord.Intents.default()
        default_intents.members = True
        default_intents.message_content = True
        intents = kwargs.pop("intents", default_intents)

        super().__init__(intents=intents, **kwargs)


    async def on_ready(self) -> None:
        self.log.info(f"Connected as {self.user.name!r} (id={self.user.id})")

        # Check we're in the correct guild
        guild = self.get_guild(self.server_id)
        if guild is None:
            self.log.error(f"Not connected to guild with requested id!")
            return

        # Add slash commands
        self.tree = app_commands.CommandTree(self)
        for cmd in self.commands:
            self.tree.add_command(Command(cmd), guild=guild)
        await self.tree.sync(guild=guild)

        self.log.info(f"Connected to guild {guild.name!r} (id={guild.id})")


    async def _add_remove_role(self, payload: discord.RawReactionActionEvent, add: bool) -> None:

        # Unknown guild
        if payload.guild_id != self.server_id:
            guild = self.get_guild(payload.guild_id)
            self.log.info(f"Ignoring reaction in guild {guild.name!r} (id={guild.id})")
            return

        # Wrong message
        if payload.message_id != self.roles.message_id:
            self.log.info(f"Ignoring reaction on message id={payload.message_id}")
            return

        # Log emoji
        emoji = payload.emoji
        add_str = "add" if add else "remove"
        self.log.info(f"Reaction {add_str} {emoji.name!r} to message id={payload.message_id}")

        # Get role
        try:
            role_id = self.roles.from_emoji[emoji.id]
        except KeyError:
            self.log.info(f"Ignoring reaction {emoji.name!r} (id={emoji.id}), no matching role")
            return

        guild = self.get_guild(payload.guild_id)
        role = discord.utils.get(guild.roles, id=role_id)
        if role is None:
            self.log.error(f"No role found with id={role_id}")
            return

        # Just in case someone finds a way to add roles they shouldn't
        if add and role.permissions.value != 0:
            self.log.error(
                f"Can't give role {role.name!r} (id={role.id}) with non-zero permissions value")
            return

        # Add/remove member's roles
        member = guild.get_member(payload.user_id)
        if add:
            await member.add_roles(role)
            self.log.info(f"Gave {role.name!r} (id={role.id}) to {member.name!r} (id={member.id})")
        else:
            await member.remove_roles(role)
            self.log.info(
                f"Removed {role.name!r} (id={role.id}) from {member.name!r} (id={member.id})")


    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self._add_remove_role(payload, add=True)


    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self._add_remove_role(payload, add=False)


    def run(self, token: str) -> None:
        super().run(
            token=token,
            log_handler=self.log.handlers[0],
            log_formatter=self.log.handlers[0].formatter,
            log_level=self.log.level,
            root_logger=True,
        )
