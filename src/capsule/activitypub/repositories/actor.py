from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import HttpUrl
from pydantic_core import to_jsonable_python

from capsule.activitypub.models import Actor
from capsule.database.service import DatabaseService


class ActorRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("id", unique=True)

    def get_main_actor(self) -> Actor:
        return Actor.make_main_actor()

    async def upsert_actor(self, actor: Actor) -> None:
        await self.collection.replace_one(
            {"id": {"$eq": str(actor.id)}},
            to_jsonable_python(actor),
            upsert=True,
        )

    async def get_actor(self, actor_id: HttpUrl) -> Actor | None:
        data = await self.collection.find_one({"id": {"$eq": str(actor_id)}})
        return Actor(**data) if data else None
