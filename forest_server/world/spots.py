"""One irregular cushion gathering per biome, plus scattered single cushions.

Python is the only place these coordinates exist. Gatherings are rejection-sampled,
so the cushions do not sit on a lattice.
"""

import math
from dataclasses import dataclass

from forest_server.world.biomes import ARCHETYPES, biome_at, chunk_index, river_z
from forest_server.world.constants import SPAWN_X, SPAWN_Z, WORLD_MAX, WORLD_MIN, WORLD_SEED
from forest_server.world.ground import ground_height
from forest_server.world.rng import mulberry32

MIN_SEAT_GAP = 10.0
SPAWN_KEEP_M = 14.0
SEATS_PER_GATHERING = 100
ISOLATED_STEP = 280.0
ISOLATED_ORIGIN = -1680.0
ISOLATED_STEPS = 13
SAMPLE_LIMIT = SEATS_PER_GATHERING * 400

# biome, kind, a, b, radius. Disks use a,b as the center. The river uses a,b as an x span.
GATHERINGS = (
    ("moss_plain", "disk", -24.0, 0.0, 95.0),
    ("cathedral_trees", "disk", 800.0, -1550.0, 120.0),
    ("river", "river", -600.0, 400.0, 0.0),
    ("waterfall_gorge", "disk", 1500.0, 1500.0, 140.0),
    ("valley_bloom", "disk", -1200.0, 1450.0, 120.0),
    ("strange_fauna", "disk", -1100.0, -1550.0, 120.0),
    ("carnivorous_bog", "disk", 400.0, -650.0, 120.0),
    ("lantern_orchard", "disk", 1400.0, 200.0, 120.0),
    ("fern_sea", "disk", -1200.0, -650.0, 120.0),
    ("hanging_vines", "disk", 200.0, 1500.0, 120.0),
    ("amber_herd", "disk", 1550.0, -650.0, 120.0),
    ("salt_mirror", "disk", 1700.0, -1550.0, 110.0),
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
    gathering: str | None

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


def _clear(x: float, z: float, biome: str, taken: list[tuple[float, float]]) -> bool:
    if not _inside_world(x, z):
        return False
    if abs(z - river_z(x)) < 16.0:
        return False
    if biome_at(x, z) != biome:
        return False
    if math.hypot(x - SPAWN_X, z - SPAWN_Z) < SPAWN_KEEP_M:
        return False
    return all(math.hypot(x - px, z - pz) >= MIN_SEAT_GAP for px, pz in taken)


def _sample_disk(cx: float, cz: float, radius: float, biome: str, rng) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    tries = 0
    while len(points) < SEATS_PER_GATHERING and tries < SAMPLE_LIMIT:
        tries += 1
        angle = rng() * math.tau
        dist = radius * math.sqrt(rng())
        x = cx + math.cos(angle) * dist
        z = cz + math.sin(angle) * dist
        if _clear(x, z, biome, points):
            points.append((x, z))
    return points


def _sample_river(x0: float, x1: float, rng) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    tries = 0
    while len(points) < SEATS_PER_GATHERING and tries < SAMPLE_LIMIT:
        tries += 1
        x = x0 + rng() * (x1 - x0)
        side = -1.0 if rng() < 0.5 else 1.0
        offset = 18.0 + rng() * 34.0
        z = river_z(x) + side * offset
        if _clear(x, z, "river", points):
            points.append((x, z))
    return points


def _gathering_points() -> list[tuple[str, float, float]]:
    placed: list[tuple[str, float, float]] = []
    for index, (biome, kind, a, b, radius) in enumerate(GATHERINGS):
        seed = (WORLD_SEED ^ ((index + 1) * 0x9E3779B1)) & 0xFFFFFFFF
        rng = mulberry32(seed)
        if kind == "disk":
            points = _sample_disk(a, b, radius, biome, rng)
        elif kind == "river":
            points = _sample_river(a, b, rng)
        else:
            raise RuntimeError(f"unknown gathering {kind}")
        if len(points) != SEATS_PER_GATHERING:
            raise RuntimeError(f"{biome} placed {len(points)} cushions, wanted {SEATS_PER_GATHERING}")
        placed.extend((biome, x, z) for x, z in points)
    return placed


def _isolated_points(taken: list[tuple[float, float]]) -> list[tuple[float, float]]:
    coords = [ISOLATED_ORIGIN + ISOLATED_STEP * index for index in range(ISOLATED_STEPS)]
    kept: list[tuple[float, float]] = []
    for x in coords:
        for z in coords:
            if abs(z - river_z(x)) < 16.0:
                continue
            if math.hypot(x - SPAWN_X, z - SPAWN_Z) < SPAWN_KEEP_M:
                continue
            if not _inside_world(x, z) or biome_at(x, z) is None:
                continue
            if any(math.hypot(x - px, z - pz) < MIN_SEAT_GAP for px, pz in taken):
                continue
            kept.append((x, z))
    return kept


def _decorate(raw: list[tuple[str | None, float, float]]) -> list[Spot]:
    spots: list[Spot] = []
    for index, (gathering, x, z) in enumerate(raw, start=1):
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
                gathering=gathering,
            )
        )
    return spots


def generate_spots() -> list[Spot]:
    gathered = _gathering_points()
    isolated = _isolated_points([(x, z) for _name, x, z in gathered])
    raw: list[tuple[str | None, float, float]] = list(gathered)
    raw.extend((None, x, z) for x, z in isolated)
    return _decorate(raw)


def gathering_markers() -> list[dict]:
    markers = []
    for biome, kind, a, b, radius in GATHERINGS:
        if kind == "disk":
            markers.append({"name": biome, "x": a, "z": b, "radius": radius})
        else:
            mid = (a + b) / 2.0
            markers.append({"name": biome, "x": mid, "z": river_z(mid) + 28.0, "radius": 24.0})
    return markers
