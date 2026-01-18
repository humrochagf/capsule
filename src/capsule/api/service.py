from typing import Annotated

from fastapi import Depends
from svcs import Container
from svcs.fastapi import DepContainer
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


def api_service_factory(container: Container) -> APIService:
    return APIService(
        auth_service=get_auth_service(container),
    )


def get_api_service(container: Container) -> APIService:
    return get_service(container, APIService)


def _api_service_injection(container: DepContainer) -> APIService:
    return get_api_service(container)


APIServiceInjection = Annotated[APIService, Depends(_api_service_injection)]
