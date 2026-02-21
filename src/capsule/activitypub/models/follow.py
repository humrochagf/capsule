from enum import StrEnum
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, HttpUrl


class FollowStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"


class Follow(BaseModel):
    id: HttpUrl
    from_actor: HttpUrl
    to_actor: HttpUrl
    status: FollowStatus = FollowStatus.pending

    def to_accept_ap(self) -> dict:
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
            "id": f"{self.to_actor}/activity/{activity_id}",
            "actor": str(self.to_actor),
            "object": {
                "type": "Follow",
                "id": str(self.id),
                "actor": str(self.from_actor),
                "object": str(self.to_actor),
            },
        }
