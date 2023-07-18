from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

import discord
from discord import app_commands

if TYPE_CHECKING:
    from .client import Client

_root = Path().parent.resolve()
_files = _root / "files"


class CommandConfig(NamedTuple):
    command: str
    description: str
    text: Optional[str]
    file: Optional[str | Path]


class Command(app_commands.Command[app_commands.Group, Any, Any]):
    def __init__(self, config: CommandConfig):
        text = "\n\n".join(config.text.splitlines()) if config.text is not None else ""
        file = (
            discord.File(_files / config.file) if config.file is not None else discord.utils.MISSING
        )

        async def callback(
            interaction: discord.Interaction[Client], *_args: Any, **_kwargs: Any
        ) -> None:
            assert interaction.command is not None  # Should never happen

            interaction.client.log.info(f"Slash command {interaction.command.name!r}")

            await interaction.response.send_message(text, file=file)

            interaction.client.log.info(f"Responded to slash command {interaction.command.name!r}")

        super().__init__(
            name=config.command, description=config.description, callback=callback  # type: ignore
        )
