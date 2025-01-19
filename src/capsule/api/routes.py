from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import HttpUrl
from starlette.status import HTTP_401_UNAUTHORIZED

from capsule.security.models import App, AuthenticatedApp, CreateAppRequest
from capsule.security.services import AuthServiceInjection
from capsule.utils import MultiContentTypeRoute

from .service import APIServiceInjection

router = APIRouter(tags=["api"], prefix="/api", route_class=MultiContentTypeRoute)

CredentialsInjection = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


@router.post("/v1/apps")
async def create_app(
    service: APIServiceInjection,
    request: CreateAppRequest,
) -> App:
    return await service.create_app(request)


@router.get("/v1/apps/verify_credentials")
async def verify_app(
    service: AuthServiceInjection, auth: CredentialsInjection
) -> AuthenticatedApp:
    token = await service.authenticate_token(auth.credentials)

    if token is None:
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    app = cast(App, await service.get_app(token.client_id))

    return AuthenticatedApp(
        name=app.name,
        website=app.website,
        redirect_uris=[HttpUrl(url) for url in str(app.redirect_uris).split()],
        scopes=token.scopes.split(),
    )
