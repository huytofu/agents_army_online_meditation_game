from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _statements(sql: str) -> list[str]:
    return [part.strip() for part in sql.split(";") if part.strip()]


async def apply_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        registered = await conn.scalar(text("SELECT to_regclass('public.schema_migrations')"))
        applied: set[str] = set()
        if registered is not None:
            rows = await conn.execute(text("SELECT filename FROM schema_migrations"))
            applied = {row[0] for row in rows}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            for statement in _statements(path.read_text()):
                await conn.execute(text(statement))
            await conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                {"filename": path.name},
            )
