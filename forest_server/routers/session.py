"""One anonymous walker: pose, a single seat claim, and a private video id."""

import math
import re
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from forest_server.database.repository import (
    apply_start_choice,
    claim_spot,
    create_session,
    force_pose,
    pose_conflicts,
    release_claim_for_session,
    save_logout_coordinates,
    session_by_token,
    set_youtube,
    spot_by_id,
    update_pose,
)
from forest_server.youtube_search import search_with_server_key

router = APIRouter(prefix="/api")
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class TokenBody(BaseModel):
    token: str | None = None


class PoseBody(BaseModel):
    token: str
    x: float
    y: float
    z: float
    yaw: float
    pitch: float


class SitBody(BaseModel):
    token: str
    spot_id: int


class VideoBody(BaseModel):
    token: str
    video_id: str | None = None


class SearchBody(BaseModel):
    token: str
    q: str = ""


class LogoutBody(BaseModel):
    token: str
    x: float
    y: float
    z: float
    yaw: float
    pitch: float


class StartBody(BaseModel):
    token: str
    choice: Literal["resume", "spawn"]


WALK_LIMIT = 1996.0


def _missing():
    return {"ok": False, "reason": "missing"}


def _coordinates_in_forest(body: LogoutBody) -> bool:
    numbers = (body.x, body.y, body.z, body.yaw, body.pitch)
    if any(not math.isfinite(value) for value in numbers):
        return False
    return (
        -WALK_LIMIT <= body.x <= WALK_LIMIT
        and -WALK_LIMIT <= body.z <= WALK_LIMIT
        and -100.0 <= body.y <= 100.0
    )


@router.post("/session")
async def open_session(body: TokenBody) -> dict:
    return await create_session(body.token)


@router.post("/logout")
async def post_logout(body: LogoutBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    if not _coordinates_in_forest(body):
        return {"ok": False, "reason": "out_of_bounds"}
    await save_logout_coordinates(found["session_id"], body.x, body.y, body.z, body.yaw, body.pitch)
    return {"ok": True}


@router.post("/session/start")
async def post_start(body: StartBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    pose = await apply_start_choice(found["session_id"], body.choice)
    return {"ok": True, "pose": pose}


@router.post("/pose")
async def post_pose(body: PoseBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    pose = dict(found["pose"])
    if pose.get("mode") != "walk":
        return {"ok": True, "pose": pose}
    pose.update({"x": body.x, "y": body.y, "z": body.z, "yaw": body.yaw, "pitch": body.pitch})
    stored = await update_pose(found["session_id"], pose)
    if stored is None:
        return _missing()
    return {"ok": True, "pose": stored["pose"]}


@router.post("/sit")
async def post_sit(body: SitBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    spot = await spot_by_id(body.spot_id)
    if spot is None:
        return _missing()
    pose = found["pose"]
    if math.hypot(float(pose["x"]) - spot["x"], float(pose["z"]) - spot["z"]) > 2.5:
        return {"ok": False, "reason": "too_far"}
    if await pose_conflicts(spot["x"], spot["z"], found["session_id"]):
        return {"ok": False, "reason": "excluded"}
    if not await claim_spot(body.spot_id, found["session_id"]):
        return {"ok": False, "reason": "taken"}
    seated = {
        "x": spot["x"],
        "y": spot["y"],
        "z": spot["z"],
        "yaw": spot["yaw"],
        "pitch": pose.get("pitch", 0.0),
        "mode": "sit",
        "spot_id": spot["id"],
    }
    await force_pose(found["session_id"], seated)
    return {"ok": True, "pose": seated}


@router.post("/stand")
async def post_stand(body: TokenBody) -> dict:
    if not body.token:
        return _missing()
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    await release_claim_for_session(found["session_id"])
    pose = dict(found["pose"])
    pose["mode"] = "walk"
    pose["spot_id"] = None
    await force_pose(found["session_id"], pose)
    return {"ok": True, "pose": pose}


@router.post("/session/youtube")
async def post_youtube(body: VideoBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    if body.video_id is not None and VIDEO_ID.fullmatch(body.video_id) is None:
        return {"ok": False, "reason": "bad_video"}
    await set_youtube(found["session_id"], body.video_id)
    return {"ok": True, "youtube_video_id": body.video_id}


@router.post("/youtube/search")
async def post_youtube_search(body: SearchBody) -> dict:
    found = await session_by_token(body.token)
    if found is None:
        return _missing()
    return await search_with_server_key(body.q)
