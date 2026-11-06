from forest_server.world.biomes import BANDS
from forest_server.world.catalog import world_meta
from forest_server.world.landmarks import LANDMARKS


def test_map_meta_lists_every_landmark_and_biome_color():
    meta = world_meta()
    assert [(item["name"], item["x"], item["z"]) for item in meta["landmarks"]] == [
        (item["name"], item["x"], item["z"]) for item in LANDMARKS
    ]
    names = {name for _z0, _z1, _closed, columns in BANDS for *_bounds, name in columns}
    names.add("river")
    for name in names:
        color = meta["palettes"][name]["map"]
        assert color.startswith("#") and len(color) == 7
