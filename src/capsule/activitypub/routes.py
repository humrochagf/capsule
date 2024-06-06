from fastapi import APIRouter, status

from capsule.__about__ import __version__
from capsule.settings import get_capsule_settings

router = APIRouter(tags=["activitypub"])


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
                "total": 0,
            },
            "localPosts": 0,
        },
        "openRegistrations": False,
        "metadata": {},
    }


@router.post("/inbox", status_code=status.HTTP_202_ACCEPTED)
async def inbox() -> None:
    pass
