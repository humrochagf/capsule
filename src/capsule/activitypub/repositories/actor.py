from capsule.activitypub.models import Actor


class ActorRepository:
    def get_main_actor(self) -> Actor:
        return Actor.make_main_actor()
