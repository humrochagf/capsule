from typing import Annotated

from fastapi import APIRouter, Depends

from .models import App, CreateAppRequest
from .service import APIService, get_api_service
from .utils import MultiContentTypeRoute

router = APIRouter(tags=["api"], prefix="/api", route_class=MultiContentTypeRoute)

APIServiceInjection = Annotated[APIService, Depends(get_api_service)]


@router.post("/v1/apps")
async def create_app(
    service: APIServiceInjection,
    request: CreateAppRequest,
) -> App:
    return await service.create_app(request)
