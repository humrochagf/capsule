from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import HttpUrl
from pydantic_core import to_jsonable_python

from capsule.activitypub.models import Follow
from capsule.database.service import DatabaseService


class FollowRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("id", unique=True)

    async def get_follow(self, follow_id: HttpUrl) -> Follow | None:
        data = await self.collection.find_one({"id": {"$eq": str(follow_id)}})
        return Follow(**data) if data else None

    async def upsert_follow(self, follow: Follow) -> None:
        await self.collection.replace_one(
            {"id": {"$eq": str(follow.id)}},
            to_jsonable_python(follow),
            upsert=True,
        )

    async def delete_follow(self, follow_id: HttpUrl) -> None:
        await self.collection.delete_one({"id": {"$eq": str(follow_id)}})
