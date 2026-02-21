import mimetypes
from typing import Annotated, cast

import httpx
from fastapi import Depends
from loguru import logger
from pydantic import HttpUrl
from svcs import Container
from svcs.fastapi import DepContainer
from wheke import get_service
from wheke_ladybug import get_ladybug_service
from wheke_sqlmodel import get_sqlmodel_service

from capsule.security.utils import SignedRequestAuth
from capsule.settings import CapsuleSettings, get_capsule_settings

from .exceptions import EnsureActorError
from .models import Actor, Follow, FollowStatus, InboxEntry, InboxEntryStatus
from .repositories import ActorRepository, FollowRepository, InboxRepository


class ActivityPubService:
    settings: CapsuleSettings

    inbox: InboxRepository
    actors: ActorRepository
    follows: FollowRepository

    def __init__(
        self,
        *,
        settings: CapsuleSettings,
        inbox_repository: InboxRepository,
        actor_repository: ActorRepository,
        follows_repository: FollowRepository,
    ) -> None:
        self.settings = settings

        self.inbox = inbox_repository
        self.actors = actor_repository
        self.follows = follows_repository

    async def create_tables(self) -> None:
        await self.actors.create_table()
        await self.follows.create_table()

    async def drop_tables(self) -> None:
        await self.follows.drop_table()
        await self.actors.drop_table()

    def get_main_actor(self) -> Actor:
        return self.actors.get_main_actor(self.settings)

    async def get_actor(self, actor_id: HttpUrl) -> Actor | None:
        return await self.actors.get_actor(actor_id)

    def get_instance_post_count(self) -> int:
        return 0

    def get_instance_actor_count(self) -> int:
        return 1

    def get_webfinger(self) -> dict:
        webfinger: dict = {
            "subject": f"acct:{self.settings.username}@{self.settings.hostname.host}",
            "aliases": [self.settings.profile_url, self.settings.actor_url],
            "links": [
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": self.settings.profile_url,
                },
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": self.settings.actor_url,
                },
            ],
        }

        if self.settings.profile_image:
            mime, _ = mimetypes.guess_type(self.settings.profile_image.name)
            webfinger["links"].append(
                {
                    "rel": "http://webfinger.net/rel/avatar",
                    "type": mime,
                    "href": f"{self.settings.actor_url}/icon",
                }
            )

        return webfinger

    async def create_inbox_entry(self, entry: InboxEntry) -> InboxEntry:
        return await self.inbox.create_entry(entry)

    async def fetch_actor_from_remote(self, actor_id: HttpUrl) -> Actor | None:
        auth = SignedRequestAuth(
            public_key_id=HttpUrl(self.settings.public_key_id),
            private_key=self.settings.private_key,
        )
        headers = {
            "User-Agent": self.settings.user_agent,
            "Accept": "application/activity+json,application/ld+json",
        }
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(str(actor_id))

            if response.is_error:
                logger.bind(
                    actor_id=actor_id,
                    http_status=response.status_code,
                    http_message=response.text,
                ).error("Failed to fetch actor from remote")
                return None

            return Actor(**response.json())

    async def ensure_main_actor(self) -> None:
        actor = await self.get_actor(HttpUrl(self.settings.actor_url))

        if not actor:
            await self.actors.upsert_actor(Actor.make_main_actor(self.settings))

    async def ensure_remote_actor(self, entry: InboxEntry) -> Actor:
        actor = await self.get_actor(entry.activity.actor)

        if not actor:
            actor = await self.fetch_actor_from_remote(entry.activity.actor)

            if actor:
                await self.actors.upsert_actor(actor)
            else:
                raise EnsureActorError

        return actor

    async def cleanup_inbox_entries(self) -> None:
        await self.inbox.delete_entries()

    async def sync_inbox_entries(self, status: InboxEntryStatus) -> None:
        if status != InboxEntryStatus.synced:
            async for entry in self.inbox.list_entries(status):
                await self.handle_activity(entry)

    async def handle_activity(self, entry: InboxEntry) -> None:
        entry_id = entry.id
        entry_status = entry.status

        try:
            match entry.activity.type, entry.activity.object_type:
                case "Follow", _:
                    entry_status = await self.handle_follow(entry)
                case "Undo", "Follow":
                    entry_status = await self.handle_unfollow(entry)
                case "Delete", None:
                    entry_status = await self.handle_delete(entry)
                case activity_type, object_type:
                    await self.ensure_remote_actor(entry)
                    entry_status = InboxEntryStatus.not_implemented

                    logger.warning(
                        "Activity type {} and object type {} pair"
                        ", is not supported yet",
                        activity_type,
                        object_type,
                    )
        except EnsureActorError:
            entry_status = InboxEntryStatus.error

        await self.inbox.update_entries_state([entry_id], entry_status)

    async def handle_follow(self, entry: InboxEntry) -> InboxEntryStatus:
        actor = await self.ensure_remote_actor(entry)
        follow = await self.follows.get_follow(entry.activity.id)

        if follow is None:
            follow = Follow(
                id=entry.activity.id,
                from_actor=entry.activity.actor,
                to_actor=HttpUrl(self.settings.actor_url),
                status=FollowStatus.accepted,
            )
            auth = SignedRequestAuth(
                public_key_id=HttpUrl(self.settings.public_key_id),
                private_key=self.settings.private_key,
            )
            headers = {
                "User-Agent": self.settings.user_agent,
                "Content-Type": "application/activity+json",
            }

            async with httpx.AsyncClient(auth=auth, headers=headers) as client:
                response = await client.post(
                    str(actor.inbox), json=follow.to_accept_ap()
                )

                if response.is_error:
                    logger.bind(
                        follow_id=follow.id,
                        http_status=response.status_code,
                        http_message=response.text,
                    ).error("Failed to accept follow")

                    return InboxEntryStatus.error

            await self.follows.upsert_follow(follow)

        return InboxEntryStatus.synced

    async def handle_unfollow(self, entry: InboxEntry) -> InboxEntryStatus:
        actor = await self.get_actor(entry.activity.actor)
        object_data = cast(dict, entry.activity.object)
        follow_id = HttpUrl(object_data.get("id", ""))
        follow = await self.follows.get_follow(follow_id)

        if (
            follow is not None
            and actor is not None
            and follow.from_actor == actor.id
            and object_data.get("actor") == str(actor.id)
        ):
            await self.follows.delete_follow(follow.id)

        return InboxEntryStatus.synced

    async def handle_delete(self, entry: InboxEntry) -> InboxEntryStatus:
        actor = await self.get_actor(entry.activity.actor)

        if actor is not None and entry.activity.object == str(actor.id):
            logger.info("Delete triggered {} cleanup", actor.id)

            main_actor = HttpUrl(self.settings.actor_url)

            await self.follows.delete_follow_by_actors(actor.id, main_actor)
            await self.follows.delete_follow_by_actors(main_actor, actor.id)
            await self.actors.delete_actor(actor.id)

        return InboxEntryStatus.synced


def activitypub_service_factory(container: Container) -> ActivityPubService:
    sqlmodel_service = get_sqlmodel_service(container)
    ladybug_service = get_ladybug_service(container)

    return ActivityPubService(
        settings=get_capsule_settings(container),
        inbox_repository=InboxRepository(sqlmodel_service),
        actor_repository=ActorRepository(ladybug_service),
        follows_repository=FollowRepository(ladybug_service),
    )


def get_activitypub_service(container: Container) -> ActivityPubService:
    return get_service(container, ActivityPubService)


def _activitypub_service_injection(container: DepContainer) -> ActivityPubService:
    return get_activitypub_service(container)


ActivityPubServiceInjection = Annotated[
    ActivityPubService, Depends(_activitypub_service_injection)
]
