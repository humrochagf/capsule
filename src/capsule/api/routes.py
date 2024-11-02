from fastapi import APIRouter

from capsule.security.models import App, CreateAppRequest

from .service import APIServiceInjection
from .utils import MultiContentTypeRoute

router = APIRouter(tags=["api"], prefix="/api", route_class=MultiContentTypeRoute)


@router.post("/v1/apps")
async def create_app(
    service: APIServiceInjection,
    request: CreateAppRequest,
) -> App:
    return await service.create_app(request)
