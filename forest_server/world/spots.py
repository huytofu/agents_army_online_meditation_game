"""Seat clearings and isolated seats. Python is the only place these coordinates exist."""

import math
from dataclasses import dataclass

from forest_server.world.biomes import ARCHETYPES, biome_at, chunk_index, river_z
from forest_server.world.constants import WORLD_MAX, WORLD_MIN, WORLD_SEED
from forest_server.world.ground import ground_height

ROW_H = 8.0 * math.sqrt(3) / 2

# name, biome, x, z, radius, expected count
FIELDS = (
    ("dew_camp", "moss_plain", -1100.0, 200.0, 76.0, 313),
    ("mushroom_yard", "moss_plain", -400.0, 500.0, 70.0, 283),
    ("bloom_bowl", "valley_bloom", -1200.0, 1400.0, 84.0, 397),
    ("petal_steps", "valley_bloom", -700.0, 1650.0, 72.0, 301),
    ("vine_loft", "hanging_vines", 200.0, 1500.0, 74.0, 313),
    ("fall_ledge", "waterfall_gorge", 1400.0, 1600.0, 68.0, 253),
    ("fern_hollow", "fern_sea", -1200.0, -700.0, 80.0, 367),
    ("bog_ring", "carnivorous_bog", 400.0, -700.0, 76.0, 313),
    ("herd_shade", "amber_herd", 1550.0, -600.0, 78.0, 349),
    ("orchard_glow", "lantern_orchard", 1200.0, 300.0, 82.0, 379),
    ("spore_camp", "strange_fauna", -1200.0, -1550.0, 74.0, 313),
    ("nave_roots", "cathedral_trees", 700.0, -1550.0, 80.0, 363),
    ("mirror_shelf", "salt_mirror", 1700.0, -1550.0, 66.0, 253),
)


@dataclass(frozen=True)
class Spot:
    id: int
    biome: str
    archetype: str
    x: float
    y: float
    z: float
    yaw: float
    chunk_x: int
    chunk_z: int

    def as_row(self) -> dict:
        return {
            "id": self.id,
            "biome": self.biome,
            "archetype": self.archetype,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "yaw": self.yaw,
            "chunk_x": self.chunk_x,
            "chunk_z": self.chunk_z,
        }


def _inside_world(x: float, z: float) -> bool:
    return WORLD_MIN < x < WORLD_MAX and WORLD_MIN < z < WORLD_MAX


def _clearing_points(cx: float, cz: float, radius: float, biome: str) -> list[tuple[float, float]]:
    max_row = int(radius / ROW_H) + 2
    max_col = int(radius / 8.0) + 2
    points: list[tuple[float, float]] = []
    for row in range(-max_row, max_row + 1):
        z = cz + row * ROW_H
        stagger = 4.0 if row % 2 else 0.0
        for col in range(-max_col, max_col + 1):
            x = cx + col * 8.0 + stagger
            if math.hypot(x - cx, z - cz) > radius:
                continue
            if not _inside_world(x, z):
                continue
            if abs(z - river_z(x)) < 16.0:
                continue
            if biome_at(x, z) != biome:
                continue
            points.append((x, z))
    return points


def _isolated_points() -> list[tuple[float, float]]:
    coords = [-1800.0 + 220.0 * i for i in range(17)]
    kept: list[tuple[float, float]] = []
    for ix, x in enumerate(coords):
        for iz, z in enumerate(coords):
            if abs(z - river_z(x)) < 16.0:
                continue
            if any(
                math.hypot(x - fx, z - fz) <= radius + 80.0
                for _name, _biome, fx, fz, radius, _count in FIELDS
            ):
                continue
            digest = (WORLD_SEED ^ (ix * 73856093) ^ (iz * 19349663)) & 0xFFFFFFFF
            if digest % 100 >= 22:
                continue
            kept.append((x, z))
    return kept


def _decorate(raw: list[tuple[float, float]]) -> list[Spot]:
    spots: list[Spot] = []
    for index, (x, z) in enumerate(raw, start=1):
        biome = biome_at(x, z)
        if biome is None:
            raise RuntimeError(f"spot {(x, z)} has no biome")
        seed = (WORLD_SEED + index * 1013904223) & 0xFFFFFFFF
        yaw = (seed % 3600) / 3600.0 * math.tau
        archetype = ARCHETYPES[biome][(seed >> 8) % 4]
        spots.append(
            Spot(
                id=index,
                biome=biome,
                archetype=archetype,
                x=x,
                y=ground_height(x, z),
                z=z,
                yaw=yaw,
                chunk_x=chunk_index(x),
                chunk_z=chunk_index(z),
            )
        )
    return spots


def generate_spots() -> list[Spot]:
    raw: list[tuple[float, float]] = []
    for _name, biome, x, z, radius, _count in FIELDS:
        raw.extend(_clearing_points(x, z, radius, biome))
    raw.extend(_isolated_points())
    return _decorate(raw)


def field_name_for(x: float, z: float) -> str | None:
    for name, _biome, fx, fz, radius, _count in FIELDS:
        if math.hypot(x - fx, z - fz) <= radius:
            return name
    return None
