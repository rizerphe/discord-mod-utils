import os

import click
import discord
from dotenv import load_dotenv

from cog import ModerationCog
from config import Config
from firebase_db import FirestoreDatabase
from manager import ModerationManager


class PromptWhenNoDefault(click.Option):
    """Propmts when no default is set

    A class responsible for only prompting for input when tjere is no
    default value set (for use with @click.option)

    """

    def prompt_for_value(self, ctx):
        if (default := self.get_default(ctx)) is None:
            return super().prompt_for_value(ctx)
        return default


load_dotenv()


@click.command()
@click.option(
    "--token",
    prompt=True,
    cls=PromptWhenNoDefault,
    default=lambda: os.getenv("TOKEN", None),
    show_default="envvar 'TOKEN'",
    type=str,
)
@click.option(
    "--firebase-creds",
    default="credentials.json",
    type=click.Path(exists=True),
)
def main(token, firebase_creds):
    """Main function

    Connects to a firestore database and starts the bot

    """
    database = FirestoreDatabase(firebase_creds)
    config = Config(token=token, database=database)
    bot = discord.Bot()
    bot.add_cog(ModerationCog(ModerationManager(bot, config)))
    bot.run(token)


if __name__ == "__main__":
    main()
