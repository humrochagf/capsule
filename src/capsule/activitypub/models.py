import mimetypes
from datetime import datetime, timezone
from enum import Enum
from uuid import NAMESPACE_URL, uuid5

from bson.objectid import ObjectId
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from capsule.settings import get_capsule_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PublicKey(BaseModel):
    id: HttpUrl
    owner: HttpUrl
    public_key_pem: str = Field(alias="publicKeyPem")


class ActorType(str, Enum):
    application = "Application"
    group = "Group"
    organization = "Organization"
    person = "Person"
    service = "Service"


class Actor(BaseModel):
    id: HttpUrl
    type: ActorType
    name: str
    summary: str
    username: str = Field(alias="preferredUsername")
    inbox: HttpUrl
    outbox: HttpUrl
    public_key: PublicKey = Field(alias="publicKey")
    manually_approve_followers: bool = Field(False, alias="manuallyApprovesFollowers")

    model_config = ConfigDict(extra="allow")

    @classmethod
    def make_main_actor(cls) -> "Actor":
        settings = get_capsule_settings()
        data: dict = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
                {
                    "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
                },
            ],
            "id": settings.actor_url,
            "type": "Person",
            "name": f"{settings.name}",
            "preferredUsername": f"{settings.username}",
            "summary": f"{settings.summary}",
            "inbox": f"{settings.actor_url}/inbox",
            "outbox": f"{settings.actor_url}/outbox",
            "manuallyApprovesFollowers": False,
            "publicKey": {
                "id": f"{settings.public_key_id}",
                "owner": f"{settings.actor_url}",
                "publicKeyPem": f"{settings.public_key}",
            },
        }

        if settings.profile_image:
            mime, _ = mimetypes.guess_type(settings.profile_image.name)
            data["icon"] = {
                "type": "Image",
                "mediaType": mime,
                "url": f"{settings.actor_url}/icon",
            }

        return Actor(**data)


class Activity(BaseModel):
    id: HttpUrl
    actor: HttpUrl
    type: str

    model_config = ConfigDict(extra="allow")


class InboxEntryStatus(str, Enum):
    created = "created"
    synced = "synced"
    error = "error"
    not_implemented = "not_implemented"


class InboxEntry(BaseModel):
    id: ObjectId | None = Field(alias="_id", default=None, exclude=True)
    status: InboxEntryStatus = InboxEntryStatus.created
    activity: Activity
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(arbitrary_types_allowed=True)


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
