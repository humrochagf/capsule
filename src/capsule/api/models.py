import secrets
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import AnyUrl, BaseModel, Field, HttpUrl

from capsule.utils import utc_now


def client_id() -> str:
    return "cp-" + secrets.token_urlsafe(40)


def client_secret() -> str:
    return secrets.token_urlsafe(43)


class CreateAppRequest(BaseModel):
    client_name: str
    redirect_uris: AnyUrl
    scopes: str = "read"
    website: HttpUrl | None = None


class App(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    website: HttpUrl | None
    redirect_uris: AnyUrl
    client_id: str = Field(default_factory=client_id)
    client_secret: str = Field(default_factory=client_secret)

    scopes: str

    created_at: datetime = Field(default_factory=utc_now)
