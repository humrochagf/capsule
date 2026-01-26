from collections.abc import Iterator
from typing import cast

from pydantic_core import to_jsonable_python
from real_ladybug import QueryResult

from capsule.activitypub.models import InboxEntry, InboxEntryStatus
from capsule.database.repository import BaseDBRepository
from capsule.utils import utc_now


class InboxRepository(BaseDBRepository):
    def create_table(self) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """CREATE NODE TABLE IF NOT EXISTS $table_name (
                    id INT64 PRIMARY KEY,
                    status STRING,
                    activity JSON,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );""",
                parameters=self.build_parameters(),
            )

    def create_entry(self, entry: InboxEntry) -> InboxEntry:
        with self.db.get_connection() as conn:
            result = cast(QueryResult, conn.execute(
                """CREATE (n:$table_name {
                    status: $status,
                    activity: $activity,
                    created_at: $created_at,
                    updated_at: $updated_at
                })
                RETURN n.id as id;""",
                parameters=self.build_parameters({
                    "status": entry.status,
                    "activity": to_jsonable_python(entry.activity),
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at,
                }),
            )).rows_as_dict()
            entry.id = cast(dict, result.get_next())["id"]

        return entry

    def list_entries(
        self, status: InboxEntryStatus
    ) -> Iterator[InboxEntry]:
        with self.db.get_connection() as conn:
            result = cast(QueryResult, conn.execute(
                """MATCH (n:$table_name)
                WHERE n.status = $status
                RETURN n as data;""",
                parameters=self.build_parameters({
                    "status": status,
                }),
            )).rows_as_dict()

            for entry in cast(Iterator[dict], result):
                yield InboxEntry(**entry["data"])

    def update_entries_state(self, ids: list, status: InboxEntryStatus) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """MATCH (n:$table_name)
                WHERE n.id IN $ids
                SET n.status = $status
                SET n.updated_at = $updated_at;""",
                parameters=self.build_parameters({
                    "ids": ids,
                    "status": status,
                    "updated_at": utc_now(),
                }),
            )
