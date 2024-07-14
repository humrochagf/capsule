from wheke import get_service

from capsule.database.service import get_database_service

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

    async def create_inbox_entry(self, entry: InboxEntry) -> None:
        await self.inbox.create_entry(entry)


def activitypub_service_factory() -> ActivityPubService:
    actor_repository = ActorRepository()
    inbox_repository = InboxRepository(get_database_service())

    return ActivityPubService(actor_repository, inbox_repository)


def get_activitypub_service() -> ActivityPubService:
    return get_service(ActivityPubService)
