from typing import cast

from pydantic import HttpUrl
from pydantic_core import to_jsonable_python
from real_ladybug import QueryResult
from wheke_ladybug import LadybugRepository

from capsule.activitypub.models import Follow


class FollowRepository(LadybugRepository):
    async def create_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                CREATE NODE TABLE IF NOT EXISTS Follow
                (
                    id STRING PRIMARY KEY,
                    actor STRING,
                    status STRING
                );
                """
            )

    async def drop_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute("DROP TABLE IF EXISTS Follow;")

    async def get_follow(self, follow_id: HttpUrl) -> Follow | None:
        with self.db.async_connection as conn:
            response = cast(
                QueryResult,
                await conn.execute(
                    """
                    MATCH (f:Follow)
                    WHERE f.id = $follow_id
                    RETURN
                    f.id as id,
                    f.actor as actor,
                    f.status as status;
                    """,
                    parameters={"follow_id": str(follow_id)},
                ),
            )

            data = cast(list[dict], response.rows_as_dict().get_all())
            return Follow.model_validate(data[0]) if len(data) > 0 else None

    async def upsert_follow(self, follow: Follow) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MERGE (f:Follow {id: $id})
                ON CREATE SET
                f.actor = $actor,
                f.status = $status
                ON MATCH SET
                f.actor = $actor,
                f.status = $status;
                """,
                parameters=to_jsonable_python(follow),
            )

    async def delete_follow(self, follow_id: HttpUrl) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MATCH (f:Follow)
                WHERE f.id = $follow_id
                DELETE f;
                """,
                parameters={"follow_id": str(follow_id)},
            )

    async def delete_follow_by_actor(self, actor_id: HttpUrl) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MATCH (f:Follow)
                WHERE f.actor = $actor_id
                DELETE f;
                """,
                parameters={"actor_id": str(actor_id)},
            )
