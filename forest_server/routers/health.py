from fastapi import APIRouter
from sqlalchemy import text

from forest_server.database.connection import get_session

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, object]:
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
            spots = await session.scalar(text("SELECT COUNT(*) FROM spots"))
        return {"status": "ok", "db": "ok", "spots": int(spots or 0)}
    except Exception:
        return {"status": "degraded", "db": "down", "spots": 0}
