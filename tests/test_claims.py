import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from sqlalchemy import text

from forest_server.app import app
from forest_server.database.connection import get_session
from forest_server.database.repository import claim_spot, create_session, release_claim_for_session

pytestmark = pytest.mark.asyncio


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_one_of_two_concurrent_claims_wins():
    async with app.router.lifespan_context(app):
        async with get_session() as session:
            await session.execute(text("DELETE FROM spot_claims WHERE spot_id = 1"))
            await session.commit()
        first = await create_session(None)
        second = await create_session(None)
        try:
            results = await asyncio.gather(
                claim_spot(1, first["session_id"]),
                claim_spot(1, second["session_id"]),
            )
            assert sorted(results) == [False, True]
        finally:
            await release_claim_for_session(first["session_id"])
            await release_claim_for_session(second["session_id"])


async def test_sit_rejects_distance_and_keeps_a_private_video():
    async with app.router.lifespan_context(app):
        async with await _client() as client:
            opened = await client.post("/api/session", json={"token": None})
            assert opened.status_code == 200
            body = opened.json()
            token = body["token"]
            pose = await client.post(
                "/api/pose",
                json={"token": token, "x": 3.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0},
            )
            assert pose.json()["ok"] is True
            refused = await client.post("/api/sit", json={"token": token, "spot_id": 1})
            assert refused.json() == {"ok": False, "reason": "too_far"}
            bad = await client.post("/api/session/youtube", json={"token": token, "video_id": "not a video"})
            assert bad.json() == {"ok": False, "reason": "bad_video"}
            stored = await client.post(
                "/api/session/youtube",
                json={"token": token, "video_id": "dQw4w9WgXcQ"},
            )
            assert stored.json()["ok"] is True
            resumed = await client.post("/api/session", json={"token": token})
            assert resumed.json()["youtube_video_id"] == "dQw4w9WgXcQ"
            other = await client.post("/api/session", json={"token": None})
            assert other.json()["youtube_video_id"] is None
