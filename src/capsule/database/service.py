from collections.abc import Generator
from contextlib import contextmanager

from real_ladybug import Connection, Database
from svcs import Container
from wheke import get_service

from capsule.settings import CapsuleSettings, get_capsule_settings


class DatabaseService:
    settings: CapsuleSettings

    db: Database

    def __init__(self, *, settings: CapsuleSettings) -> None:
        self.settings = settings

        self.db = Database(settings.connection_string)

    def init_db(self) -> None:
        with self.get_connection() as connection:
            connection.execute(
                "INSTALL json;"
                "LOAD json;"
            )

    @contextmanager
    def get_connection(self) -> Generator[Connection]:
        with Connection(self.db) as connection:
            yield connection


def database_service_factory(container: Container) -> DatabaseService:
    service = DatabaseService(settings=get_capsule_settings(container))
    service.init_db()
    return service


def get_database_service(container: Container) -> DatabaseService:
    return get_service(container, DatabaseService)
