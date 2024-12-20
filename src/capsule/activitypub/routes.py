from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from starlette.templating import Jinja2Templates

from capsule.__about__ import __version__
from capsule.activitypub.models.inbox import InboxEntryStatus
from capsule.security.exception import VerificationBadFormatError, VerificationError
from capsule.security.services import SignatureServiceInjection
from capsule.settings import CapsuleSettingsInjection

from .models import Activity, Actor, InboxEntry
from .service import ActivityPubServiceInjection

router = APIRouter(tags=["activitypub"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


class ActivityJSONResponse(JSONResponse):
    media_type = "application/activity+json"


class JRDJSONResponse(JSONResponse):
    media_type = "application/jrd+json"


@router.get("/.well-known/host-meta")
async def well_known_host_meta(
    settings: CapsuleSettingsInjection, request: Request
) -> Response:
    return templates.TemplateResponse(
        name="host-meta.xml",
        media_type="application/xrd+xml",
        request=request,
        context={
            "hostname": settings.hostname,
        },
    )


@router.get("/.well-known/nodeinfo")
async def well_known_nodeinfo(settings: CapsuleSettingsInjection) -> dict:
    return {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{settings.hostname}nodeinfo/2.0",
            }
        ],
    }


@router.get("/.well-known/webfinger", response_class=JRDJSONResponse)
async def well_known_webfinger(
    settings: CapsuleSettingsInjection,
    service: ActivityPubServiceInjection,
    resource: str = "",
) -> dict:
    acct = resource.removeprefix("acct:").split("@")

    match acct:
        case [settings.username, settings.hostname.host]:
            return service.get_webfinger()
        case [_, _]:
            raise HTTPException(HTTP_404_NOT_FOUND)
        case _:
            raise HTTPException(HTTP_400_BAD_REQUEST)


@router.get("/nodeinfo/2.0")
async def nodeinfo(
    settings: CapsuleSettingsInjection, service: ActivityPubServiceInjection
) -> dict:
    return {
        "version": "2.0",
        "software": {
            "name": settings.project_name.lower(),
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


@router.get("/@{username}", response_class=ActivityJSONResponse)
@router.get("/actors/{username}", response_class=ActivityJSONResponse)
async def actor(service: ActivityPubServiceInjection, username: str) -> Actor:
    main_actor = service.get_main_actor()

    if username != main_actor.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return main_actor


@router.get("/actors/{username}/icon")
async def actor_profile_picture(
    settings: CapsuleSettingsInjection,
    service: ActivityPubServiceInjection,
    username: str,
) -> FileResponse:
    main_actor = service.get_main_actor()

    if username != main_actor.username or settings.profile_image is None:
        raise HTTPException(HTTP_404_NOT_FOUND)

    return FileResponse(settings.profile_image)


@router.post("/actors/{username}/inbox", status_code=status.HTTP_202_ACCEPTED)
async def actor_inbox(
    activitypub: ActivityPubServiceInjection,
    signature: SignatureServiceInjection,
    background_tasks: BackgroundTasks,
    request: Request,
    username: str,
    activity: Activity,
) -> None:
    main_actor = activitypub.get_main_actor()

    if username != main_actor.username:
        raise HTTPException(HTTP_404_NOT_FOUND)

    actor = await activitypub.get_actor(activity.actor)

    if actor:
        try:
            await signature.verify_request(request, actor.public_key.public_key_pem)
        except VerificationBadFormatError as exc:
            raise HTTPException(HTTP_400_BAD_REQUEST) from exc
        except VerificationError as exc:
            raise HTTPException(HTTP_401_UNAUTHORIZED) from exc
    else:
        logger.bind(actor_id=activity.actor).info("New actor, skipping signature check")

    entry = await activitypub.create_inbox_entry(InboxEntry(activity=activity))

    background_tasks.add_task(activitypub.handle_activity, entry)


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


@router.post("/system/inbox/sync", status_code=status.HTTP_202_ACCEPTED)
async def system_inbox_sync(
    service: ActivityPubServiceInjection,
    status: InboxEntryStatus = InboxEntryStatus.created,
) -> None:
    await service.sync_inbox_entries(status)


@router.post("/system/inbox/cleanup", status_code=status.HTTP_202_ACCEPTED)
async def system_inbox_cleanup(service: ActivityPubServiceInjection) -> None:
    await service.cleanup_inbox_entries()
