from typing import cast

from pydantic import HttpUrl
from pydantic_core import to_jsonable_python
from real_ladybug import QueryResult
from wheke_ladybug import LadybugRepository

from capsule.activitypub.models import Actor
from capsule.settings import CapsuleSettings


class ActorRepository(LadybugRepository):
    async def create_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                CREATE NODE TABLE IF NOT EXISTS Actor
                (
                    id STRING PRIMARY KEY,
                    type STRING,
                    name STRING,
                    summary STRING,
                    username STRING,
                    inbox STRING,
                    outbox STRING,
                    public_key STRUCT
                    (
                        id STRING,
                        owner STRING,
                        public_key_pem STRING
                    ),
                    manually_approve_followers BOOLEAN
                );
                """
            )

    async def drop_table(self) -> None:
        with self.db.async_connection as conn:
            await conn.execute("DROP TABLE IF EXISTS Actor;")

    def get_main_actor(self, settings: CapsuleSettings) -> Actor:
        return Actor.make_main_actor(settings)

    async def get_actor(self, actor_id: HttpUrl) -> Actor | None:
        with self.db.async_connection as conn:
            response = cast(
                QueryResult,
                await conn.execute(
                    """
                    MATCH (a:Actor)
                    WHERE a.id = $actor_id
                    RETURN
                    a.id as id,
                    a.type as type,
                    a.name as name,
                    a.summary as summary,
                    a.username as username,
                    a.inbox as inbox,
                    a.outbox as outbox,
                    a.public_key as public_key,
                    a.manually_approve_followers as manually_approve_followers;
                    """,
                    parameters={"actor_id": str(actor_id)},
                ),
            )

            data = cast(list[dict], response.rows_as_dict().get_all())
            return (
                Actor.model_validate(data[0], by_name=True) if len(data) > 0 else None
            )

    async def upsert_actor(self, actor: Actor) -> None:
        with self.db.async_connection as conn:
            await conn.execute(
                """
                MERGE (a:Actor {id: $id})
                ON CREATE SET
                a.type = $type,
                a.name = $name,
                a.summary = $summary,
                a.username = $username,
                a.inbox = $inbox,
                a.outbox = $outbox,
                a.public_key = $public_key,
                a.manually_approve_followers = $manually_approve_followers
                ON MATCH SET
                a.type = $type,
                a.name = $name,
                a.summary = $summary,
                a.username = $username,
                a.inbox = $inbox,
                a.outbox = $outbox,
                a.public_key = $public_key,
                a.manually_approve_followers = $manually_approve_followers;
                """,
                parameters=to_jsonable_python(actor, by_alias=False),
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
