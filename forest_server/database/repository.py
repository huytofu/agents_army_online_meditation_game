"""Spot rows for this game's Postgres. Scatter is not stored."""

from sqlalchemy import text

from forest_server.database.connection import get_session
from forest_server.world.spots import generate_spots

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
    async with get_session() as session:
        existing = int(await session.scalar(text("SELECT COUNT(*) FROM spots")) or 0)
        if existing:
            return existing
        rows = [spot.as_row() for spot in generate_spots()]
        await session.execute(INSERT_SPOTS, rows)
        await session.commit()
        return len(rows)


async def spots_in_chunk(cx: int, cz: int) -> list[dict]:
    async with get_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, biome, archetype, x, y, z, yaw, chunk_x, chunk_z
                FROM spots
                WHERE chunk_x = :cx AND chunk_z = :cz
                ORDER BY id
                """
            ),
            {"cx": cx, "cz": cz},
        )
        return [dict(row) for row in result.mappings()]
