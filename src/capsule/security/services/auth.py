from typing import Annotated

import bcrypt
from fastapi import Depends
from pydantic import AnyUrl
from svcs import Container
from svcs.fastapi import DepContainer
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import CapsuleSettings, get_capsule_settings

from ..models import App, Authorization, CreateAppRequest, OAuthTokenRequest, Token
from ..repositories import AppRepository, AuthorizationRepository, TokenRepository


class AuthService:
    settings: CapsuleSettings

    apps: AppRepository
    authorizations: AuthorizationRepository
    tokens: TokenRepository

    def __init__(
        self,
        *,
        settings: CapsuleSettings,
        app_repository: AppRepository,
        authorization_repository: AuthorizationRepository,
        token_repository: TokenRepository,
    ) -> None:
        self.settings = settings

        self.apps = app_repository
        self.authorizations = authorization_repository
        self.tokens = token_repository

    async def setup_repositories(self) -> None:
        await self.apps.create_indexes()
        await self.authorizations.create_indexes()
        await self.tokens.create_indexes()

    async def create_app(self, request: CreateAppRequest) -> App:
        app = App(
            name=request.client_name,
            redirect_uris=request.redirect_uris,
            scopes=request.scopes,
            website=request.website,
        )

        await self.apps.create_app(app)

        return app

    async def get_app(self, client_id: str) -> App | None:
        return await self.apps.get_app(client_id)

    async def authorize_app(
        self, client_id: str, scopes: str, redirect_uri: AnyUrl
    ) -> Authorization:
        authorization = Authorization(
            client_id=client_id, scopes=scopes, redirect_uri=redirect_uri
        )

        await self.authorizations.upsert_authorization(authorization)

        return authorization

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf8"), hashed_password.encode("utf8")
        )

    def get_password_hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt()).decode("utf8")

    def authenticate_user(self, username: str, password: str) -> bool:
        return username == self.settings.username and self.verify_password(
            password, self.settings.password
        )

    async def authenticate_token(self, access_token: str) -> Token | None:
        token = await self.tokens.get_token(access_token)

        if token is None:
            return None

        return token

    async def make_oauth_token(self, request: OAuthTokenRequest) -> Token | None:
        app = await self.get_app(request.client_id)
        authorization = await self.authorizations.get_authorization(request.code)

        if app is None or authorization is None:
            return None

        is_valid = (
            not authorization.has_expired
            and request.redirect_uri == authorization.redirect_uri
            and request.client_id == authorization.client_id
            and request.client_secret == app.client_secret
        )

        if not is_valid:
            return None

        token = Token(
            client_id=app.client_id,
            scopes=authorization.scopes,
        )

        await self.tokens.create_token(token)

        return token


def auth_service_factory(container: Container) -> AuthService:
    settings = get_capsule_settings(container)
    database_service = get_database_service(container)

    return AuthService(
        settings=settings,
        app_repository=AppRepository("apps", database_service),
        authorization_repository=AuthorizationRepository(
            "authorizations", database_service
        ),
        token_repository=TokenRepository("tokens", database_service),
    )


def get_auth_service(container: Container) -> AuthService:
    return get_service(container, AuthService)


def _auth_service_injection(container: DepContainer) -> AuthService:
    return get_auth_service(container)


AuthServiceInjection = Annotated[AuthService, Depends(_auth_service_injection)]
