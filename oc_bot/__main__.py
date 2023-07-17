import os

import yaml

from .client import Client


def main(config):
    # Load environment variables
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        raise ValueError(f"DISCORD_TOKEN environment variable not set!")

    with open(config, "r") as f:
        config = yaml.safe_load(f)

    # Run bot
    client = Client(config)
    client.run(token)


if __name__ == "__main__":
    main()
