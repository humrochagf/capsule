from abc import ABC, abstractmethod

from .service import DatabaseService


class BaseDBRepository(ABC):
    table_name: str
    db: DatabaseService

    def __init__(self, table_name: str, database_service: DatabaseService) -> None:
        self.table_name = table_name
        self.db = database_service

    @abstractmethod
    def create_table(self) -> None:
        ...

    def build_parameters(self, parameters: dict | None = None) -> dict:
        if parameters is None:
            parameters = {}

        parameters["table_name"] = self.table_name

        return parameters

    def delete_all(self) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "MATCH (n:$table_name) DELETE n",
                parameters=self.build_parameters(),
            )
