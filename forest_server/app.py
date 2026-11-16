import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from forest_server.database.connection import close_database, init_database
from forest_server.routers.health import router as health_router
from forest_server.routers.session import router as session_router
from forest_server.routers.world import router as world_router

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await init_database()
    except Exception:
        log.exception("database init failed")
    yield
    await close_database()


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(session_router)
app.include_router(world_router)
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
