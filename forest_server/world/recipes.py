"""Seated scenes. One spot id always rebuilds the same local blocks."""

import math

from forest_server.world.biomes import AIRY_KITS
from forest_server.world.rng import mulberry32

VARIANTS = {
    "mushroom": 2,
    "boulder": 2,
    "tree": 3,
    "spiral_tree": 2,
    "cliff_wall": 2,
}


def spot_seed(spot_id: int) -> int:
    return (20261105 + int(spot_id) * 1013904223) & 0xFFFFFFFF


def recipe_for_spot(spot) -> dict:
    spot_id = _field(spot, "id")
    biome = _field(spot, "biome")
    archetype = _field(spot, "archetype")
    yaw = _field(spot, "yaw")
    rng = mulberry32(spot_seed(spot_id))
    blocks = _layout(rng, archetype)
    if archetype != "behind_sheet":
        blocks = [block for block in blocks if _legal(block)]
    guard = 0
    while len(blocks) < 8 and guard < 6:
        guard += 1
        extra = [
            block
            for block in arc(rng, "fern", 4, 6.5, math.pi, 2.0, 1.0, 0.0, "sway", 0.07, 5.0)
            if _legal(block)
        ]
        if not extra:
            break
        blocks.extend(extra)
    return {
        "spot_id": spot_id,
        "biome": biome,
        "archetype": archetype,
        "yaw": yaw,
        "blocks": blocks,
    }


def arc(rng, kit, count, radius, center, spread, scale, y, motion, amount, period):
    blocks = []
    for index in range(count):
        if count == 1:
            angle = center
        else:
            angle = center - spread / 2 + spread * (index / (count - 1))
        angle += (rng() - 0.5) * 0.12
        used = radius * (0.92 + 0.16 * rng())
        variants = VARIANTS.get(kit, 1)
        variant = int(rng() * variants) % max(variants, 1)
        used_scale = scale * (0.85 + 0.3 * rng())
        blocks.append(
            _block(
                kit,
                math.sin(angle) * used,
                y,
                math.cos(angle) * used,
                angle,
                used_scale,
                variant,
                motion,
                amount,
                period,
            )
        )
    return blocks


def front(rng, kit, count, z, x_spread, scale, y, motion, amount, period):
    del rng
    blocks = []
    variants = VARIANTS.get(kit, 1)
    for index in range(count):
        if count == 1:
            x = 0.0
        else:
            x = -x_spread + (2 * x_spread) * (index / (count - 1))
        blocks.append(_block(kit, x, y, z, 0.0, scale, index % variants, motion, amount, period))
    return blocks


def _layout(rng, archetype: str) -> list[dict]:
    built: list[dict] = []
    for item in LAYOUTS.get(archetype, ()):
        kind, args = item[0], item[1:]
        if kind == "arc":
            built.extend(arc(rng, *args))
        else:
            built.extend(front(rng, *args))
    return built


def _block(kit, x, y, z, rot_y, scale, variant, motion, amount, period) -> dict:
    return {
        "kit": kit,
        "variant": variant,
        "x": x,
        "y": y,
        "z": z,
        "rot_y": rot_y,
        "scale": scale,
        "motion": motion,
        "motion_period": period,
        "motion_amount": amount,
        "space": "local",
    }


def _legal(block: dict) -> bool:
    if block["kit"] in AIRY_KITS:
        return True
    distance = math.hypot(block["x"], block["z"])
    if distance < 0.8:
        return False
    return not (abs(math.atan2(block["x"], block["z"])) < 0.35 and distance < 4)


def _field(spot, key: str):
    if isinstance(spot, dict):
        return spot[key]
    return getattr(spot, key)


def _none():
    return ("none", 0.0, 1.0)


N = _none()

LAYOUTS = {
    "dew_clearing": (
        ("arc", "mushroom", 9, 3.0, math.pi, 2.4, 0.8, 0.0, *N),
        ("arc", "fern", 12, 5.5, math.pi, 2.8, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "moss_mound", 6, 8.0, 0.0, 3.0, 1.3, 0.0, *N),
        ("front", "dead_log", 1, 3.2, 1.4, 1.1, 0.0, *N),
    ),
    "mushroom_ring": (
        ("arc", "mushroom", 14, 3.2, math.pi, 5.0, 1.0, 0.0, *N),
        ("arc", "fern", 8, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "mushroom", 2, 4.6, 2.0, 1.0, 0.0, *N),
    ),
    "log_seat": (
        ("front", "dead_log", 2, 2.4, 1.6, 1.2, 0.0, *N),
        ("front", "fern", 2, 4.6, 1.8, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "fern", 10, 6.0, math.pi, 2.5, 1.0, 0.0, *N),
        ("arc", "moss_mound", 5, 8.0, math.pi, 2.0, 1.0, 0.0, *N),
    ),
    "mound_overlook": (
        ("front", "moss_mound", 2, 1.5, 2.2, 1.8, 0.0, *N),
        ("front", "fern", 2, 4.6, 1.8, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "tree", 4, 10.0, math.pi, 2.2, 0.6, 0.0, *N),
    ),
    "between_roots": (
        ("arc", "tree", 4, 6.0, math.pi, 2.6, 1.8, 0.0, *N),
        ("arc", "fern", 8, 3.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "fern", 2, 4.6, 1.8, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "shaft_clearing": (
        ("arc", "tree", 6, 9.0, math.pi, 4.5, 2.0, 0.0, *N),
        ("arc", "vine_strand", 8, 6.0, math.pi, 2.0, 1.0, 4.0, "sway", 0.1, 7.0),
        ("front", "vine_strand", 2, 3.5, 1.4, 1.0, 3.0, "sway", 0.1, 7.0),
    ),
    "hollow": (
        ("front", "tree", 1, 3.0, 2.2, 2.2, 0.0, *N),
        ("front", "fern", 2, 4.6, 1.8, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "vine_strand", 6, 4.0, math.pi, 2.0, 1.0, 3.0, *N),
        ("arc", "mushroom", 4, 3.0, math.pi, 1.5, 1.0, 0.0, *N),
    ),
    "vine_nave": (
        ("arc", "tree", 2, 6.0, math.atan2(3.5, 6.0), 0.5, 1.7, 0.0, *N),
        ("arc", "tree", 2, 10.0, math.atan2(-3.5, 10.0), 0.5, 1.7, 0.0, *N),
        ("arc", "vine_strand", 8, 3.5, math.pi, 2.0, 1.0, 4.0, *N),
    ),
    "bank_stone": (
        ("arc", "river_stone", 8, 4.0, 0.0, 1.4, 1.0, 0.0, *N),
        ("arc", "reed", 10, 4.5, math.pi / 2, 1.2, 1.0, 0.0, *N),
        ("front", "pool_disc", 1, 5.0, 0.0, 3.0, 0.0, *N),
    ),
    "reed_pocket": (
        ("arc", "reed", 16, 3.5, math.pi, 5.0, 1.0, 0.0, *N),
        ("arc", "river_stone", 5, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "reed", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "shallow_bend": (
        ("front", "pool_disc", 1, 4.0, 0.0, 4.0, 0.0, *N),
        ("arc", "river_stone", 6, 5.0, 0.8, 1.0, 1.0, 0.0, *N),
        ("arc", "reed", 8, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
    ),
    "boulder_island_view": (
        ("front", "boulder", 1, 4.0, 2.0, 1.8, 0.0, *N),
        ("arc", "reed", 8, 5.0, math.pi, 2.4, 1.0, 0.0, *N),
    ),
    "pool_ledge": (
        ("front", "pool_disc", 1, 4.0, 0.0, 3.0, 0.0, *N),
        ("front", "waterfall_sheet", 1, 7.0, 0.0, 8.0, 2.0, "uv_scroll", 0.25, 4.0),
        ("front", "cliff_wall", 2, 6.0, 4.0, 2.0, 0.0, *N),
        ("arc", "mist_card", 4, 5.0, math.pi, 1.5, 1.0, 0.0, "bob", 0.3, 6.0),
    ),
    "mist_shelf": (
        ("arc", "mist_card", 4, 3.0, 0.0, 1.0, 1.0, 0.0, "drift", 0.4, 8.0),
        ("front", "cliff_wall", 2, 5.0, 3.0, 1.2, 0.0, *N),
        ("front", "waterfall_sheet", 1, 6.0, 3.0, 6.0, 0.0, "uv_scroll", 0.2, 4.0),
    ),
    "behind_sheet": (
        ("front", "waterfall_sheet", 1, 2.2, 0.0, 8.0, 1.0, "uv_scroll", 0.25, 4.0),
        ("front", "pool_disc", 1, 1.0, 0.0, 2.0, 0.0, *N),
        ("front", "cliff_wall", 2, 3.0, 3.0, 2.0, 0.0, *N),
        ("arc", "mist_card", 4, 2.5, math.pi, 1.5, 1.0, 0.0, *N),
    ),
    "gorge_floor": (
        ("front", "cliff_wall", 1, 2.0, 2.4, 2.4, 0.0, *N),
        ("front", "cliff_wall", 1, 3.2, 2.4, 2.4, 0.0, *N),
        ("front", "cliff_wall", 1, 4.4, 2.4, 2.4, 0.0, *N),
        ("front", "cliff_wall", 1, 5.6, 2.4, 2.4, 0.0, *N),
        ("front", "cliff_wall", 1, 6.8, 2.4, 2.4, 0.0, *N),
        ("front", "cliff_wall", 1, 8.0, 2.4, 2.4, 0.0, *N),
        ("front", "waterfall_sheet", 1, 10.0, 0.0, 8.0, 3.0, "uv_scroll", 0.25, 4.0),
        ("arc", "mist_card", 4, 4.0, math.pi, 1.5, 1.0, 0.0, *N),
    ),
    "terrace_lip": (
        ("front", "ridge_card", 1, 12.0, 0.0, 2.0, 0.0, *N),
        ("front", "ridge_card", 1, 16.0, 0.0, 3.0, 0.0, *N),
        ("front", "ridge_card", 1, 20.0, 0.0, 4.0, 0.0, *N),
        ("arc", "wildflower", 10, 4.0, math.pi / 2, 1.0, 1.0, 0.0, *N),
        ("arc", "moss_mound", 4, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
    ),
    "flower_bowl": (
        ("arc", "wildflower", 18, 3.4, math.pi, 5.0, 1.0, 0.0, *N),
        ("front", "wildflower", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.08, 4.5),
    ),
    "ridge_seat": (
        ("front", "ridge_card", 4, -2.0, 3.0, 1.6, 0.0, *N),
        ("arc", "wildflower", 8, 5.0, 0.0, 1.2, 1.0, 0.0, *N),
    ),
    "amphitheater": (
        ("arc", "ridge_card", 5, 11.0, math.pi, 2.2, 3.0, 0.0, *N),
        ("arc", "wildflower", 12, 4.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "wildflower", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.08, 4.5),
    ),
    "spore_circle": (
        ("arc", "spore", 12, 3.0, math.pi, 2.4, 1.0, 0.0, "bob", 0.4, 5.0),
        ("arc", "spiral_tree", 5, 7.0, math.pi, 2.4, 1.0, 0.0, *N),
        ("arc", "glow_moth", 4, 2.0, 0.0, 1.2, 1.0, 0.0, "path_circle", 1.6, 14.0),
    ),
    "spiral_cathedral": (
        ("arc", "spiral_tree", 5, 6.0, math.pi, 2.4, 1.4, 0.0, *N),
        ("arc", "spore", 10, 3.5, math.pi, 2.0, 1.0, 0.0, "bob", 0.3, 6.0),
        ("front", "spore", 2, 3.2, 1.2, 1.0, 1.2, "bob", 0.3, 6.0),
    ),
    "moth_lane": (
        ("arc", "glow_moth", 6, 4.0, 0.0, 1.2, 1.0, 0.0, "drift", 0.5, 9.0),
        ("arc", "spiral_tree", 4, 7.0, math.pi / 2, 1.0, 1.0, 0.0, *N),
    ),
    "violet_hollow": (
        ("arc", "spore", 12, 4.0, math.pi, 2.4, 1.0, 0.0, "bob", 0.35, 5.0),
        ("front", "spiral_tree", 1, 4.0, 2.5, 1.0, 0.0, *N),
        ("front", "lantern_frog", 2, 3.0, 2.0, 1.0, 0.0, "hop", 0.35, 6.0),
    ),
    "pitcher_ring": (
        ("arc", "pitcher", 8, 5.0, math.pi, 2.2, 1.2, 0.0, *N),
        ("arc", "sundew", 8, 3.2, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "acid_cup", 4, 6.5, math.pi, 1.5, 1.0, 0.0, *N),
        ("front", "sundew", 2, 4.6, 1.8, 1.0, 0.0, *N),
    ),
    "sundew_jewel": (
        ("arc", "sundew", 10, 3.5, math.pi, 4.0, 1.0, 0.0, *N),
        ("arc", "crystal_shard", 6, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "bone_rib", 1, 5.0, 0.0, 1.0, 0.0, *N),
    ),
    "maw_clearing": (
        ("arc", "snap_maw", 6, 4.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "vine_noose", 6, 6.0, math.pi, 2.0, 1.0, 2.0, "sway", 0.1, 7.0),
        ("arc", "mud_patch", 4, 7.0, math.pi, 1.4, 1.0, 0.0, *N),
        ("front", "snap_maw", 2, 4.6, 1.8, 1.0, 0.0, "sway", 0.12, 6.0),
    ),
    "acid_cup_seat": (
        ("arc", "acid_cup", 8, 3.6, math.pi, 2.4, 1.0, 0.0, *N),
        ("arc", "pitcher", 6, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "bone_rib", 2, 5.0, 2.0, 1.0, 0.0, *N),
    ),
    "glow_fruit": (
        ("arc", "blossom_tree", 5, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "beetle_lamp", 6, 3.2, math.pi, 2.0, 1.0, 0.0, "bob", 0.25, 6.0),
        ("arc", "butterfly", 4, 4.0, math.pi, 1.4, 1.0, 1.2, "path_circle", 1.2, 10.0),
        ("front", "butterfly", 2, 3.0, 1.2, 1.0, 1.2, "path_circle", 0.8, 8.0),
    ),
    "glass_aisle": (
        ("arc", "glass_leaf", 10, 3.5, math.pi, 2.2, 1.0, 1.0, "bob", 0.2, 6.0),
        ("arc", "blossom_tree", 4, 7.0, math.pi, 1.5, 1.0, 0.0, *N),
        ("front", "glass_leaf", 2, 3.2, 1.2, 1.0, 1.4, "bob", 0.2, 6.0),
    ),
    "moth_orchard": (
        ("arc", "glow_moth", 8, 3.2, math.pi, 2.0, 1.0, 1.0, "path_circle", 1.2, 12.0),
        ("arc", "blossom_tree", 5, 7.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "glow_moth", 2, 3.2, 1.2, 1.0, 1.4, "path_circle", 1.0, 10.0),
    ),
    "lantern_root": (
        ("front", "blossom_tree", 1, 5.0, 0.0, 2.2, 0.0, *N),
        ("arc", "flower_gold", 8, 3.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "beetle_lamp", 6, 5.0, math.pi, 2.0, 1.0, 0.0, "bob", 0.2, 6.0),
    ),
    "fiddle_bowl": (
        ("arc", "fiddlehead", 12, 3.4, math.pi, 4.0, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "fern", 8, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "fiddlehead", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "staghorn_nave": (
        ("arc", "staghorn", 8, 4.0, math.pi, 2.2, 1.0, 0.0, *N),
        ("arc", "fern", 8, 6.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "staghorn", 2, 4.6, 1.8, 1.0, 0.0, *N),
    ),
    "fern_tunnel": (
        ("arc", "fern", 10, 3.2, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "tree", 4, 7.0, math.pi, 1.6, 1.2, 0.0, *N),
        ("arc", "fiddlehead", 6, 5.0, math.pi, 1.5, 1.0, 0.0, *N),
        ("front", "fern", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "curl_overlook": (
        ("front", "tree", 2, 6.0, 1.6, 1.4, 0.0, *N),
        ("arc", "fern", 8, 4.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "flower_pink", 6, 5.0, math.pi, 1.6, 1.0, 0.0, *N),
    ),
    "root_swing": (
        ("arc", "vine_strand", 10, 4.0, math.pi, 2.2, 1.0, 4.0, "sway", 0.1, 7.0),
        ("arc", "epiphyte", 6, 5.0, math.pi, 2.0, 1.0, 3.0, *N),
        ("front", "vine_strand", 2, 3.4, 1.2, 1.0, 3.2, "sway", 0.1, 7.0),
    ),
    "epiphyte_balcony": (
        ("arc", "epiphyte", 8, 3.5, math.pi, 2.0, 1.0, 3.0, *N),
        ("arc", "vine_strand", 8, 6.0, math.pi, 2.0, 1.0, 4.0, "sway", 0.1, 7.0),
        ("arc", "blossom_tree", 3, 8.0, math.pi, 1.2, 1.0, 0.0, *N),
        ("front", "epiphyte", 2, 4.6, 1.6, 1.0, 2.4, "sway", 0.08, 6.0),
    ),
    "loris_perch": (
        ("arc", "loris", 4, 3.2, math.pi, 1.4, 1.0, 2.0, "bob", 0.12, 5.0),
        ("arc", "vine_strand", 8, 5.0, math.pi, 2.0, 1.0, 3.0, *N),
        ("arc", "epiphyte", 6, 4.0, math.pi, 1.6, 1.0, 3.5, *N),
        ("front", "vine_strand", 2, 3.4, 1.2, 1.0, 3.0, "sway", 0.1, 7.0),
    ),
    "curtain_gap": (
        ("arc", "vine_strand", 12, 3.2, math.pi, 4.0, 1.0, 3.5, "sway", 0.1, 7.0),
        ("arc", "monkey", 3, 6.0, math.pi, 1.2, 1.0, 0.0, "bob", 0.12, 4.0),
        ("front", "vine_strand", 2, 3.4, 1.2, 1.0, 3.2, "sway", 0.1, 7.0),
    ),
    "grazer_shade": (
        ("arc", "grazer", 4, 6.0, math.pi, 1.5, 1.0, 0.0, "bob", 0.08, 4.0),
        ("arc", "seed_head", 8, 4.0, math.pi, 2.0, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "tree_yellow", 3, 9.0, math.pi, 1.2, 1.1, 0.0, *N),
        ("front", "seed_head", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "seed_ring": (
        ("arc", "seed_head", 12, 3.5, math.pi, 4.0, 1.0, 0.0, "sway", 0.07, 5.0),
        ("arc", "wildflower", 8, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("front", "seed_head", 2, 4.6, 1.6, 1.0, 0.0, "sway", 0.07, 5.0),
    ),
    "dust_bowl": (
        ("arc", "boulder", 5, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "grass_patch", 8, 3.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "dirt_patch", 4, 5.0, math.pi, 1.4, 1.0, 0.0, *N),
        ("front", "grass_patch", 2, 4.6, 1.8, 1.0, 0.0, *N),
    ),
    "bird_perch": (
        ("arc", "kite_bird", 4, 5.0, math.pi, 1.4, 1.0, 3.0, "drift", 1.2, 9.0),
        ("arc", "seed_head", 8, 4.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "tree_yellow", 3, 8.0, math.pi, 1.2, 1.0, 0.0, *N),
        ("front", "kite_bird", 2, 3.4, 1.4, 1.0, 2.2, "drift", 0.8, 8.0),
    ),
    "crust_lip": (
        ("arc", "salt_crust", 10, 4.0, math.pi, 2.4, 1.0, 0.0, *N),
        ("arc", "crystal_shard", 6, 6.0, math.pi, 1.5, 1.0, 0.0, *N),
        ("front", "crystal_shard", 2, 4.6, 1.6, 1.0, 0.0, *N),
    ),
    "pink_pool": (
        ("front", "pool_disc", 1, 5.0, 0.0, 4.0, 0.0, *N),
        ("arc", "salt_crust", 8, 6.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "brine_skipper", 4, 3.2, math.pi, 1.4, 1.0, 0.4, "hop", 0.35, 6.0),
    ),
    "crystal_seat": (
        ("arc", "crystal_shard", 8, 3.5, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "salt_crust", 6, 6.0, math.pi, 1.6, 1.0, 0.0, *N),
        ("front", "bone_rib", 2, 5.5, 2.0, 1.0, 0.0, *N),
    ),
    "brine_hollow": (
        ("arc", "brine_skipper", 6, 3.0, math.pi, 1.6, 1.0, 0.4, "hop", 0.35, 6.0),
        ("arc", "salt_crust", 8, 5.0, math.pi, 2.0, 1.0, 0.0, *N),
        ("arc", "crystal_shard", 4, 7.0, math.pi, 1.4, 1.0, 0.0, *N),
        ("front", "brine_skipper", 2, 3.2, 1.2, 1.0, 0.4, "hop", 0.35, 6.0),
    ),
}
