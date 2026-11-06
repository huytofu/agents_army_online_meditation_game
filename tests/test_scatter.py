import math

from forest_server.world.biomes import AIRY_KITS, CARNIVOROUS_KITS, biome_at, chunk_index
from forest_server.world.landmarks import LANDMARKS, landmarks_in_chunk
from forest_server.world.scatter import SCATTER, scatter_for_chunk


def _chunk(x: float, z: float):
    return scatter_for_chunk(chunk_index(x), chunk_index(z))


def _counts(blocks):
    found: dict[str, int] = {}
    for block in blocks:
        found[block["kit"]] = found.get(block["kit"], 0) + 1
    return found


def test_moss_chunk_matches_the_recipe():
    blocks = _chunk(-1100, 200)
    expected = {kit: count for kit, count, _scale in SCATTER["moss_plain"]}
    assert _counts(blocks) == expected
    for block in blocks:
        assert biome_at(block["x"], block["z"]) == "moss_plain"


def test_cathedral_trees_are_tall():
    blocks = _chunk(700, -1550)
    expected = {kit: count for kit, count, _scale in SCATTER["cathedral_trees"]}
    assert _counts(blocks) == expected
    trees = [block for block in blocks if block["kit"] == "tree"]
    assert trees
    assert all(block["scale"] >= 1.6 for block in trees)


def test_bog_is_carnivorous_and_valley_is_not():
    bog = _chunk(400, -700)
    assert any(block["kit"] == "pitcher" for block in bog)
    forbidden = {"wildflower", "blossom_tree", "fern", "mushroom"}
    assert forbidden.isdisjoint(block["kit"] for block in bog)
    valley = _chunk(-1200, 1400)
    assert any(block["kit"] == "wildflower" for block in valley)
    assert CARNIVOROUS_KITS and set(CARNIVOROUS_KITS).isdisjoint(block["kit"] for block in valley)


def test_native_pieces_stay_in_one_biome():
    homes = {
        "monkey": (200, 1500, "hanging_vines"),
        "water_puddle": (0, None, "river"),
        "mud_patch": (400, -700, "carnivorous_bog"),
        "tree_dead": (700, -1550, "cathedral_trees"),
        "mushroom_white": (-1200, -1550, "strange_fauna"),
    }
    from forest_server.world.biomes import river_z

    river_point = (0, river_z(0))
    for kit, (x, z, biome) in homes.items():
        if z is None:
            x, z = river_point
        blocks = _chunk(x, z)
        assert any(block["kit"] == kit for block in blocks), kit
        assert all(biome_at(block["x"], block["z"]) == biome for block in blocks if block["kit"] == kit)
    moss = _chunk(-1100, 200)
    moss_kits = {block["kit"] for block in moss}
    assert "monkey" not in moss_kits
    assert "water_puddle" not in moss_kits
    assert "mud_patch" not in moss_kits
    assert "tree_dead" not in moss_kits
    assert "mushroom_white" not in moss_kits
    assert "rabbit" in moss_kits
    assert "flower_pink" in moss_kits


def test_landmark_recipes():
    great = landmarks_in_chunk(54, 50)
    sheets = [block for mark in great for block in mark["blocks"] if block["kit"] == "waterfall_sheet"]
    assert sheets
    assert all(block["scale"] >= 8 for block in sheets)
    heart = next(mark for mark in LANDMARKS if mark["name"] == "cathedral_heart")
    trees = [block for block in heart["blocks"] if block["kit"] == "tree"]
    assert len(trees) == 7
    assert all(block["scale"] >= 2.2 for block in trees)
    throne = next(mark for mark in LANDMARKS if mark["name"] == "pitcher_throne")
    assert any(block["kit"] == "pitcher" and block["scale"] >= 4 for block in throne["blocks"])
    jewel = next(mark for mark in LANDMARKS if mark["name"] == "sundew_jewel")
    assert any(block["kit"] == "sundew" and block["scale"] >= 3.5 for block in jewel["blocks"])
    nave = next(mark for mark in LANDMARKS if mark["name"] == "fern_nave")
    kits = _counts(nave["blocks"])
    assert kits["fern"] >= 12
    assert kits["staghorn"] >= 6
    for block in nave["blocks"]:
        if block["kit"] in AIRY_KITS:
            continue
        assert math.hypot(block["x"] - nave["x"], block["z"] - nave["z"]) > 1.2
