from datetime import datetime, timedelta
from enum import Enum

from pydantic import AnyUrl, BaseModel, HttpUrl
from sqlmodel import Field, SQLModel

from capsule.types import DateTimeType, UrlType
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


class App(SQLModel, table=True):
    name: str
    website: HttpUrl | None = Field(sa_type=UrlType, nullable=True)
    redirect_uris: AnyUrl = Field(sa_type=UrlType)
    client_id: str = Field(default_factory=client_id, primary_key=True)
    client_secret: str = Field(default_factory=secret_token)
    scopes: str
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTimeType)


class Authorization(SQLModel, table=True):
    client_id: str = Field(primary_key=True)
    scopes: str
    redirect_uri: AnyUrl = Field(sa_type=UrlType)
    code: str = Field(default_factory=secret_token, unique=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTimeType)

    @property
    def has_expired(self) -> bool:
        return utc_now() - self.created_at > AUTHORIZATION_TTL


class Token(SQLModel, table=True):
    client_id: str = Field(primary_key=True)
    scopes: str
    token: str = Field(default_factory=secret_token, unique=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTimeType)
