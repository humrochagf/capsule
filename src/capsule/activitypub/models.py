from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from capsule.settings import get_capsule_settings


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

    model_config = ConfigDict(extra="allow")

    @classmethod
    def make_main_actor(cls) -> "Actor":
        settings = get_capsule_settings()
        data: dict = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": f"{settings.hostname}actors/{settings.username}",
            "type": "Person",
            "name": f"{settings.name}",
            "preferredUsername": f"{settings.username}",
            "summary": f"{settings.summary}",
            "inbox": f"{settings.hostname}actors/{settings.username}/inbox",
            "outbox": f"{settings.hostname}actors/{settings.username}/outbox",
            "publicKey": {
                "id": f"{settings.hostname}actors/{settings.username}#main-key",
                "owner": f"{settings.hostname}actors/{settings.username}",
                "publicKeyPem": f"{settings.public_key}",
            },
        }

        return Actor(**data)
