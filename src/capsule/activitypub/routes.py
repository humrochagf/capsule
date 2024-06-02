from fastapi import APIRouter, status

router = APIRouter(prefix="/ap", tags=["activitypub"])


@router.post("/inbox", status_code=status.HTTP_202_ACCEPTED)
async def inbox() -> None:
    pass
