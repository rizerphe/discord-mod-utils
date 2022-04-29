from typing import Callable
from typing import Coroutine

import discord

from config import Config


async def is_mod(
    user: discord.Member, config: Config, respond: Callable[[str], Coroutine]
) -> bool:
    """Check if the user us a moderator and send an error message if not

    Args:
        user: the member to check the roles of
        config: the configuration that contains the guild database
        respond: the function to respond with

    Returns:
        True if the user is a moderator; False otherwise

    """
    role = config.get_mod_role(user.guild.id)
    if role is None:
        await respond(
            "You didn't set up a moderator. " + "Use `/config moderator` to choose one"
        )
        return False
    if role in [role.id for role in user.roles]:
        return True
    await respond("This command is reserved for moderators")
    return False
