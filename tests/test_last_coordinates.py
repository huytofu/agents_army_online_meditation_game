"""Last coordinates are saved on logout and chosen at the next login."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from forest_server.app import app
from forest_server.database.connection import get_session
from forest_server.world.ground import ground_height

pytestmark = pytest.mark.asyncio

SPAWN = (-24.0, 0.0)


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_logout_stores_coordinates_for_that_session_only():
    async with app.router.lifespan_context(app):
        async with await _client() as client:
            opened = await client.post("/api/session", json={"token": None})
            assert opened.status_code == 200
            body = opened.json()
            token = body["token"]
            assert body["saved_coordinates"] is None

            other = await client.post("/api/session", json={"token": None})
            other_token = other.json()["token"]

            saved = await client.post(
                "/api/logout",
                json={"token": token, "x": 40.0, "y": 1.25, "z": -12.5, "yaw": 0.4, "pitch": -0.2},
            )
            assert saved.status_code == 200
            assert saved.json()["ok"] is True

            again = await client.post("/api/logout", json={
                "token": token, "x": 88.0, "y": 2.0, "z": 15.0, "yaw": 1.2, "pitch": 0.1,
            })
            assert again.json()["ok"] is True

            resumed = await client.post("/api/session", json={"token": token})
            coordinates = resumed.json()["saved_coordinates"]
            assert coordinates["x"] == pytest.approx(88.0)
            assert coordinates["y"] == pytest.approx(2.0)
            assert coordinates["z"] == pytest.approx(15.0)
            assert coordinates["yaw"] == pytest.approx(1.2)
            assert coordinates["pitch"] == pytest.approx(0.1)

            stranger = await client.post("/api/session", json={"token": other_token})
            assert stranger.json()["saved_coordinates"] is None


async def test_resume_restores_saved_coordinates_and_keeps_them():
    async with app.router.lifespan_context(app):
        async with await _client() as client:
            opened = await client.post("/api/session", json={"token": None})
            token = opened.json()["token"]
            await client.post(
                "/api/logout",
                json={"token": token, "x": 40.0, "y": 1.25, "z": -12.5, "yaw": 0.4, "pitch": -0.2},
            )
            resumed = await client.post("/api/session/start", json={"token": token, "choice": "resume"})
            assert resumed.status_code == 200
            pose = resumed.json()["pose"]
            assert resumed.json()["ok"] is True
            assert pose["x"] == pytest.approx(40.0)
            assert pose["z"] == pytest.approx(-12.5)
            assert pose["yaw"] == pytest.approx(0.4)
            assert pose["mode"] == "walk"
            assert pose["spot_id"] is None

            still = await client.post("/api/session", json={"token": token})
            assert still.json()["saved_coordinates"]["x"] == pytest.approx(40.0)
            assert still.json()["saved_coordinates"]["z"] == pytest.approx(-12.5)


async def test_spawn_choice_overwrites_saved_coordinates_with_the_default():
    async with app.router.lifespan_context(app):
        async with await _client() as client:
            opened = await client.post("/api/session", json={"token": None})
            token = opened.json()["token"]
            await client.post(
                "/api/logout",
                json={"token": token, "x": 40.0, "y": 1.25, "z": -12.5, "yaw": 0.4, "pitch": -0.2},
            )
            started = await client.post("/api/session/start", json={"token": token, "choice": "spawn"})
            assert started.json()["ok"] is True
            pose = started.json()["pose"]
            spawn_x, spawn_z = SPAWN
            assert pose["x"] == pytest.approx(spawn_x)
            assert pose["y"] == pytest.approx(ground_height(spawn_x, spawn_z))
            assert pose["z"] == pytest.approx(spawn_z)
            assert pose["yaw"] == pytest.approx(0.0)
            assert pose["pitch"] == pytest.approx(0.0)
            assert pose["mode"] == "walk"

            stored = await client.post("/api/session", json={"token": token})
            coordinates = stored.json()["saved_coordinates"]
            assert coordinates["x"] == pytest.approx(spawn_x)
            assert coordinates["y"] == pytest.approx(ground_height(spawn_x, spawn_z))
            assert coordinates["z"] == pytest.approx(spawn_z)
            assert coordinates["yaw"] == pytest.approx(0.0)
            assert coordinates["pitch"] == pytest.approx(0.0)


async def test_logout_frees_a_claimed_seat():
    async with app.router.lifespan_context(app):
        async with get_session() as session:
            spot = (
                await session.execute(
                    text(
                        """
                        SELECT id, x, y, z
                        FROM spots
                        WHERE x > 100
                        ORDER BY id
                        LIMIT 1
                        """
                    )
                )
            ).mappings().one()
            await session.execute(
                text("DELETE FROM spot_claims WHERE spot_id = :spot_id"),
                {"spot_id": spot["id"]},
            )
            await session.commit()
        async with await _client() as client:
            opened = await client.post("/api/session", json={"token": None})
            token = opened.json()["token"]
            session_id = opened.json()["session_id"]
            moved = await client.post(
                "/api/pose",
                json={
                    "token": token,
                    "x": spot["x"],
                    "y": spot["y"],
                    "z": spot["z"],
                    "yaw": 0.0,
                    "pitch": 0.0,
                },
            )
            assert moved.json()["ok"] is True
            sat = await client.post("/api/sit", json={"token": token, "spot_id": spot["id"]})
            assert sat.json()["ok"] is True

            left = await client.post(
                "/api/logout",
                json={
                    "token": token,
                    "x": spot["x"],
                    "y": spot["y"],
                    "z": spot["z"],
                    "yaw": 1.0,
                    "pitch": 0.0,
                },
            )
            assert left.json()["ok"] is True

            async with get_session() as session:
                claims = await session.scalar(
                    text("SELECT COUNT(*) FROM spot_claims WHERE session_id = :session_id"),
                    {"session_id": session_id},
                )
            assert int(claims or 0) == 0
            resumed = await client.post("/api/session", json={"token": token})
            assert resumed.json()["pose"]["mode"] == "walk"
            assert resumed.json()["saved_coordinates"]["x"] == pytest.approx(float(spot["x"]))
