import mimetypes
from datetime import datetime, timezone
from enum import Enum

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
    manually_approve_followers: bool = Field(alias="manuallyApprovesFollowers")

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
            "id": f"{settings.hostname}actors/{settings.username}",
            "type": "Person",
            "name": f"{settings.name}",
            "preferredUsername": f"{settings.username}",
            "summary": f"{settings.summary}",
            "inbox": f"{settings.hostname}actors/{settings.username}/inbox",
            "outbox": f"{settings.hostname}actors/{settings.username}/outbox",
            "manuallyApprovesFollowers": False,
            "publicKey": {
                "id": f"{settings.hostname}actors/{settings.username}#main-key",
                "owner": f"{settings.hostname}actors/{settings.username}",
                "publicKeyPem": f"{settings.public_key}",
            },
        }

        if settings.profile_image:
            mime, _ = mimetypes.guess_type(settings.profile_image.name)
            data["icon"] = {
                "type": "Image",
                "mediaType": mime,
                "url": f"{settings.hostname}actors/{settings.username}/icon",
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
    actor_id: HttpUrl
    status: FollowStatus = FollowStatus.pending
