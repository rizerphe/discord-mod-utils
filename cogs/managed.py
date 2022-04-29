from manager import ModerationManager
from discord.ext import commands


class ManagedCog(commands.Cog):
    """My parent Cog

    Diferent sets of tools are stored in different classes
    This class stores the properties shared between them

    """

    def __init__(self, manager: ModerationManager):
        """Initialize the cog"""
        self.manager = manager
