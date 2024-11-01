from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_core import to_jsonable_python

from capsule.database.service import DatabaseService

from ..models import Authorization


class AuthorizationRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("client_id", unique=True)
        await self.collection.create_index("code", unique=True)

    async def upsert_authorization(self, authorization: Authorization) -> None:
        await self.collection.replace_one(
            {"client_id": {"$eq": str(authorization.client_id)}},
            to_jsonable_python(authorization),
            upsert=True,
        )

    async def get_authorization(self, code: str) -> Authorization | None:
        data = await self.collection.find_one({"code": {"$eq": code}})
        return Authorization(**data) if data else None
