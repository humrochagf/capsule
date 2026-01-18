from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from svcs import Container
from wheke import get_service

from capsule.settings import CapsuleSettings, get_capsule_settings


class DatabaseService:
    settings: CapsuleSettings

    client: AsyncIOMotorClient
    database: AsyncIOMotorDatabase

    def __init__(self, *, settings: CapsuleSettings) -> None:
        self.settings = settings

        self.client = AsyncIOMotorClient(f"{settings.connection_string}")
        self.database = self.client[settings.database_name]

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        return self.database[name]

    async def drop_db(self) -> None:
        await self.client.drop_database(self.settings.database_name)


def database_service_factory(container: Container) -> DatabaseService:
    return DatabaseService(settings=get_capsule_settings(container))


def get_database_service(container: Container) -> DatabaseService:
    return get_service(container, DatabaseService)
