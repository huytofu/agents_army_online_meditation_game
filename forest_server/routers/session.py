"""One anonymous walker: pose, a single seat claim, and a private video id."""

import math
import re

from fastapi import APIRouter
from pydantic import BaseModel

from forest_server.database.repository import (
    claim_spot,
    create_session,
    force_pose,
    pose_conflicts,
    release_claim_for_session,
    session_by_token,
    set_youtube,
    spot_by_id,
    update_pose,
)

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


def _missing():
    return {"ok": False, "reason": "missing"}


@router.post("/session")
async def open_session(body: TokenBody) -> dict:
    return await create_session(body.token)


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
