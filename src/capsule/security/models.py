from datetime import datetime, timedelta
from enum import Enum

from pydantic import AnyUrl, BaseModel, Field, HttpUrl

from capsule.utils import utc_now

from .utils import client_id, secret_token

AUTHORIZATION_TTL = timedelta(seconds=60)


class CreateAppRequest(BaseModel):
    client_name: str
    redirect_uris: AnyUrl
    scopes: str = "read"
    website: HttpUrl | None = None


class AuthorizeAppRequest(BaseModel):
    client_id: str
    redirect_uri: AnyUrl
    scope: str
    state: str = ""


class GrantType(str, Enum):
    authorization_code = "authorization_code"
    client_credentials = "client_credentials"


class OAuthTokenRequest(BaseModel):
    grant_type: GrantType
    code: str
    client_id: str
    client_secret: str
    redirect_uri: AnyUrl
    code_verifier: str = ""
    scope: str = "read"


class AuthenticatedApp(BaseModel):
    name: str
    website: HttpUrl | None
    redirect_uris: list[AnyUrl]
    scopes: list[str]


class App(BaseModel):
    name: str
    website: HttpUrl | None
    redirect_uris: AnyUrl
    client_id: str = Field(default_factory=client_id)
    client_secret: str = Field(default_factory=secret_token)
    scopes: str
    created_at: datetime = Field(default_factory=utc_now)


class Authorization(BaseModel):
    client_id: str
    scopes: str
    redirect_uri: AnyUrl
    code: str = Field(default_factory=secret_token)
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def has_expired(self) -> bool:
        return utc_now() - self.created_at > AUTHORIZATION_TTL


class Token(BaseModel):
    client_id: str
    scopes: str
    token: str = Field(default_factory=secret_token)
    created_at: datetime = Field(default_factory=utc_now)
