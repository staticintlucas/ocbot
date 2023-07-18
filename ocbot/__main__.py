import os
from pathlib import Path

import yaml

from .client import Client


def main(config_path: str | Path) -> None:
    # Load environment variables
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable not set!")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Run bot
    client = Client(config)
    client.run(token)
