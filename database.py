from dataclasses import dataclass, asdict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from typing import Optional


@dataclass
class Guild:
    moderator_role: Optional[int] = None
    cases_channel: Optional[int] = None

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
            )
        return cls()

    def to_dict(self):
        return {
            "moderator_role": str(self.moderator_role) if self.moderator_role else None,
            "cases_channel": str(self.cases_channel) if self.cases_channel else None,
        }


class Database:
    def __init__(self, credentials_file="credentials.json"):
        self.cred = credentials.Certificate(credentials_file)
        firebase_admin.initialize_app(self.cred)

        self.db = firestore.client()

    def get_guild(self, guild_id) -> Guild:
        doc_ref = self.db.collection("guilds").document(str(guild_id))
        doc = doc_ref.get()
        return Guild.from_dict(doc.to_dict())

    def set_guild(self, guild_id, guild: Guild):
        doc_ref = self.db.collection("guilds").document(str(guild_id))
        doc_ref.set(guild.to_dict())