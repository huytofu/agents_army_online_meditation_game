import math

from forest_server.world.biomes import biome_at, chunk_index, river_z
from forest_server.world.spots import FIELDS, field_name_for, generate_spots


def test_biome_contracts():
    assert biome_at(-24, 0) == "moss_plain"
    assert biome_at(0, river_z(0)) == "river"
    assert biome_at(1600, river_z(1600)) == "waterfall_gorge"
    for name, biome, x, z, _radius, _count in FIELDS:
        assert biome_at(x, z) == biome, name


def test_spot_counts_and_identity():
    first = generate_spots()
    second = generate_spots()
    assert [(s.id, s.x, s.z, s.biome, s.archetype, s.yaw) for s in first] == [
        (s.id, s.x, s.z, s.biome, s.archetype, s.yaw) for s in second
    ]
    assert [s.id for s in first] == list(range(1, 4257))
    counts = {name: 0 for name, *_rest in FIELDS}
    isolated = 0
    for spot in first:
        field = field_name_for(spot.x, spot.z)
        if field is None:
            isolated += 1
        else:
            counts[field] += 1
        assert abs(spot.z - river_z(spot.x)) >= 16
    assert isolated == 59
    for name, _biome, _x, _z, _radius, expected in FIELDS:
        assert counts[name] == expected
    assert len(first) == 4256


def test_separation_and_chunks():
    spots = generate_spots()
    by_field: dict[str, list] = {name: [] for name, *_rest in FIELDS}
    isolated = []
    for spot in spots:
        field = field_name_for(spot.x, spot.z)
        if field is None:
            isolated.append(spot)
        else:
            by_field[field].append(spot)
    for group in by_field.values():
        for index, spot in enumerate(group):
            nearest = min(
                math.hypot(spot.x - other.x, spot.z - other.z)
                for other_index, other in enumerate(group)
                if other_index != index
            )
            assert nearest >= 7.99
    for index, spot in enumerate(isolated):
        for other in isolated[index + 1 :]:
            assert math.hypot(spot.x - other.x, spot.z - other.z) >= 220
        for _name, _biome, fx, fz, radius, _count in FIELDS:
            assert math.hypot(spot.x - fx, spot.z - fz) > radius + 80
    assert (chunk_index(1500), chunk_index(1250)) == (54, 50)
    assert (chunk_index(800), chunk_index(-1600)) == (43, 6)
    assert (chunk_index(-1400), chunk_index(-1600)) == (9, 6)
    assert (chunk_index(-1100), chunk_index(200)) == (14, 34)
    heron_z = river_z(-800)
    assert (chunk_index(-800), chunk_index(heron_z)) == (18, 28)
