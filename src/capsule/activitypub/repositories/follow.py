from typing import cast

from pydantic import HttpUrl
from pydantic_core import to_jsonable_python
from real_ladybug import QueryResult

from capsule.activitypub.models import Follow
from capsule.database.repository import BaseDBRepository


class FollowRepository(BaseDBRepository):
    def create_table(self) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """CREATE NODE TABLE IF NOT EXISTS $table_name (
                    id STRING PRIMARY KEY,
                    actor STRING,
                    status STRING,
                );""",
                parameters=self.build_parameters(),
            )

    async def get_follow(self, follow_id: HttpUrl) -> Follow | None:
        with self.db.get_connection() as conn:
            result = cast(QueryResult, conn.execute(
                """MATCH (n:$table_name)
                WHERE n.id = $id
                RETURN n.id as id, n.actor as actor, n.status as status;""",
                parameters=self.build_parameters({
                    "id": follow_id,
                }),
            )).rows_as_dict()

            if not result.has_next():
                return None

            data = result.get_next()

        return Follow(**data) if isinstance(data, dict) else None

    def upsert_follow(self, follow: Follow) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """MERGE (n:$table_name {id: $id})
                ON MATCH
                    SET n.actor = $actor
                    SET n.status = $status
                ON CREATE
                    SET n.actor = $actor
                    SET n.status = $status
                RETURN
                ;""",
                parameters=self.build_parameters(to_jsonable_python(follow)),
            )

    async def delete_follow(self, follow_id: HttpUrl) -> None:
        await self.collection.delete_one({"id": {"$eq": str(follow_id)}})

    async def delete_follow_by_actor(self, actor_id: HttpUrl) -> None:
        await self.collection.delete_one({"actor": {"$eq": str(actor_id)}})
