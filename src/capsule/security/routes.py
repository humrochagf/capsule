import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import AnyUrl
from starlette.responses import HTMLResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

from .forms import GrantType, OAuth2AuthorizationCodeForm
from .services import AuthService, get_auth_service

security = HTTPBasic()

AuthServiceInjection = Annotated[AuthService, Depends(get_auth_service)]
BasicAuthInjection = Annotated[HTTPBasicCredentials, Depends(security)]
OAuth2FormInjection = Annotated[OAuth2AuthorizationCodeForm, Depends()]

router = APIRouter(tags=["security"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@router.get("/oauth/authorize", include_in_schema=False)
async def request_authorization(
    service: AuthServiceInjection,
    auth: BasicAuthInjection,
    request: Request,
    client_id: str,
    scope: str,
    redirect_uri: AnyUrl,
    response_type: str,

) -> HTMLResponse:
    if not service.authenticate_user(auth.username, auth.password):
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    return templates.TemplateResponse(
        name="authorize.html",
        request=request,
        context={
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
