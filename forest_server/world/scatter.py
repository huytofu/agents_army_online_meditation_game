"""Chunk scatter. Counts are attempted, then dropped when the biome does not match."""

import math

from forest_server.world.biomes import biome_at, chunk_origin
from forest_server.world.constants import CHUNK_SIZE, WORLD_MAX, WORLD_MIN, WORLD_SEED
from forest_server.world.ground import ground_height
from forest_server.world.rng import mulberry32

# kit, count, scale (float or (lo, hi))
SCATTER = {
    "moss_plain": (
        ("tree", 3, (0.5, 0.8)),
        ("moss_mound", 28, 1.0),
        ("fern", 18, 1.0),
        ("mushroom", 14, 1.0),
        ("dead_log", 6, 1.0),
        ("cushion_moss", 10, 1.0),
        ("flower_pink", 8, 1.0),
        ("flower_white", 6, 1.0),
        ("mushroom_brown", 6, 1.0),
        ("grass_patch", 10, 1.0),
        ("dirt_patch", 5, 1.0),
        ("fallen_leaves", 8, 1.0),
        ("rabbit", 3, 1.0),
        ("worm", 4, 1.0),
        ("songbird", 2, 1.0),
        ("butterfly", 4, 1.0),
        ("tree_tall", 1, 1.0),
        ("tree_branched", 2, 1.0),
        ("tree_broad", 1, 1.0),
    ),
    "cathedral_trees": (
        ("tree", 10, (1.6, 2.4)),
        ("fern", 12, 1.0),
        ("vine_strand", 8, 1.0),
        ("boulder", 4, 1.0),
        ("fallen_leaves", 8, 1.0),
        ("mushroom_brown", 4, 1.0),
        ("tree_dead", 3, 1.0),
        ("tree_tall", 2, (1.4, 1.8)),
        ("songbird", 1, 1.0),
    ),
    "river": (
        ("reed", 22, 1.0),
        ("river_stone", 16, 1.0),
        ("lily_pad", 8, 1.0),
        ("dragonfly", 4, 1.0),
        ("heron", 1, 1.0),
        ("water_puddle", 6, 1.0),
    ),
    "waterfall_gorge": (
        ("cliff_wall", 14, 1.0),
        ("boulder", 8, 1.0),
        ("mist_card", 10, 1.0),
        ("rainbow_card", 3, 1.0),
    ),
    "valley_bloom": (
        ("wildflower", 36, 1.0),
        ("blossom_tree", 6, 1.0),
        ("seed_head", 8, 1.0),
        ("kite_bird", 3, 1.0),
        ("moss_mound", 6, 1.0),
        ("flower_blue", 8, 1.0),
        ("flower_gold", 8, 1.0),
        ("grass_patch", 6, 1.0),
        ("rabbit", 2, 1.0),
        ("butterfly", 5, 1.0),
        ("songbird", 2, 1.0),
        ("tree_yellow", 3, 1.0),
    ),
    "carnivorous_bog": (
        ("pitcher", 16, 1.0),
        ("sundew", 18, 1.0),
        ("snap_maw", 8, 1.0),
        ("vine_noose", 6, 1.0),
        ("acid_cup", 6, 1.0),
        ("bone_rib", 4, 1.0),
        ("mud_patch", 8, 1.0),
    ),
    "strange_fauna": (
        ("spiral_tree", 8, 1.0),
        ("spore", 20, 1.0),
        ("glow_moth", 8, 1.0),
        ("lantern_frog", 6, 1.0),
        ("beetle_lamp", 6, 1.0),
        ("mushroom_white", 6, 1.0),
    ),
    "lantern_orchard": (
        ("blossom_tree", 8, 1.0),
        ("glass_leaf", 16, 1.0),
        ("beetle_lamp", 8, 1.0),
        ("glow_moth", 10, 1.0),
        ("seed_head", 6, 1.0),
        ("butterfly", 6, 1.0),
        ("flower_gold", 4, 1.0),
    ),
    "fern_sea": (
        ("fern", 40, 1.0),
        ("fiddlehead", 16, 1.0),
        ("staghorn", 10, 1.0),
        ("tree", 2, 0.6),
        ("flower_pink", 6, 1.0),
        ("mushroom_gold", 5, 1.0),
        ("fallen_leaves", 6, 1.0),
        ("rabbit", 2, 1.0),
        ("tree_branched", 2, 1.0),
    ),
    "hanging_vines": (
        ("vine_strand", 18, 1.0),
        ("epiphyte", 14, 1.0),
        ("blossom_tree", 4, 1.0),
        ("loris", 5, 1.0),
        ("cliff_wall", 4, 1.0),
        ("monkey", 4, 1.0),
    ),
    "amber_herd": (
        ("seed_head", 16, 1.0),
        ("grazer", 5, 1.0),
        ("kite_bird", 4, 1.0),
        ("wildflower", 10, 1.0),
        ("boulder", 4, 1.0),
        ("grass_patch", 6, 1.0),
        ("dirt_patch", 4, 1.0),
        ("rabbit", 2, 1.0),
        ("worm", 3, 1.0),
        ("songbird", 2, 1.0),
        ("tree_yellow", 2, 1.0),
    ),
    "salt_mirror": (
        ("salt_crust", 16, 1.0),
        ("crystal_shard", 12, 1.0),
        ("pool_disc", 4, 1.0),
        ("brine_skipper", 10, 1.0),
        ("bone_rib", 3, 1.0),
    ),
}

HANGING = {"vine_strand", "vine_noose", "epiphyte"}
FLOATING = {"songbird", "butterfly"}

MOTION = {
    "fern": ("sway", 0.07, 5.0),
    "reed": ("sway", 0.07, 5.0),
    "fiddlehead": ("sway", 0.07, 5.0),
    "staghorn": ("sway", 0.07, 5.0),
    "vine_strand": ("sway", 0.07, 5.0),
    "seed_head": ("sway", 0.07, 5.0),
    "wildflower": ("sway", 0.07, 5.0),
    "epiphyte": ("sway", 0.07, 5.0),
    "glow_moth": ("path_circle", 1.4, 12.0),
    "dragonfly": ("drift", 0.8, 6.0),
    "kite_bird": ("drift", 1.2, 9.0),
    "lantern_frog": ("hop", 0.35, 6.0),
    "brine_skipper": ("hop", 0.35, 6.0),
    "grazer": ("bob", 0.08, 4.0),
    "heron": ("sway", 0.04, 7.0),
    "loris": ("bob", 0.12, 5.0),
    "snap_maw": ("sway", 0.15, 8.0),
    "waterfall_sheet": ("uv_scroll", 0.2, 4.0),
    "rainbow_card": ("uv_scroll", 0.2, 4.0),
    "spore": ("bob", 0.25, 6.0),
    "glass_leaf": ("bob", 0.25, 6.0),
    "beetle_lamp": ("bob", 0.25, 6.0),
    "mist_card": ("bob", 0.25, 6.0),
    "pitcher": ("sway", 0.03, 9.0),
    "flower_pink": ("sway", 0.08, 4.5),
    "flower_blue": ("sway", 0.08, 5.0),
    "flower_gold": ("sway", 0.08, 4.2),
    "flower_white": ("sway", 0.06, 5.5),
    "rabbit": ("hop", 0.2, 3.5),
    "worm": ("bob", 0.04, 2.5),
    "monkey": ("bob", 0.12, 4.0),
    "songbird": ("drift", 1.4, 8.0),
    "butterfly": ("path_circle", 0.8, 6.0),
}


def chunk_seed(cx: int, cz: int) -> int:
    return (WORLD_SEED ^ (cx * 734287 + cz * 912367)) & 0xFFFFFFFF


def biomes_in_chunk(cx: int, cz: int) -> set[str]:
    x0 = chunk_origin(cx)
    z0 = chunk_origin(cz)
    found: set[str] = set()
    step = 8.0
    x = x0 + 0.5
    while x < x0 + CHUNK_SIZE:
        z = z0 + 0.5
        while z < z0 + CHUNK_SIZE:
            name = biome_at(x, z)
            if name:
                found.add(name)
            z += step
        x += step
    return found


def _block(kit: str, x: float, z: float, rot_y: float, scale: float, y_lift: float, variant: int) -> dict:
    motion, amount, period = MOTION.get(kit, ("none", 0.0, 1.0))
    return {
        "kit": kit,
        "variant": variant,
        "x": x,
        "y": ground_height(x, z) + y_lift,
        "z": z,
        "rot_y": rot_y,
        "scale": scale,
        "motion": motion,
        "motion_period": period,
        "motion_amount": amount,
        "space": "world",
    }


def scatter_for_chunk(cx: int, cz: int) -> list[dict]:
    rng = mulberry32(chunk_seed(cx, cz))
    x0 = chunk_origin(cx)
    z0 = chunk_origin(cz)
    present = biomes_in_chunk(cx, cz)
    blocks: list[dict] = []
    for biome, specs in SCATTER.items():
        if biome not in present:
            continue
        for kit, count, scale_spec in specs:
            for _ in range(count):
                for _attempt in range(40):
                    x = x0 + rng() * CHUNK_SIZE
                    z = z0 + rng() * CHUNK_SIZE
                    if not (WORLD_MIN < x < WORLD_MAX and WORLD_MIN < z < WORLD_MAX):
                        continue
                    if biome_at(x, z) != biome:
                        continue
                    if isinstance(scale_spec, tuple):
                        scale = scale_spec[0] + rng() * (scale_spec[1] - scale_spec[0])
                    else:
                        scale = float(scale_spec)
                    rot_y = rng() * math.tau
                    variant = int(rng() * 3) % 3
                    if kit in HANGING:
                        y_lift = 2.0 + rng() * 6.0
                    elif kit in FLOATING:
                        y_lift = 1.6 + rng() * 2.4
                    else:
                        y_lift = 0.0
                    blocks.append(_block(kit, x, z, rot_y, scale, y_lift, variant))
                    break
    return blocks
