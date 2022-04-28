from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class Guild:
    moderator_role: Optional[int] = None
    cases_channel: Optional[int] = None
    duplication_webhook: Optional[int] = None

    @classmethod
    def from_dict(cls, dictionary: Optional[dict]):
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

    def to_dict(self):
        return {
            "moderator_role": str(self.moderator_role) if self.moderator_role else None,
            "cases_channel": str(self.cases_channel) if self.cases_channel else None,
            "duplication_webhook": str(self.duplication_webhook)
            if self.duplication_webhook
            else None,
        }


class Database(ABC):
    @abstractmethod
    def get_guild(self, guild_id: int) -> Guild:
        pass

    @abstractmethod
    def set_guild(self, guild_id: int, guild: Guild) -> None:
        pass
