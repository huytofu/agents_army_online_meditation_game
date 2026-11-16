"""Spot rows and the one local session. Scatter is not stored."""

import hashlib
import json
import math
import secrets
import uuid

from sqlalchemy import text

from forest_server.database.connection import get_session
from forest_server.world.ground import ground_height
from forest_server.world.spots import generate_spots

SPAWN = (-24.0, 0.0)

INSERT_SPOTS = text(
    """
    INSERT INTO spots (id, biome, archetype, x, y, z, yaw, chunk_x, chunk_z)
    VALUES (:id, :biome, :archetype, :x, :y, :z, :yaw, :chunk_x, :chunk_z)
    """
)


async def spot_count() -> int:
    async with get_session() as session:
        value = await session.scalar(text("SELECT COUNT(*) FROM spots"))
    return int(value or 0)


async def seed_spots_if_empty() -> int:
    spots = generate_spots()
    rows = [spot.as_row() for spot in spots]
    first = rows[0]
    async with get_session() as session:
        existing = int(await session.scalar(text("SELECT COUNT(*) FROM spots")) or 0)
        if existing == len(rows):
            current = (
                await session.execute(text("SELECT x, z FROM spots WHERE id = 1"))
            ).one()
            if float(current.x) == first["x"] and float(current.z) == first["z"]:
                return existing
        await session.execute(text("DELETE FROM spot_claims"))
        await session.execute(text("DELETE FROM spots"))
        await session.execute(INSERT_SPOTS, rows)
        await session.execute(
            text(
                """
                UPDATE sessions
                SET pose = pose || '{"mode": "walk", "spot_id": null}'::jsonb
                WHERE pose->>'mode' = 'sit'
                """
            )
        )
        await session.commit()
        return len(rows)


async def spots_in_chunk(cx: int, cz: int) -> list[dict]:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                SELECT s.id, s.biome, s.archetype, s.x, s.y, s.z, s.yaw, s.chunk_x, s.chunk_z,
                       (c.spot_id IS NOT NULL) AS claimed
                FROM spots s
                LEFT JOIN spot_claims c ON c.spot_id = s.id
                WHERE s.chunk_x = :cx AND s.chunk_z = :cz
                ORDER BY s.id
                """
            ),
            {"cx": cx, "cz": cz},
        )
        return [dict(row) for row in result.mappings()]


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_color(session_id: uuid.UUID) -> str:
    hue = (int(session_id.hex[:4], 16) % 90) + 25
    return _hsl_hex(hue, 0.28, 0.42)


def _spawn_pose() -> dict:
    x, z = SPAWN
    return {
        "x": x,
        "y": ground_height(x, z),
        "z": z,
        "yaw": 0.0,
        "pitch": 0.0,
        "mode": "walk",
        "spot_id": None,
    }


def _hsl_hex(hue: float, saturation: float, lightness: float) -> str:
    chroma = (1 - abs(2 * lightness - 1)) * saturation
    sector = (hue % 360) / 60
    match = chroma * (1 - abs(sector % 2 - 1))
    if sector < 1:
        red, green, blue = chroma, match, 0.0
    elif sector < 2:
        red, green, blue = match, chroma, 0.0
    elif sector < 3:
        red, green, blue = 0.0, chroma, match
    elif sector < 4:
        red, green, blue = 0.0, match, chroma
    elif sector < 5:
        red, green, blue = match, 0.0, chroma
    else:
        red, green, blue = chroma, 0.0, match
    shift = lightness - chroma / 2

    def channel(value: float) -> int:
        return max(0, min(255, round((value + shift) * 255)))

    return f"#{channel(red):02x}{channel(green):02x}{channel(blue):02x}"


def _pose(value) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _public(row, token: str | None = None) -> dict:
    payload = {
        "session_id": str(row["id"]),
        "color": row["color"],
        "pose": _pose(row["pose"]),
        "youtube_video_id": row["youtube_video_id"],
    }
    if token is not None:
        payload["token"] = token
    return payload


async def session_by_token_hash(token_hash: str) -> dict | None:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, color, pose, youtube_video_id
                FROM sessions
                WHERE token_hash = :token_hash
                """
            ),
            {"token_hash": token_hash},
        )
        row = result.mappings().first()
    if row is None:
        return None
    return _public(row)


async def create_session(token: str | None) -> dict:
    if token:
        existing = await session_by_token_hash(hash_token(token))
        if existing:
            existing["token"] = token
            return existing
    raw = secrets.token_urlsafe(32)
    session_id = uuid.uuid4()
    pose = _spawn_pose()
    async with get_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO sessions (id, token_hash, color, pose)
                VALUES (:id, :token_hash, :color, CAST(:pose AS jsonb))
                """
            ),
            {
                "id": session_id,
                "token_hash": hash_token(raw),
                "color": session_color(session_id),
                "pose": json.dumps(pose),
            },
        )
        await session.commit()
    return {
        "token": raw,
        "session_id": str(session_id),
        "color": session_color(session_id),
        "pose": pose,
        "youtube_video_id": None,
    }


async def update_pose(session_id: str, pose: dict) -> dict | None:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                UPDATE sessions
                SET pose = CAST(:pose AS jsonb), last_seen_at = now()
                WHERE id = :id AND pose->>'mode' = 'walk'
                RETURNING id, color, pose, youtube_video_id
                """
            ),
            {"id": session_id, "pose": json.dumps(pose)},
        )
        row = result.mappings().first()
        if row is None:
            result = await session.execute(
                text("SELECT id, color, pose, youtube_video_id FROM sessions WHERE id = :id"),
                {"id": session_id},
            )
            row = result.mappings().first()
            await session.commit()
            if row is None:
                return None
            return _public(row)
        await session.commit()
    return _public(row)


async def force_pose(session_id: str, pose: dict) -> None:
    async with get_session() as session:
        await session.execute(
            text(
                """
                UPDATE sessions
                SET pose = CAST(:pose AS jsonb), last_seen_at = now()
                WHERE id = :id
                """
            ),
            {"id": session_id, "pose": json.dumps(pose)},
        )
        await session.commit()


async def set_youtube(session_id: str, video_id: str | None) -> None:
    async with get_session() as session:
        await session.execute(
            text(
                """
                UPDATE sessions
                SET youtube_video_id = :video_id, last_seen_at = now()
                WHERE id = :id
                """
            ),
            {"id": session_id, "video_id": video_id},
        )
        await session.commit()


async def claim_spot(spot_id: int, session_id: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                INSERT INTO spot_claims (spot_id, session_id)
                VALUES (:spot_id, :session_id)
                ON CONFLICT (spot_id) DO NOTHING
                RETURNING spot_id
                """
            ),
            {"spot_id": spot_id, "session_id": session_id},
        )
        won = result.first() is not None
        await session.commit()
    return won


async def release_claim_for_session(session_id: str) -> None:
    async with get_session() as session:
        await session.execute(
            text("DELETE FROM spot_claims WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
        await session.commit()


async def pose_conflicts(x: float, z: float, session_id: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                SELECT pose
                FROM sessions
                WHERE id <> :session_id
                  AND last_seen_at > now() - interval '15 seconds'
                """
            ),
            {"session_id": session_id},
        )
        rows = result.scalars().all()
    for raw in rows:
        pose = _pose(raw)
        if math.hypot(float(pose["x"]) - x, float(pose["z"]) - z) < 5:
            return True
    return False


async def spot_by_id(spot_id: int) -> dict | None:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, biome, archetype, x, y, z, yaw, chunk_x, chunk_z
                FROM spots
                WHERE id = :id
                """
            ),
            {"id": spot_id},
        )
        row = result.mappings().first()
    return dict(row) if row else None


async def session_by_token(token: str) -> dict | None:
    found = await session_by_token_hash(hash_token(token))
    if found is None:
        return None
    found["token"] = token
    return found
