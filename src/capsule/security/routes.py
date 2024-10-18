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
    if not service.authenticate_user(auth_form):
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    return {
        "access_token": "token",
        "token_type": "Bearer",
        "scope": "read write follow push",
        "created_at": 1573979017,
    }
