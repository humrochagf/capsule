from fastapi import APIRouter, status

from capsule.__about__ import __version__
from capsule.settings import settings

router = APIRouter(tags=["activitypub"])


@router.get("/.well-known/nodeinfo")
async def well_known_nodeinfo() -> dict:
    return {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{settings.hostname}nodeinfo/2.0/",
            }
        ],
    }


@router.get("/nodeinfo")
async def nodeinfo() -> dict:
    return {
        "version": "2.0",
        "software": {
            "name": "capsule",
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
