import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from database import Database
from database import Guild


class FirestoreDatabase(Database):
    """Google Firestore implementation of the database"""

    def __init__(self, credentials_file="credentials.json"):
        """Initialize the firestore database"""
        self.cred = credentials.Certificate(credentials_file)
        firebase_admin.initialize_app(self.cred)

        self.db = firestore.client()

    def get_guild(self, guild_id: int) -> Guild:
        """Retrieve the configuration for a given guild"""
        doc_ref = self.db.collection("guilds").document(str(guild_id))
        doc = doc_ref.get()
        return Guild.from_dict(doc.to_dict())

    def set_guild(self, guild_id, guild: Guild) -> None:
        """Save the configuration of a guild"""
        doc_ref = self.db.collection("guilds").document(str(guild_id))
        doc_ref.set(guild.to_dict())
