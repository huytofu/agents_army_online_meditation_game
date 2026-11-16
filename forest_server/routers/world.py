from fastapi import APIRouter, HTTPException

from forest_server.database.repository import spot_by_id, spots_in_chunk
from forest_server.world.biomes import legal_chunk
from forest_server.world.catalog import world_meta
from forest_server.world.landmarks import landmarks_in_chunk
from forest_server.world.recipes import recipe_for_spot
from forest_server.world.scatter import scatter_for_chunk
from forest_server.world.water import water_in_chunk

router = APIRouter(prefix="/api/world")


@router.get("/meta")
async def meta() -> dict:
    return world_meta()


@router.get("/spots/{spot_id}/recipe")
async def recipe(spot_id: int) -> dict:
    spot = await spot_by_id(spot_id)
    if spot is None:
        raise HTTPException(status_code=404, detail="unknown spot")
    return recipe_for_spot(spot)


@router.get("/chunks/{cx}/{cz}")
async def chunk(cx: int, cz: int) -> dict:
    if not legal_chunk(cx, cz):
        raise HTTPException(status_code=404, detail="unknown chunk")
    return {
        "cx": cx,
        "cz": cz,
        "spots": await spots_in_chunk(cx, cz),
        "scatter": scatter_for_chunk(cx, cz),
        "landmarks": landmarks_in_chunk(cx, cz),
        "water": water_in_chunk(cx, cz),
    }
