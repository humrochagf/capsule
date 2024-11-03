from typing import Annotated

from fastapi import Depends
from wheke import get_service

from capsule.security.models import App, CreateAppRequest
from capsule.security.services import AuthService, get_auth_service


class APIService:
    auth: AuthService

    def __init__(
        self,
        *,
        auth_service: AuthService,
    ) -> None:
        self.auth = auth_service

    async def create_app(self, request: CreateAppRequest) -> App:
        return await self.auth.create_app(request)


def api_service_factory() -> APIService:
    return APIService(
        auth_service=get_auth_service(),
    )


def get_api_service() -> APIService:
    return get_service(APIService)


APIServiceInjection = Annotated[APIService, Depends(get_api_service)]
