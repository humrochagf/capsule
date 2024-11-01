from typing import Annotated

import bcrypt
from fastapi import Depends
from pydantic import AnyUrl
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import CapsuleSettings, get_capsule_settings

from ..models import App, Authorization, CreateAppRequest, Token
from ..repositories import AppRepository, AuthorizationRepository, TokenRepository


class AuthService:
    settings: CapsuleSettings

    apps: AppRepository
    authorizations: AuthorizationRepository
    tokens: TokenRepository

    def __init__(
        self,
        *,
        app_repository: AppRepository,
        authorization_repository: AuthorizationRepository,
        token_repository: TokenRepository,
    ) -> None:
        self.settings = get_capsule_settings()

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

    async def make_token(self, authorization_code: str) -> Token | None:
        authorization = await self.authorizations.get_authorization(authorization_code)

        if authorization is None or authorization.has_expired:
            return None

        await self.get_app(authorization.client_id)

        # TODO make token and return
        return None


def auth_service_factory() -> AuthService:
    database_service = get_database_service()

    return AuthService(
        app_repository=AppRepository("apps", database_service),
        authorization_repository=AuthorizationRepository(
            "authorizations", database_service
        ),
        token_repository=TokenRepository("tokens", database_service),
    )


def get_auth_service() -> AuthService:
    return get_service(AuthService)


AuthServiceInjection = Annotated[AuthService, Depends(get_auth_service)]
