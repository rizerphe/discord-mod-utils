from dataclasses import dataclass
from typing import Optional

from database import Database


@dataclass
class Config:
    """A dataclass for storing the app config"""

    database: Database
    token: str

    def get_mod_cases(self, guild_id: int) -> Optional[int]:
        """Get the ID of the channel used for storing mod cases"""
        return self.database.get_guild(guild_id).cases_channel

    def get_mod_role(self, guild_id: int) -> Optional[int]:
        """Get the ID of the moderator role"""
        return self.database.get_guild(guild_id).moderator_role

    def get_mod_hook(self, guild_id: int) -> Optional[int]:
        """Get the ID of the moderation webhook"""
        return self.database.get_guild(guild_id).duplication_webhook

    def set_mod_hook(self, guild_id: int, mod_hook_id: Optional[int]) -> None:
        """Set the ID of the moderation webhook"""
        guild = self.database.get_guild(guild_id)
        guild.duplication_webhook = mod_hook_id
        self.database.set_guild(guild_id, guild)
