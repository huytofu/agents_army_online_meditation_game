import math
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from forest_server.app import app
from forest_server.world.biomes import AIRY_KITS, ARCHETYPES
from forest_server.world.catalog import kit_names
from forest_server.world.recipes import recipe_for_spot


def _spot(spot_id: int, biome: str, archetype: str) -> SimpleNamespace:
    return SimpleNamespace(id=spot_id, biome=biome, archetype=archetype, yaw=0.4)


def _solid_clear(block: dict) -> bool:
    if block["kit"] in AIRY_KITS:
        return True
    distance = math.hypot(block["x"], block["z"])
    if distance < 0.8:
        return False
    return not (abs(math.atan2(block["x"], block["z"])) < 0.35 and distance < 4)


def test_every_archetype_builds_a_stable_legal_scene():
    known = set(kit_names())
    for biome, names in ARCHETYPES.items():
        for archetype in names:
            spot = _spot(archetype.__len__() + len(biome), biome, archetype)
            first = recipe_for_spot(spot)
            second = recipe_for_spot(spot)
            assert first == second
            assert first["spot_id"] == spot.id
            assert first["biome"] == biome
            assert first["archetype"] == archetype
            assert first["yaw"] == spot.yaw
            assert len(first["blocks"]) >= 8
            for block in first["blocks"]:
                assert block["kit"] in known
                assert block["space"] == "local"
                if archetype != "behind_sheet":
                    assert _solid_clear(block)


@pytest.mark.asyncio
async def test_recipe_route_returns_one_spot_and_hides_the_rest():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            found = await client.get("/api/world/spots/1/recipe")
            missing = await client.get("/api/world/spots/999999/recipe")
    assert found.status_code == 200
    assert found.json()["spot_id"] == 1
    assert missing.status_code == 404


def test_pool_ledge_keeps_a_full_waterfall():
    spot = _spot(7, "waterfall_gorge", "pool_ledge")
    sheets = [block for block in recipe_for_spot(spot)["blocks"] if block["kit"] == "waterfall_sheet"]
    assert sheets
    assert max(block["scale"] for block in sheets) >= 8
