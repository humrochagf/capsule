from fastapi.security import OAuth2PasswordRequestForm
from wheke import get_service

from capsule.settings import CapsuleSettings, get_capsule_settings


class AuthService:
    settings: CapsuleSettings

    def __init__(self) -> None:
        self.settings = get_capsule_settings()

    async def token_auth(self, auth_form: OAuth2PasswordRequestForm) -> dict | None:
        if auth_form.username != self.settings.username:
            return None

        # TODO: do the actual auth
        return {
            "access_token": "token",
            "token_type": "Bearer",
            "scope": "read write follow push",
            "created_at": 1573979017,
        }


def auth_service_factory() -> AuthService:
    return AuthService()


def get_auth_service() -> AuthService:
    return get_service(AuthService)
