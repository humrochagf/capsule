from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import CapsuleSettings, get_capsule_settings

from ..repositories import TokenRepository


class AuthService:
    settings: CapsuleSettings
    crypt_context: CryptContext

    tokens: TokenRepository

    def __init__(
        self,
        *,
        token_repository: TokenRepository,
    ) -> None:
        self.settings = get_capsule_settings()
        self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        self.tokens = token_repository

    async def setup_repositories(self) -> None:
        await self.tokens.create_indexes()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.crypt_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.crypt_context.hash(password)

    async def authenticate_user(self, auth_form: OAuth2PasswordRequestForm) -> bool:
        if auth_form.username != self.settings.username:
            return False

        return self.verify_password(auth_form.password, self.settings.password)


def auth_service_factory() -> AuthService:
    database_service = get_database_service()

    return AuthService(
        token_repository=TokenRepository("tokens", database_service),
    )


def get_auth_service() -> AuthService:
    return get_service(AuthService)
