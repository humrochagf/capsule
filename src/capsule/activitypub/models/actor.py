import mimetypes
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from capsule.settings import CapsuleSettings


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
    def make_main_actor(cls, settings: CapsuleSettings) -> "Actor":
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
