from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response, status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from starlette.templating import Jinja2Templates

from capsule.__about__ import __version__
from capsule.settings import get_capsule_settings

router = APIRouter(tags=["activitypub"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@router.get("/.well-known/host-meta")
async def well_known_host_meta(request: Request) -> Response:
    return templates.TemplateResponse(
        name="host-meta.xml",
        media_type="application/xrd+xml",
        request=request,
        context={
            "hostname": get_capsule_settings().hostname,
        },
    )


@router.get("/.well-known/nodeinfo")
async def well_known_nodeinfo() -> dict:
    return {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{get_capsule_settings().hostname}nodeinfo/2.0",
            }
        ],
    }


@router.get("/.well-known/webfinger")
async def well_known_webfinger(resource: str = "") -> dict:
    settings = get_capsule_settings()
    acct = resource.removeprefix("acct:").split("@")

    match acct:
        case [settings.username, settings.hostname.host]:
            return {}
        case [_, _]:
            raise HTTPException(HTTP_404_NOT_FOUND)
        case _:
            raise HTTPException(HTTP_400_BAD_REQUEST)


@router.get("/nodeinfo/2.0")
async def nodeinfo() -> dict:
    return {
        "version": "2.0",
        "software": {
            "name": get_capsule_settings().project_name.lower(),
            "version": __version__,
        },
        "protocols": ["activitypub"],
        "services": {
            "outbound": [],
            "inbound": [],
        },
        "usage": {
            "users": {
                "total": 1,
            },
            "localPosts": 0,
        },
        "openRegistrations": False,
        "metadata": {},
    }


@router.post("/inbox", status_code=status.HTTP_202_ACCEPTED)
async def inbox() -> None:
    pass
