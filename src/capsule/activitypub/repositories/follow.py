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
                CREATE REL TABLE IF NOT EXISTS Follows
                (
                    FROM Actor to Actor,
                    id STRING,
                    status STRING
                );
                """
            )

    async def drop_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute("DROP TABLE IF EXISTS Follows;")

    async def get_follow(self, follow_id: HttpUrl) -> Follow | None:
        with self.db.async_connection as conn:
            response = cast(
                QueryResult,
                await conn.execute(
                    """
                    MATCH (a:Actor)-[f:Follows]->(b:Actor)
                    WHERE f.id = $follow_id
                    RETURN
                    f.id as id,
                    a.id as from_actor,
                    b.id as to_actor,
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
                MATCH (a:Actor), (b:Actor)
                WHERE a.id = $from_actor AND b.id = $to_actor
                MERGE (a)-[f:Follows {id:$id}]->(b)
                ON CREATE SET
                f.status = $status
                ON MATCH SET
                f.status = $status;
                """,
                parameters=to_jsonable_python(follow),
            )

    async def delete_follow(self, follow_id: HttpUrl) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MATCH (a:Actor)-[f:Follows]->(b:Actor)
                WHERE f.id = $follow_id
                DELETE f;
                """,
                parameters={"follow_id": str(follow_id)},
            )

    async def delete_follow_by_actors(
        self, from_actor: HttpUrl, to_actor: HttpUrl
    ) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MATCH (a:Actor)-[f:Follows]->(b:Actor)
                WHERE a.id = $from_actor AND b.id = $to_actor
                DELETE f;
                """,
                parameters={
                    "from_actor": str(from_actor),
                    "to_actor": str(to_actor),
                },
            )
