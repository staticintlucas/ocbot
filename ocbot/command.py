from pathlib import Path
from typing import Optional, NamedTuple, TYPE_CHECKING

import discord
from discord import app_commands

if TYPE_CHECKING:
    from .client import Client

_root = Path().parent.resolve()
_img = _root / "img"

class CommandConfig(NamedTuple):
    command: str
    description: str
    text: Optional[str]
    file: Optional[str | Path]

class Command(app_commands.Command):
    def __init__(self, config: CommandConfig):

        async def callback(interaction: discord.Interaction):
            client: Client = interaction.client

            text = "\n\n".join(config.text.splitlines()) if config.text is not None else ""
            file = discord.File(Path() / "files" / config.file) if config.file is not None else discord.utils.MISSING

            await interaction.response.send_message(text, file=file)

        super().__init__(
            name=config.command,
            description=config.description,
            callback=callback
        )
