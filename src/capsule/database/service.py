from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from wheke import get_service

from capsule.settings import get_capsule_settings


class DatabaseService:
    client: AsyncIOMotorClient
    database: AsyncIOMotorDatabase

    def __init__(self) -> None:
        settings = get_capsule_settings()

        self.client = AsyncIOMotorClient(f"{settings.connection_string}")
        self.database = self.client[settings.database_name]

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        return self.database[name]

    async def drop_db(self) -> None:
        settings = get_capsule_settings()
        await self.client.drop_database(settings.database_name)


def database_service_factory() -> DatabaseService:
    return DatabaseService()


def get_database_service() -> DatabaseService:
    return get_service(DatabaseService)
