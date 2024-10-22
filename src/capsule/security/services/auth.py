from passlib.context import CryptContext
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import CapsuleSettings, get_capsule_settings

from ..models import App, CreateAppRequest
from ..repositories import AppRepository, TokenRepository


class AuthService:
    settings: CapsuleSettings
    crypt_context: CryptContext

    apps: AppRepository
    tokens: TokenRepository

    def __init__(
        self,
        *,
        app_repository: AppRepository,
        token_repository: TokenRepository,
    ) -> None:
        self.settings = get_capsule_settings()
        self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        self.apps = app_repository
        self.tokens = token_repository

    async def setup_repositories(self) -> None:
        await self.apps.create_indexes()
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

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.crypt_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.crypt_context.hash(password)

    async def authenticate_user(self, username: str, password: str) -> bool:
        return username == self.settings.username and self.verify_password(
            password, self.settings.password
        )


def auth_service_factory() -> AuthService:
    database_service = get_database_service()

    return AuthService(
        app_repository=AppRepository("apps", database_service),
        token_repository=TokenRepository("tokens", database_service),
    )


def get_auth_service() -> AuthService:
    return get_service(AuthService)
