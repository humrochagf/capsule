import time
from typing import Annotated

from fastapi import APIRouter, Depends

from .forms import GrantType, OAuth2AuthorizationCodeForm
from .services import AuthService, get_auth_service

AuthServiceInjection = Annotated[AuthService, Depends(get_auth_service)]
OAuth2FormInjection = Annotated[OAuth2AuthorizationCodeForm, Depends()]

router = APIRouter(tags=["security"])


@router.post("/oauth/authorize")
async def authorize_app(
    service: AuthServiceInjection, auth_form: OAuth2FormInjection
) -> dict:
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
