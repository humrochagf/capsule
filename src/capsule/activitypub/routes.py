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
            return {
                "subject": f"acct:{settings.username}@{settings.hostname.host}",
                "aliases": [
                    f"{settings.hostname}@{settings.username}",
                    f"{settings.hostname}actors/{settings.username}",
                ],
                "links": [
                    {
                        "rel": "http://webfinger.net/rel/profile-page",
                        "type": "text/html",
                        "href": f"{settings.hostname}@{settings.username}",
                    },
                    {
                        "rel": "self",
                        "type": "application/activity+json",
                        "href": f"{settings.hostname}actors/{settings.username}",
                    },
                ],
            }
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


@router.get("/@{username}")
@router.get("/actors/{username}")
async def actor(username: str) -> dict:
    settings = get_capsule_settings()

    if username != settings.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        ],
        "id": f"{settings.hostname}actors/{settings.username}",
        "type": "Person",
        "name": f"{settings.name}",
        "preferredUsername": f"{settings.username}",
        "summary": f"{settings.summary}",
        "inbox": f"{settings.hostname}actors/{settings.username}/inbox",
        "outbox": f"{settings.hostname}actors/{settings.username}/outbox",
        "publicKey": {
            "id": f"{settings.hostname}actors/{settings.username}#main-key",
            "owner": f"{settings.hostname}actors/{settings.username}",
            "publicKeyPem": f"{settings.public_key}"
        }
    }


@router.post("/actors/{username}/inbox", status_code=status.HTTP_202_ACCEPTED)
async def actor_inbox(username: str) -> None:
    settings = get_capsule_settings()

    if username != settings.username:
        raise HTTPException(HTTP_404_NOT_FOUND)


@router.get("/actors/{username}/outbox")
async def actor_outbox(username: str) -> dict:
    settings = get_capsule_settings()

    if username != settings.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": 0,
        "orderedItems": [],
    }
