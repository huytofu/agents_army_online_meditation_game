"""Biome rectangles and the river corridor. Layout authority for phase 2."""

import math

from forest_server.world.constants import CHUNK_SIZE, WORLD_MAX, WORLD_MIN

RIVER_SLOPE = 0.55
RIVER_OFFSET = 280.0
RIVER_SINES = ((60.0, 0.0018), (22.0, 0.006))
RIVER_CORRIDOR = 55.0
RIVER_WET = 16.0
GORGE_KEEP = 90.0

# (z_min, z_max, z_max_inclusive, columns of (x_min, x_max, x_max_inclusive, name))
BANDS = (
    (
        -2000.0,
        -1100.0,
        False,
        (
            (-2000.0, 200.0, False, "strange_fauna"),
            (200.0, 1400.0, False, "cathedral_trees"),
            (1400.0, 2000.0, True, "salt_mirror"),
        ),
    ),
    (
        -1100.0,
        -200.0,
        False,
        (
            (-2000.0, -200.0, False, "fern_sea"),
            (-200.0, 1100.0, False, "carnivorous_bog"),
            (1100.0, 2000.0, True, "amber_herd"),
        ),
    ),
    (
        -200.0,
        800.0,
        False,
        (
            (-2000.0, 400.0, False, "moss_plain"),
            (400.0, 2000.0, True, "lantern_orchard"),
        ),
    ),
    (
        800.0,
        2000.0,
        True,
        (
            (-2000.0, -400.0, False, "valley_bloom"),
            (-400.0, 800.0, False, "hanging_vines"),
            (800.0, 2000.0, True, "waterfall_gorge"),
        ),
    ),
)

ARCHETYPES = {
    "moss_plain": ("dew_clearing", "mushroom_ring", "log_seat", "mound_overlook"),
    "cathedral_trees": ("between_roots", "shaft_clearing", "hollow", "vine_nave"),
    "river": ("bank_stone", "reed_pocket", "shallow_bend", "boulder_island_view"),
    "waterfall_gorge": ("pool_ledge", "mist_shelf", "behind_sheet", "gorge_floor"),
    "valley_bloom": ("terrace_lip", "flower_bowl", "ridge_seat", "amphitheater"),
    "strange_fauna": ("spore_circle", "spiral_cathedral", "moth_lane", "violet_hollow"),
    "carnivorous_bog": ("pitcher_ring", "sundew_jewel", "maw_clearing", "acid_cup_seat"),
    "lantern_orchard": ("glow_fruit", "glass_aisle", "moth_orchard", "lantern_root"),
    "fern_sea": ("fiddle_bowl", "staghorn_nave", "fern_tunnel", "curl_overlook"),
    "hanging_vines": ("root_swing", "epiphyte_balcony", "loris_perch", "curtain_gap"),
    "amber_herd": ("grazer_shade", "seed_ring", "dust_bowl", "bird_perch"),
    "salt_mirror": ("crust_lip", "pink_pool", "crystal_seat", "brine_hollow"),
}

AIRY_KITS = (
    "mist_card",
    "spore",
    "glow_moth",
    "waterfall_sheet",
    "vine_strand",
    "dragonfly",
    "kite_bird",
    "brine_skipper",
    "rainbow_card",
    "glass_leaf",
    "beetle_lamp",
)

CARNIVOROUS_KITS = ("pitcher", "sundew", "snap_maw", "vine_noose", "acid_cup")


def river_z(x: float) -> float:
    return (
        RIVER_SLOPE * x
        + RIVER_OFFSET
        + sum(amp * math.sin(x * freq) for amp, freq in RIVER_SINES)
    )


def _in_range(value: float, low: float, high: float, high_inclusive: bool) -> bool:
    if value < low:
        return False
    if high_inclusive:
        return value <= high
    return value < high


def rectangle_biome(x: float, z: float) -> str | None:
    for z_min, z_max, z_closed, columns in BANDS:
        if not _in_range(z, z_min, z_max, z_closed):
            continue
        for x_min, x_max, x_closed, name in columns:
            if _in_range(x, x_min, x_max, x_closed):
                return name
    return None


def biome_at(x: float, z: float) -> str | None:
    base = rectangle_biome(x, z)
    if base is None:
        return None
    distance = abs(z - river_z(x))
    if base == "waterfall_gorge" and distance <= GORGE_KEEP:
        return "waterfall_gorge"
    if distance < RIVER_CORRIDOR:
        return "river"
    return base


def chunk_index(value: float) -> int:
    return math.floor((value - WORLD_MIN) / CHUNK_SIZE)


def chunk_origin(index: int) -> float:
    return WORLD_MIN + index * CHUNK_SIZE


def legal_chunk(cx: int, cz: int) -> bool:
    limit = int(math.floor((WORLD_MAX - WORLD_MIN) / CHUNK_SIZE))
    # 4000 / 64 = 62.5, so indexes 0..62 inclusive.
    return 0 <= cx <= limit and 0 <= cz <= limit
