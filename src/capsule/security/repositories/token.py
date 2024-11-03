from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_core import to_jsonable_python

from capsule.database.service import DatabaseService

from ..models import Token


class TokenRepository:
    collection: AsyncIOMotorCollection

    def __init__(self, collection_name: str, database_service: DatabaseService) -> None:
        self.collection = database_service.get_collection(collection_name)

    async def create_indexes(self) -> None:
        await self.collection.create_index("client_id", unique=True)
        await self.collection.create_index("token")

    async def create_token(self, token: Token) -> None:
        await self.collection.insert_one(to_jsonable_python(token))

    async def get_token(self, access_token: str) -> Token | None:
        data = await self.collection.find_one({"token": {"$eq": access_token}})
        return Token(**data) if data else None
