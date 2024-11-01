import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import AnyUrl
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

from .forms import GrantType, OAuth2FormInjection
from .services import AuthServiceInjection

security = HTTPBasic()

BasicAuthInjection = Annotated[HTTPBasicCredentials, Depends(security)]

router = APIRouter(tags=["security"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@router.get("/oauth/authorize", include_in_schema=False)
async def request_authorization(
    auth_service: AuthServiceInjection,
    auth: BasicAuthInjection,
    request: Request,
    client_id: str,
    scope: str,
    redirect_uri: AnyUrl,
    response_type: str,
) -> HTMLResponse:
    if not auth_service.authenticate_user(auth.username, auth.password):
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    app = await auth_service.get_app(client_id)

    if not app:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid client_id")

    return templates.TemplateResponse(
        name="authorize.html",
        request=request,
        context={
            "username": auth.username,
            "app_name": app.name,
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
        },
    )


@router.post("/oauth/authorize")
async def authorize(
    service: AuthServiceInjection,
    auth: BasicAuthInjection,
) -> dict:
    if not service.authenticate_user(auth.username, auth.password):
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    return {}


@router.post("/oauth/token")
async def token_auth(
    service: AuthServiceInjection, auth_form: OAuth2FormInjection
) -> dict:
    match auth_form.grant_type:
        case GrantType.authorization_code:
            return {
                "access_token": "token",
                "token_type": "Bearer",
                "scope": "read write follow push",
                "created_at": 1573979017,
            }
        case GrantType.client_credentials:
            # individual client credential token unsupported
            # returning fixed token for apps interacting with
            # public apis
            return {
                "access_token": "__app__",
                "token_type": "Bearer",
                "scope": "read",
                "created_at": int(time.time()),
            }
