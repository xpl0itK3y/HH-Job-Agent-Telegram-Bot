from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/ready", summary="Service readiness probe")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}
