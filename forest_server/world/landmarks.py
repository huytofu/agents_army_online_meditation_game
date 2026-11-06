"""Twelve authored landmarks. Block lists stay even when a glTF replaces the drawing."""

import math

from forest_server.world.biomes import chunk_index, river_z
from forest_server.world.ground import ground_height
from forest_server.world.scatter import MOTION


def _at(kit: str, x: float, z: float, scale: float, rot_y: float = 0.0, y_lift: float = 0.0) -> dict:
    motion, amount, period = MOTION.get(kit, ("none", 0.0, 1.0))
    return {
        "kit": kit,
        "variant": 0,
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


def _ring(kit: str, cx: float, cz: float, radius: float, count: int, scale: float, y_lift: float = 0.0) -> list[dict]:
    blocks = []
    for index in range(count):
        angle = (index / count) * math.tau
        blocks.append(
            _at(
                kit,
                cx + math.cos(angle) * radius,
                cz + math.sin(angle) * radius,
                scale,
                angle,
                y_lift,
            )
        )
    return blocks


def _great_fall() -> list[dict]:
    cx, cz = 1500.0, 1250.0
    blocks = _ring("cliff_wall", cx, cz + 6.0, 10.0, 7, 2.2)
    for index, x_off in enumerate((-6.0, -2.0, 2.0, 6.0)):
        blocks.append(_at("waterfall_sheet", cx + x_off, cz + 4.0, 8.0, rot_y=0.0, y_lift=1.0))
    blocks.append(_at("pool_disc", cx, cz - 2.0, 6.0))
    blocks.extend(_ring("mist_card", cx, cz, 8.0, 6, 1.4, y_lift=2.0))
    blocks.append(_at("rainbow_card", cx - 4.0, cz + 2.0, 2.0, y_lift=6.0))
    blocks.append(_at("rainbow_card", cx + 4.0, cz + 2.0, 2.0, y_lift=6.0))
    return blocks


def _cathedral_heart() -> list[dict]:
    return _ring("tree", 800.0, -1600.0, 14.0, 7, 2.2)


def _spore_well() -> list[dict]:
    cx, cz = -1400.0, -1600.0
    return (
        _ring("spore", cx, cz, 6.0, 14, 1.0, y_lift=1.2)
        + _ring("spiral_tree", cx, cz, 12.0, 8, 1.3)
        + _ring("glow_moth", cx, cz, 8.0, 6, 1.0, y_lift=3.0)
    )


def _bloom_ridge() -> list[dict]:
    cx, cz = -1500.0, 1700.0
    return (
        _ring("ridge_card", cx, cz, 12.0, 7, 3.2)
        + _ring("wildflower", cx, cz, 7.0, 16, 1.0)
        + _ring("kite_bird", cx, cz, 9.0, 4, 1.0, y_lift=4.0)
    )


def _pitcher_throne() -> list[dict]:
    cx, cz = 500.0, -800.0
    blocks = [_at("pitcher", cx, cz + 2.0, 4.2)]
    blocks.extend(_ring("pitcher", cx, cz, 7.0, 8, 1.2))
    blocks.extend(_ring("sundew", cx, cz, 4.5, 8, 1.0))
    blocks.extend(_ring("snap_maw", cx, cz, 9.0, 4, 1.1))
    blocks.append(_at("acid_cup", cx, cz - 1.5, 1.6))
    return blocks


def _lantern_monarch() -> list[dict]:
    cx, cz = 1500.0, 400.0
    return (
        [_at("blossom_tree", cx, cz, 3.2)]
        + _ring("glass_leaf", cx, cz, 6.0, 10, 1.0, y_lift=2.0)
        + _ring("glow_moth", cx, cz, 8.0, 8, 1.0, y_lift=3.5)
    )


def _mirror_pan() -> list[dict]:
    cx, cz = 1750.0, -1500.0
    return (
        [_at("pool_disc", cx, cz, 14.0)]
        + _ring("salt_crust", cx, cz, 16.0, 12, 1.2)
        + _ring("crystal_shard", cx, cz, 12.0, 8, 1.4)
        + _ring("brine_skipper", cx, cz, 10.0, 6, 1.0, y_lift=0.4)
    )


def _heron_bend() -> list[dict]:
    cx, cz = -800.0, river_z(-800.0)
    blocks = []
    for index, along in enumerate((-4.0, 0.0, 4.0)):
        blocks.append(_at("heron", cx + along, cz + 3.0, 1.0, rot_y=index))
    blocks.extend(_ring("reed", cx, cz, 6.0, 10, 1.0))
    blocks.extend(_ring("river_stone", cx, cz, 3.5, 6, 1.0))
    blocks.extend(_ring("dragonfly", cx, cz, 5.0, 4, 1.0, y_lift=1.5))
    return blocks


def _vine_gate() -> list[dict]:
    cx, cz = 100.0, 1600.0
    blocks = [
        _at("cliff_wall", cx - 4.0, cz, 2.4),
        _at("cliff_wall", cx + 4.0, cz, 2.4),
    ]
    for index in range(8):
        x = cx - 3.5 + index
        blocks.append(_at("vine_strand", x, cz, 1.0, y_lift=3.0 + (index % 3)))
    blocks.extend(_ring("epiphyte", cx, cz, 3.0, 6, 1.0, y_lift=4.0))
    blocks.extend(_ring("loris", cx, cz, 3.2, 4, 1.0, y_lift=2.5))
    return blocks


def _amber_circle() -> list[dict]:
    cx, cz = 1600.0, -700.0
    blocks = []
    for index in range(6):
        angle = (index / 6) * math.tau
        blocks.append(
            _at(
                "grazer",
                cx + math.cos(angle) * 8.0,
                cz + math.sin(angle) * 8.0,
                1.0,
                rot_y=angle + math.pi,
            )
        )
    blocks.extend(_ring("seed_head", cx, cz, 5.0, 10, 1.0))
    blocks.extend(_ring("kite_bird", cx, cz, 6.0, 3, 1.0, y_lift=5.0))
    return blocks


def _fern_nave() -> list[dict]:
    cx, cz = -1400.0, -650.0
    blocks = []
    for index, along in enumerate((-10.0, -6.0, -2.0, 2.0, 6.0, 10.0)):
        blocks.append(_at("fern", cx - 3.6, cz + along, 1.2, rot_y=0.2))
        blocks.append(_at("fern", cx + 3.6, cz + along, 1.2, rot_y=-0.2))
        blocks.append(_at("staghorn", cx - 5.2, cz + along, 1.3))
        blocks.append(_at("staghorn", cx + 5.2, cz + along, 1.3))
    for index, along in enumerate((-8.0, -4.0, 0.0, 4.0)):
        blocks.append(_at("fiddlehead", cx - 6.4, cz + along, 1.0))
        blocks.append(_at("fiddlehead", cx + 6.4, cz + along, 1.0))
    return blocks


def _sundew_jewel() -> list[dict]:
    cx, cz = 200.0, -500.0
    return (
        [_at("sundew", cx, cz, 3.6)]
        + _ring("sundew", cx, cz, 5.0, 10, 0.8)
        + _ring("crystal_shard", cx, cz, 3.0, 4, 1.2)
    )


LANDMARKS = (
    {"name": "great_fall", "x": 1500.0, "z": 1250.0, "blocks": _great_fall()},
    {"name": "cathedral_heart", "x": 800.0, "z": -1600.0, "blocks": _cathedral_heart()},
    {"name": "spore_well", "x": -1400.0, "z": -1600.0, "blocks": _spore_well()},
    {"name": "bloom_ridge", "x": -1500.0, "z": 1700.0, "blocks": _bloom_ridge()},
    {"name": "pitcher_throne", "x": 500.0, "z": -800.0, "blocks": _pitcher_throne()},
    {"name": "lantern_monarch", "x": 1500.0, "z": 400.0, "blocks": _lantern_monarch()},
    {"name": "mirror_pan", "x": 1750.0, "z": -1500.0, "blocks": _mirror_pan()},
    {"name": "heron_bend", "x": -800.0, "z": river_z(-800.0), "blocks": _heron_bend()},
    {"name": "vine_gate", "x": 100.0, "z": 1600.0, "blocks": _vine_gate()},
    {"name": "amber_circle", "x": 1600.0, "z": -700.0, "blocks": _amber_circle()},
    {"name": "fern_nave", "x": -1400.0, "z": -650.0, "blocks": _fern_nave()},
    {"name": "sundew_jewel", "x": 200.0, "z": -500.0, "blocks": _sundew_jewel()},
)


def landmarks_in_chunk(cx: int, cz: int) -> list[dict]:
    found = []
    for landmark in LANDMARKS:
        if chunk_index(landmark["x"]) == cx and chunk_index(landmark["z"]) == cz:
            found.append(
                {
                    "name": landmark["name"],
                    "x": landmark["x"],
                    "z": landmark["z"],
                    "blocks": landmark["blocks"],
                }
            )
    return found
