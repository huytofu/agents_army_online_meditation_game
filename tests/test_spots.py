import math

from forest_server.world.biomes import biome_at, chunk_index, river_z
from forest_server.world.constants import SPAWN_X, SPAWN_Z
from forest_server.world.spots import (
    GATHERINGS,
    ISOLATED_STEP,
    MIN_SEAT_GAP,
    SEATS_PER_GATHERING,
    SPAWN_KEEP_M,
    generate_spots,
)

OCTANTS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def _nearest(spot, others) -> float:
    return min(
        math.hypot(spot.x - other.x, spot.z - other.z)
        for other in others
        if other.id != spot.id
    )


def test_biome_contracts():
    assert biome_at(-24, 0) == "moss_plain"
    assert biome_at(0, river_z(0)) == "river"
    assert biome_at(1600, river_z(1600)) == "waterfall_gorge"
    for biome, kind, a, b, _radius in GATHERINGS:
        if kind == "disk":
            assert biome_at(a, b) == biome


def test_spot_counts_and_identity():
    first = generate_spots()
    second = generate_spots()
    assert [(s.id, s.x, s.z, s.biome, s.archetype, s.yaw, s.gathering) for s in first] == [
        (s.id, s.x, s.z, s.biome, s.archetype, s.yaw, s.gathering) for s in second
    ]
    assert [s.id for s in first] == list(range(1, 1501))
    counts = {biome: 0 for biome, *_rest in GATHERINGS}
    isolated = 0
    for spot in first:
        if spot.gathering is None:
            isolated += 1
        else:
            counts[spot.gathering] += 1
            assert spot.biome == spot.gathering
        assert abs(spot.z - river_z(spot.x)) >= 16
        assert math.hypot(spot.x - SPAWN_X, spot.z - SPAWN_Z) >= SPAWN_KEEP_M
    assert isolated == 300
    assert counts == {biome: SEATS_PER_GATHERING for biome, *_rest in GATHERINGS}
    assert len(first) == 1500


def test_gatherings_are_irregular_and_ten_meters_apart():
    spots = generate_spots()
    for biome, *_rest in GATHERINGS:
        group = [spot for spot in spots if spot.gathering == biome]
        gaps = [_nearest(spot, group) for spot in group]
        assert min(gaps) >= MIN_SEAT_GAP
        assert max(gaps) - min(gaps) > 5


def test_home_gathering_surrounds_spawn():
    spots = [spot for spot in generate_spots() if spot.gathering == "moss_plain"]
    nearest = {name: math.inf for name in OCTANTS}
    for spot in spots:
        angle = math.degrees(math.atan2(spot.x - SPAWN_X, spot.z - SPAWN_Z)) % 360
        name = OCTANTS[int((angle + 22.5) // 45) % 8]
        nearest[name] = min(nearest[name], math.hypot(spot.x - SPAWN_X, spot.z - SPAWN_Z))
    assert all(distance <= 40 for distance in nearest.values())


def test_separation_and_chunks():
    spots = generate_spots()
    isolated = [spot for spot in spots if spot.gathering is None]
    gathered = [spot for spot in spots if spot.gathering is not None]
    for index, spot in enumerate(isolated):
        for other in isolated[index + 1 :]:
            assert math.hypot(spot.x - other.x, spot.z - other.z) >= ISOLATED_STEP
        assert _nearest(spot, gathered) >= MIN_SEAT_GAP
    assert (chunk_index(1500), chunk_index(1250)) == (54, 50)
    assert (chunk_index(800), chunk_index(-1600)) == (43, 6)
    assert (chunk_index(-1400), chunk_index(-1600)) == (9, 6)
    assert (chunk_index(-24), chunk_index(0)) == (30, 31)
    heron_z = river_z(-800)
    assert (chunk_index(-800), chunk_index(heron_z)) == (18, 28)
