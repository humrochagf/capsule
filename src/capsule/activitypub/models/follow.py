from enum import Enum
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, HttpUrl

from capsule.settings import get_capsule_settings


class FollowStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"


class Follow(BaseModel):
    id: HttpUrl
    actor: HttpUrl
    status: FollowStatus = FollowStatus.pending

    def to_accept_ap(self) -> dict:
        settings = get_capsule_settings()
        activity_id = uuid5(NAMESPACE_URL, str(self.id))

        return {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
                {
                    "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
                },
            ],
            "type": "Accept",
            "id": f"{settings.actor_url}/activity/{activity_id}",
            "actor": settings.actor_url,
            "object": {
                "type": "Follow",
                "id": str(self.id),
                "actor": str(self.actor),
                "object": settings.actor_url,
            },
        }
