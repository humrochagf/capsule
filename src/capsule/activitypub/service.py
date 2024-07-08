from wheke import get_service

from capsule.activitypub.models import Actor
from capsule.activitypub.repositories.actor import ActorRepository


class ActivityPubService:
    actor_repository: ActorRepository

    def __init__(self) -> None:
        self.actor_repository = ActorRepository()

    def get_main_actor(self) -> Actor:
        return self.actor_repository.get_main_actor()

    def get_instance_post_count(self) -> int:
        return 0

    def get_instance_actor_count(self) -> int:
        return 1


def activitypub_service_factory() -> ActivityPubService:
    return ActivityPubService()


def get_activitypub_service() -> ActivityPubService:
    return get_service(ActivityPubService)
