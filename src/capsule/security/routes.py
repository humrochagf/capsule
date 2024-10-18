import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_400_BAD_REQUEST

from .services import AuthService, get_auth_service

AuthServiceInjection = Annotated[AuthService, Depends(get_auth_service)]
OAuth2FormInjection = Annotated[OAuth2PasswordRequestForm, Depends()]

router = APIRouter(tags=["security"])


@router.post("/oauth/token")
async def token_auth(
    service: AuthServiceInjection, auth_form: OAuth2FormInjection
) -> dict:
    if not await service.authenticate_user(auth_form):
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    match auth_form.grant_type:
        case "client_credentials":
            # individual client credential token unsupported
            # returning fixed token for apps interacting with
            # public apis
            return {
                "access_token": "__app__",
                "token_type": "Bearer",
                "scope": "read",
                "created_at": int(time.time()),
            }
        case "authorization_code":
            return {
                "access_token": "token",
                "token_type": "Bearer",
                "scope": "read write follow push",
                "created_at": 1573979017,
            }
        case _:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid grant type")
