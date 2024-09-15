import mimetypes

import httpx
from pydantic import HttpUrl
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import get_capsule_settings

from .models import Actor, InboxEntry, InboxEntryStatus
from .repositories import ActorRepository, InboxRepository


class ActivityPubService:
    actors: ActorRepository
    inbox: InboxRepository

    def __init__(
        self,
        actor_repository: ActorRepository,
        inbox_repository: InboxRepository,
    ) -> None:
        self.actors = actor_repository
        self.inbox = inbox_repository

    async def setup_repositories(self) -> None:
        await self.inbox.create_indexes()
        await self.actors.create_indexes()

    def get_main_actor(self) -> Actor:
        return self.actors.get_main_actor()

    async def get_actor(self, actor_id: HttpUrl) -> Actor | None:
        return await self.actors.get_actor(actor_id)

    def get_instance_post_count(self) -> int:
        return 0

    def get_instance_actor_count(self) -> int:
        return 1

    def get_webfinger(self) -> dict:
        settings = get_capsule_settings()
        webfinger: dict = {
            "subject": f"acct:{settings.username}@{settings.hostname.host}",
            "aliases": [
                f"{settings.hostname}@{settings.username}",
                f"{settings.hostname}actors/{settings.username}",
            ],
            "links": [
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": f"{settings.hostname}@{settings.username}",
                },
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": f"{settings.hostname}actors/{settings.username}",
                },
            ],
        }

        if settings.profile_image:
            mime, _ = mimetypes.guess_type(settings.profile_image.name)
            webfinger["links"].append(
                {
                    "rel": "http://webfinger.net/rel/avatar",
                    "type": mime,
                    "href": f"{settings.hostname}actors/{settings.username}/icon",
                }
            )

        return webfinger

    async def create_inbox_entry(self, entry: InboxEntry) -> None:
        await self.inbox.create_entry(entry)

    async def fetch_actor_from_remote(self, actor_id: HttpUrl) -> Actor | None:
        headers = {"Accept": "application/activity+json"}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(str(actor_id))

            return Actor(**response.json())

    async def sync_inbox_entries(self) -> None:
        actors: dict[HttpUrl, Actor] = {}
        synced_entries: list = []

        async for entry in self.inbox.list_entries(InboxEntryStatus.created):
            if entry.activity.actor not in actors:
                actor = await self.get_actor(entry.activity.actor)

                if not actor:
                    actor = await self.fetch_actor_from_remote(entry.activity.actor)

                    if actor:
                        await self.actors.upsert_actor(actor)

                if actor:
                    actors[entry.activity.actor] = actor

            synced_entries.append(entry.id)

        await self.inbox.update_entries_state(synced_entries, InboxEntryStatus.synced)


def activitypub_service_factory() -> ActivityPubService:
    database_service = get_database_service()

    actor_repository = ActorRepository(database_service)
    inbox_repository = InboxRepository(database_service)

    return ActivityPubService(actor_repository, inbox_repository)


def get_activitypub_service() -> ActivityPubService:
    return get_service(ActivityPubService)
