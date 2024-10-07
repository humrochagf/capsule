from wheke import get_service

from capsule.database.service import get_database_service
from capsule.settings import CapsuleSettings, get_capsule_settings

from .models import App, CreateAppRequest
from .repositories import AppRepository


class APIService:
    settings: CapsuleSettings

    apps: AppRepository

    def __init__(
        self,
        *,
        app_repository: AppRepository,
    ) -> None:
        self.settings = get_capsule_settings()

        self.apps = app_repository

    async def setup_repositories(self) -> None:
        await self.apps.create_indexes()

    async def create_app(self, request: CreateAppRequest) -> App:
        app = App(
            name=request.client_name,
            redirect_uris=request.redirect_uris,
            scopes=request.scopes,
            website=request.website,
        )

        await self.apps.create_app(app)

        return app


def api_service_factory() -> APIService:
    database_service = get_database_service()

    return APIService(
        app_repository=AppRepository("apps", database_service),
    )


def get_api_service() -> APIService:
    return get_service(APIService)
