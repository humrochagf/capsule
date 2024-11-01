import time
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import AnyUrl
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from starlette.templating import Jinja2Templates

from capsule.security.models import AuthorizeAppRequest

from .forms import GrantType, OAuth2FormInjection
from .services import AuthServiceInjection

security = HTTPBasic()

BasicAuthInjection = Annotated[HTTPBasicCredentials, Depends(security)]

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
    state: str = "",
) -> HTMLResponse:
    if not service.authenticate_user(auth.username, auth.password):
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    app = await service.get_app(client_id)

    if not app:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid client_id")

    for requested_scope in scope.split():
        if requested_scope not in app.scopes.split():
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="Bad scope for this app")

    if str(redirect_uri) not in str(app.redirect_uris).split():
        raise HTTPException(
            HTTP_400_BAD_REQUEST, detail="Bad redirect_uri for this app"
        )

    return templates.TemplateResponse(
        name="oauth_authorize.html",
        request=request,
        context={
            "username": auth.username,
            "app_name": app.name,
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "state": state,
        },
    )


@router.post("/oauth/authorize")
async def authorize(
    service: AuthServiceInjection,
    auth: BasicAuthInjection,
    request: Request,
    authorize: AuthorizeAppRequest,
) -> Response:
    if not service.authenticate_user(auth.username, auth.password):
        raise HTTPException(HTTP_401_UNAUTHORIZED)

    app = await service.get_app(authorize.client_id)

    if not app:
        raise HTTPException(HTTP_400_BAD_REQUEST, detail="Invalid client_id")

    for requested_scope in authorize.scope.split():
        if requested_scope not in app.scopes.split():
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="Bad scope for this app")

    if str(authorize.redirect_uri) not in str(app.redirect_uris).split():
        raise HTTPException(
            HTTP_400_BAD_REQUEST, detail="Bad redirect_uri for this app"
        )

    authorization = await service.authorize_app(
        app.id, authorize.scope, authorize.redirect_uri
    )

    if str(authorization.redirect_uri) == "urn:ietf:wg:oauth:2.0:oob":
        return templates.TemplateResponse(
            name="oauth_code.html",
            request=request,
            context={"code": authorization.code},
        )

    query = authorization.redirect_uri.query or ""
    query += f"&code={authorization.code}" if query else f"code={authorization.code}"

    if authorize.state:
        query += f"&state={authorize.state}"

    url = authorization.redirect_uri.build(
        scheme=authorization.redirect_uri.scheme,
        username=authorization.redirect_uri.username,
        password=authorization.redirect_uri.password,
        host=authorization.redirect_uri.host or "",
        port=authorization.redirect_uri.port,
        path=authorization.redirect_uri.path,
        query=query,
        fragment=authorization.redirect_uri.fragment,
    )

    return RedirectResponse(str(url))


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
