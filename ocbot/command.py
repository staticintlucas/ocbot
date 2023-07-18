from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

import discord
from discord import app_commands

if TYPE_CHECKING:
    from .client import Client

_root = Path().parent.resolve()
_files = _root / "files"


class CommandConfig(NamedTuple):
    command: str
    description: str
    text: str | None
    file: str | Path | None


class Command(app_commands.Command[app_commands.Group, Any, Any]):
    def __init__(self, config: CommandConfig):
        text = "\n\n".join(config.text.splitlines()) if config.text is not None else ""
        file = (
            discord.File(_files / config.file) if config.file is not None else discord.utils.MISSING
        )

        async def callback(interaction: discord.Interaction[Client]) -> None:
            assert interaction.command is not None  # Should never happen

            interaction.client.log.info(f"Slash command {interaction.command.name!r}")

            await interaction.response.send_message(text, file=file)

            interaction.client.log.info(f"Responded to slash command {interaction.command.name!r}")

        super().__init__(
            name=config.command, description=config.description, callback=callback  # type: ignore
        )
