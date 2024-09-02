import mimetypes

from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import get_capsule_settings

from .models import Actor, InboxEntry
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

    def get_main_actor(self) -> Actor:
        return self.actors.get_main_actor()

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


def activitypub_service_factory() -> ActivityPubService:
    actor_repository = ActorRepository()
    inbox_repository = InboxRepository(get_database_service())

    return ActivityPubService(actor_repository, inbox_repository)


def get_activitypub_service() -> ActivityPubService:
    return get_service(ActivityPubService)
