import math

from forest_server.world.biomes import RIVER_MESH_INSET, RIVER_WET, biome_at, chunk_index, river_z
from forest_server.world.constants import TERMS
from forest_server.world.ground import ground_height
from forest_server.world.water import water_in_chunk

# Avatar head sits at 1.54 m with radius 0.16 m, so the neck is 1.38 m.
NECK = 1.38


def _waves(x: float, z: float) -> float:
    return sum(a * math.sin(kx * x + kz * z + phase) for a, kx, kz, phase in TERMS)


def _centerline() -> list[tuple[float, float]]:
    points = []
    x = -2000.0
    while x <= 2000.0 + 1e-6:
        z = river_z(x)
        if biome_at(x, z) == "river":
            points.append((x, z))
        x += 8.0
    return points


def _surface(x: float, z: float) -> float:
    samples = water_in_chunk(chunk_index(x), chunk_index(z))
    return next(sample["y"] for sample in samples if abs(sample["x"] - x) < 1e-6)


def test_river_ribbon_sits_above_the_ground():
    x = -24.0
    z = river_z(x)
    samples = water_in_chunk(chunk_index(x), chunk_index(z))
    assert len(samples) >= 2
    for sample in samples:
        assert sample["y"] > ground_height(sample["x"], sample["z"])


def test_river_ribbon_connects_across_chunk_borders():
    points = _centerline()
    assert len(points) > 50
    seams = 0
    for (x0, z0), (x1, _z1) in zip(points, points[1:]):
        if x1 - x0 > 8.0 + 1e-6:
            continue
        seams += 1
        samples = water_in_chunk(chunk_index(x0), chunk_index(z0))
        xs = [sample["x"] for sample in samples]
        assert any(abs(sample_x - x0) < 1e-6 for sample_x in xs)
        assert any(abs(sample_x - x1) < 1e-6 for sample_x in xs)
    assert seams > 30


def test_river_is_deepest_at_the_neck_in_the_middle():
    x = 0.0
    z = river_z(x)
    surface = _surface(x, z)
    center = ground_height(x, z)
    assert abs((surface - center) - NECK) < 1e-9
    previous = center
    for lateral in (4.0, 8.0, 12.0, 15.0):
        left = ground_height(x, z - lateral)
        right = ground_height(x, z + lateral)
        assert abs(left - right) < 1e-9
        assert left > previous
        previous = left
        assert surface - left < NECK
    outer = z + RIVER_WET + 2.0
    assert abs(ground_height(x, outer) - _waves(x, outer)) < 1e-9
    gorge_x = 1200.0
    gorge_z = river_z(gorge_x)
    assert biome_at(gorge_x, gorge_z) == "waterfall_gorge"
    assert abs(ground_height(gorge_x, gorge_z) - _waves(gorge_x, gorge_z)) < 1e-9


def test_ground_grid_cannot_bridge_into_the_ribbon():
    # Client ground quads are 2 m, including the diagonal. The sheet is inset
    # by more than the largest river-distance jump, so a high bank vertex
    # cannot reach the water.
    step = 2.0
    worst = 0.0
    x = -2000.0
    while x <= 2000.0 + 1e-6:
        zc = river_z(x)
        for ix in range(-1, 3):
            for iz in range(-12, 13):
                x1 = x + ix * step
                z1 = zc + iz * step
                lat1 = abs(z1 - river_z(x1))
                for dx, dz in ((step, 0.0), (0.0, step), (step, step), (step, -step)):
                    x2 = x1 + dx
                    z2 = z1 + dz
                    lat2 = abs(z2 - river_z(x2))
                    worst = max(worst, abs(lat2 - lat1))
        x += 32.0
    assert worst < RIVER_MESH_INSET


def test_channel_bed_stays_under_the_water_sheet():
    for x, z in _centerline()[::7]:
        surface = _surface(x, z)
        for step in range(17):
            lateral = step * RIVER_WET / 16.0
            assert ground_height(x, z + lateral) < surface
            assert ground_height(x, z - lateral) < surface
