import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED

from .forms import GrantType, OAuth2AuthorizationCodeForm
from .services import AuthService, get_auth_service

security = HTTPBasic()

AuthServiceInjection = Annotated[AuthService, Depends(get_auth_service)]
BasicAuthInjection = Annotated[HTTPBasicCredentials, Depends(security)]
OAuth2FormInjection = Annotated[OAuth2AuthorizationCodeForm, Depends()]

router = APIRouter(tags=["security"])


@router.get("/oauth/authorize")
async def authorize_app(
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
