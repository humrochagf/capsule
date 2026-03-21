from typing import cast

from pydantic import HttpUrl
from pydantic_core import to_jsonable_python
from real_ladybug import QueryResult
from wheke_ladybug import LadybugRepository

from capsule.activitypub.models import Actor, ActorAP


class ActorRepository(LadybugRepository):
    async def create_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                CREATE NODE TABLE IF NOT EXISTS Actor
                (
                    id STRING PRIMARY KEY,
                    ap_data JSON,
                    is_local BOOLEAN
                );
                """
            )

    async def drop_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute("DROP TABLE IF EXISTS Actor;")

    async def get_actor(self, actor_id: HttpUrl) -> Actor | None:
        with self.db.async_connection as conn:
            response = cast(
                QueryResult,
                await conn.execute(
                    """
                    MATCH (a:Actor)
                    WHERE a.id = $actor_id
                    RETURN
                    a.id AS id,
                    a.ap_data AS ap_data,
                    a.is_local AS is_local;
                    """,
                    parameters={"actor_id": str(actor_id)},
                ),
            )

            response_data = cast(list[dict], response.rows_as_dict().get_all())

            if len(response_data) > 0:
                data = response_data[0]
            else:
                return None

            data["ap_data"] = ActorAP.model_validate_json(data["ap_data"])

            return Actor.model_validate(data)

    async def upsert_actor(self, actor: Actor) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MERGE (a:Actor {id: $id})
                ON CREATE SET
                a.ap_data = to_json($ap_data),
                a.is_local = $is_local
                ON MATCH SET
                a.ap_data = to_json($ap_data),
                a.is_local = $is_local;
                """,
                parameters=to_jsonable_python(actor),
            )

    async def delete_actor(self, actor_id: HttpUrl) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MATCH (a:Actor)
                WHERE a.id = $actor_id
                DELETE a;
                """,
                parameters={"actor_id": str(actor_id)},
            )
