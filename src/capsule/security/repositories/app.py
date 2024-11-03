from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_core import to_jsonable_python

from capsule.database.service import DatabaseService

from ..models import App


class AppRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("client_id", unique=True)

    async def create_app(self, app: App) -> None:
        await self.collection.insert_one(to_jsonable_python(app))

    async def get_app(self, client_id: str) -> App | None:
        data = await self.collection.find_one({"client_id": {"$eq": client_id}})
        return App(**data) if data else None
