from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Guild:
    """Stores the configuration of a specified guild"""

    moderator_role: Optional[int] = None
    cases_channel: Optional[int] = None
    duplication_webhook: Optional[int] = None

    @classmethod
    def from_dict(cls, dictionary: Optional[dict]):
        """Create a config object from a dictionary representation"""
        if dictionary:
            return cls(
                moderator_role=int(dictionary["moderator_role"])
                if dictionary.get("moderator_role")
                else None,
                cases_channel=int(dictionary["cases_channel"])
                if dictionary.get("cases_channel")
                else None,
                duplication_webhook=int(dictionary["duplication_webhook"])
                if dictionary.get("duplication_webhook")
                else None,
            )
        return cls()

    def to_dict(self) -> dict[str, Optional[str]]:
        """Generate a dictionary representation of the configuration"""
        return {
            "moderator_role": str(self.moderator_role) if self.moderator_role else None,
            "cases_channel": str(self.cases_channel) if self.cases_channel else None,
            "duplication_webhook": str(self.duplication_webhook)
            if self.duplication_webhook
            else None,
        }


class Database(ABC):
    """An abstract representation of the database"""

    @abstractmethod
    def get_guild(self, guild_id: int) -> Guild:
        """Retrieve the configuration for a given guild"""
        pass

    @abstractmethod
    def set_guild(self, guild_id: int, guild: Guild) -> None:
        """Save the configuration of a guild"""
        pass
