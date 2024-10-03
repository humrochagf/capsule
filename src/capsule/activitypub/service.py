import mimetypes
from collections import defaultdict
from typing import cast

import httpx
from loguru import logger
from pydantic import HttpUrl
from pydantic_core import Url
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.security.utils import SignedRequestAuth
from capsule.settings import CapsuleSettings, get_capsule_settings

from .models import Actor, Follow, FollowStatus, InboxEntry, InboxEntryStatus
from .repositories import ActorRepository, FollowRepository, InboxRepository


class ActivityPubService:
    settings: CapsuleSettings

    inbox: InboxRepository
    actors: ActorRepository
    followers: FollowRepository
    following: FollowRepository

    def __init__(
        self,
        *,
        inbox_repository: InboxRepository,
        actor_repository: ActorRepository,
        followers_repository: FollowRepository,
        following_repository: FollowRepository,
    ) -> None:
        self.settings = get_capsule_settings()

        self.inbox = inbox_repository
        self.actors = actor_repository
        self.followers = followers_repository
        self.following = following_repository

    async def setup_repositories(self) -> None:
        await self.inbox.create_indexes()
        await self.actors.create_indexes()
        await self.followers.create_indexes()
        await self.following.create_indexes()

    def get_main_actor(self) -> Actor:
        return self.actors.get_main_actor()

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

    async def create_inbox_entry(self, entry: InboxEntry) -> None:
        await self.inbox.create_entry(entry)

    async def fetch_actor_from_remote(self, actor_id: HttpUrl) -> Actor | None:
        auth = SignedRequestAuth(
            public_key_id=Url(self.settings.public_key_id),
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

    async def sync_inbox_entries(self) -> None:
        actors: dict[HttpUrl, Actor] = {}
        parsed_entries: dict[InboxEntryStatus, list] = defaultdict(list)

        async for entry in self.inbox.list_entries(InboxEntryStatus.created):
            actor = actors.get(entry.activity.actor)

            if actor is None:
                actor = await self.get_actor(entry.activity.actor)

                if not actor:
                    actor = await self.fetch_actor_from_remote(entry.activity.actor)

                    if actor:
                        await self.actors.upsert_actor(actor)

                if actor:
                    actors[entry.activity.actor] = actor

            if actor is None:
                parsed_entries[InboxEntryStatus.error].append(entry.id)
                continue

            match entry.activity.type, entry.activity.object_type:
                case "Follow", _:
                    await self.handle_follow(entry, actor)
                case "Undo", "Follow":
                    await self.handle_unfollow(entry, actor)
                case activity_type, object_type:
                    entry.status = InboxEntryStatus.not_implemented
                    logger.warning(
                        "Activity type {} and object type {} pair"
                        ", is not supported yet",
                        activity_type,
                        object_type,
                    )

            parsed_entries[entry.status].append(entry.id)

        for status, entries in parsed_entries.items():
            await self.inbox.update_entries_state(entries, status)

    async def handle_follow(self, entry: InboxEntry, actor: Actor) -> None:
        follow = await self.followers.get_follow(entry.activity.id)

        if follow is None:
            follow = Follow(
                id=entry.activity.id,
                actor=entry.activity.actor,
                status=FollowStatus.accepted,
            )
            auth = SignedRequestAuth(
                public_key_id=Url(self.settings.public_key_id),
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
                    entry.status = InboxEntryStatus.error
                    return None

            await self.followers.upsert_follow(follow)
            entry.status = InboxEntryStatus.synced

    async def handle_unfollow(self, entry: InboxEntry, actor: Actor) -> None:
        object_data = cast(dict, entry.activity.object)
        follow_id = Url(object_data.get("id", ""))
        follow = await self.followers.get_follow(follow_id)

        if (
            follow is not None
            and follow.actor == actor.id
            and object_data.get("actor") == str(actor.id)
        ):
            await self.followers.delete_follow(follow.id)

        entry.status = InboxEntryStatus.synced


def activitypub_service_factory() -> ActivityPubService:
    database_service = get_database_service()

    return ActivityPubService(
        inbox_repository=InboxRepository("inbox", database_service),
        actor_repository=ActorRepository("actors", database_service),
        followers_repository=FollowRepository("followers", database_service),
        following_repository=FollowRepository("following", database_service),
    )


def get_activitypub_service() -> ActivityPubService:
    return get_service(ActivityPubService)
