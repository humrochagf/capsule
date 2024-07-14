from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_core import to_jsonable_python

from capsule.database.service import DatabaseService

from ..models import InboxEntry


class InboxRepository:
    name: str = "ap_inbox_entries"
    collection: AsyncIOMotorCollection

    def __init__(self, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(self.name)

    async def create_entry(self, entry: InboxEntry) -> None:
        await self.collection.insert_one(to_jsonable_python(entry))
