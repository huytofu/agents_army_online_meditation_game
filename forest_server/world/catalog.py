"""JSON the browser is allowed to know. No second forest lives in JavaScript source."""

from forest_server.world.biomes import (
    AIRY_KITS,
    BANDS,
    GORGE_KEEP,
    RIVER_CORRIDOR,
    RIVER_OFFSET,
    RIVER_SINES,
    RIVER_SLOPE,
    RIVER_WET,
)
from forest_server.world.constants import (
    CHUNK_SIZE,
    EXCLUSION_M,
    MAX_SPEED,
    SIT_RANGE_M,
    SPOT_SPACING,
    TERMS,
    WORLD_MAX,
    WORLD_MIN,
)
from forest_server.world.landmarks import LANDMARKS
from forest_server.world.scatter import SCATTER

PALETTES = {
    "moss_plain": {
        "fog": "#d5e2d2",
        "fog_density": 0.018,
        "sun": "#ffe0b0",
        "ground": "#6f8f62",
        "moss": "#3e6b45",
        "cap": "#c4554a",
        "stem": "#efe6d4",
    },
    "cathedral_trees": {
        "fog": "#9aa89a",
        "fog_density": 0.028,
        "sun": "#f3e2b8",
        "trunk": "#4a382c",
        "canopy": "#1d3328",
    },
    "river": {
        "fog": "#d5e4e2",
        "fog_density": 0.016,
        "sun": "#ffe0b0",
        "water": "#6e9aa3",
        "stone": "#8a8178",
        "reed": "#7ea15a",
    },
    "waterfall_gorge": {
        "fog": "#d0ddd8",
        "fog_density": 0.02,
        "sun": "#f4f0e4",
        "rock": "#6d7270",
        "sheet": "#c5ddd8",
        "mist": "#ffffff",
        "rainbow": "#f2c9ff",
    },
    "valley_bloom": {
        "fog": "#f3e4ef",
        "fog_density": 0.012,
        "sun": "#ffe0b0",
        "grass": "#8aaa62",
        "flowers": ["#d47aa6", "#e6c85a", "#7ec8e3"],
        "ridge": "#9aa7b0",
    },
    "strange_fauna": {
        "fog": "#6a6288",
        "fog_density": 0.03,
        "clear": "#2a2440",
        "sun": "#d7c4f2",
        "ground": "#3a3550",
        "spiral": "#6a4a78",
        "spore": "#d7f28a",
        "moth": "#f2c9ff",
    },
    "carnivorous_bog": {
        "fog": "#c8d2a4",
        "fog_density": 0.026,
        "clear": "#3e4630",
        "sun": "#e6d48a",
        "pitcher": "#6f8f3a",
        "throat": "#c4554a",
        "acid": "#d6e25a",
        "bone": "#efe6d4",
    },
    "lantern_orchard": {
        "fog": "#f7e2b0",
        "fog_density": 0.014,
        "sun": "#ffe0b0",
        "blossom": ["#e25b8a", "#f2c14e"],
        "glass": ["#7ee0c8", "#f2a3c7"],
        "lamp": "#d7f28a",
    },
    "fern_sea": {
        "fog": "#d5e6cf",
        "fog_density": 0.02,
        "sun": "#ffe8c4",
        "fern": "#3e6b45",
        "staghorn": "#7ea15a",
    },
    "hanging_vines": {
        "fog": "#d7e4c8",
        "fog_density": 0.022,
        "sun": "#ffe0b0",
        "vine": "#3e6b45",
        "epiphyte": "#c4554a",
        "eye": "#f2c9ff",
    },
    "amber_herd": {
        "fog": "#f0ddb8",
        "fog_density": 0.014,
        "sun": "#ffd39a",
        "hide": "#c47a3a",
        "seed": "#e6c85a",
        "bird": "#e25b4a",
    },
    "salt_mirror": {
        "fog": "#f4efe6",
        "fog_density": 0.01,
        "clear": "#efe8dc",
        "sun": "#fff6e8",
        "crust": "#efe6d4",
        "crystal": "#d7f0ff",
        "pool": "#e7a0b4",
    },
}


def kit_names() -> list[str]:
    names = {"seat_cushion"}
    for specs in SCATTER.values():
        for kit, _count, _scale in specs:
            names.add(kit)
    for landmark in LANDMARKS:
        for block in landmark["blocks"]:
            names.add(block["kit"])
    return sorted(names)


def world_meta() -> dict:
    bands = []
    for z_min, z_max, z_closed, columns in BANDS:
        bands.append(
            {
                "z_min": z_min,
                "z_max": z_max,
                "z_max_inclusive": z_closed,
                "columns": [
                    {
                        "x_min": x_min,
                        "x_max": x_max,
                        "x_max_inclusive": x_closed,
                        "name": name,
                    }
                    for x_min, x_max, x_closed, name in columns
                ],
            }
        )
    return {
        "world_min": WORLD_MIN,
        "world_max": WORLD_MAX,
        "chunk_size": CHUNK_SIZE,
        "spot_spacing": SPOT_SPACING,
        "exclusion_m": EXCLUSION_M,
        "sit_range_m": SIT_RANGE_M,
        "max_speed": MAX_SPEED,
        "spawn": [-24.0, 0.0],
        "walk_limit": 1996.0,
        "terms": [list(term) for term in TERMS],
        "bands": bands,
        "river": {
            "slope": RIVER_SLOPE,
            "offset": RIVER_OFFSET,
            "sines": [list(pair) for pair in RIVER_SINES],
            "corridor": RIVER_CORRIDOR,
            "wet": RIVER_WET,
            "gorge_keep": GORGE_KEEP,
        },
        "kits": kit_names(),
        "airy_kits": list(AIRY_KITS),
        "palettes": PALETTES,
    }
