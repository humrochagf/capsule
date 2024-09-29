from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_core import to_jsonable_python

from capsule.database.service import DatabaseService

from ..models import InboxEntry, InboxEntryStatus


class InboxRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("created_at")

    async def create_entry(self, entry: InboxEntry) -> None:
        await self.collection.insert_one(to_jsonable_python(entry))

    async def list_entries(
        self, status: InboxEntryStatus
    ) -> AsyncGenerator[InboxEntry]:
        cursor = self.collection.find({"status": {"$eq": status}})

        async for entry in cursor:
            yield InboxEntry(**entry)

    async def update_entries_state(
        self, ids: list[str], status: InboxEntryStatus
    ) -> None:
        await self.collection.update_many(
            {"_id": {"$in": ids}},
            {"$set": {"status": status}},
        )
