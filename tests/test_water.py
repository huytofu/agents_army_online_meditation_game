from forest_server.world.biomes import chunk_index, river_z
from forest_server.world.ground import ground_height
from forest_server.world.water import water_in_chunk


def test_river_ribbon_sits_above_the_ground():
    x = -24.0
    z = river_z(x)
    samples = water_in_chunk(chunk_index(x), chunk_index(z))
    assert len(samples) >= 2
    for sample in samples:
        assert sample["y"] > ground_height(sample["x"], sample["z"])
