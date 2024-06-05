from fastapi import APIRouter, status

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
    return {}


@router.post("/inbox", status_code=status.HTTP_202_ACCEPTED)
async def inbox() -> None:
    pass
