import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from starlette.templating import Jinja2Templates

from capsule.__about__ import __version__
from capsule.settings import get_capsule_settings

from .models import Actor, Activity, InboxEntry
from .service import ActivityPubService, get_activitypub_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["activitypub"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")

ActivityPubServiceInjection = Annotated[
    ActivityPubService, Depends(get_activitypub_service)
]


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
async def nodeinfo(service: ActivityPubServiceInjection) -> dict:
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
                "total": service.get_instance_actor_count(),
            },
            "localPosts": service.get_instance_post_count(),
        },
        "openRegistrations": False,
        "metadata": {},
    }


@router.get("/@{username}")
@router.get("/actors/{username}")
async def actor(service: ActivityPubServiceInjection, username: str) -> Actor:
    main_actor = service.get_main_actor()

    if username != main_actor.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return main_actor


@router.post("/actors/{username}/inbox", status_code=status.HTTP_202_ACCEPTED)
async def actor_inbox(
    service: ActivityPubServiceInjection, username: str, activity: Activity
) -> None:
    main_actor = service.get_main_actor()

    if username != main_actor.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    await service.create_inbox_entry(InboxEntry(activity=activity))


@router.get("/actors/{username}/outbox")
async def actor_outbox(service: ActivityPubServiceInjection, username: str) -> dict:
    main_actor = service.get_main_actor()

    if username != main_actor.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": 0,
        "orderedItems": [],
    }
