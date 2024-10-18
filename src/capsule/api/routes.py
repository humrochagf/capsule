from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

from capsule.security.models import App, CreateAppRequest

from .service import APIService, get_api_service
from .utils import MultiContentTypeRoute

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth/token")

OAuth2TokenInjection = Annotated[str, Depends(oauth2_scheme)]
APIServiceInjection = Annotated[APIService, Depends(get_api_service)]

router = APIRouter(tags=["api"], prefix="/api", route_class=MultiContentTypeRoute)


@router.post("/v1/apps")
async def create_app(
    service: APIServiceInjection,
    request: CreateAppRequest,
) -> App:
    return await service.create_app(request)


@router.get("/v1/apps")
async def verify_app(
    token: OAuth2TokenInjection,
) -> dict:
    return {"token": token}
