import json
import struct
from pathlib import Path

from forest_server.world.catalog import kit_names
from forest_server.world.landmarks import LANDMARKS

ROOT = Path("web/assets")
LANDMARK_NAMES = {mark["name"] for mark in LANDMARKS}


def _glb_stats(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:4] == b"glTF"
    chunk_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + chunk_length])
    accessors = document["accessors"]
    meshes = document.get("meshes", [])
    triangles = 0
    for mesh in meshes:
        for primitive in mesh["primitives"]:
            if "indices" in primitive:
                triangles += accessors[primitive["indices"]]["count"] // 3
            else:
                triangles += accessors[primitive["attributes"]["POSITION"]]["count"] // 3
    return len(meshes), triangles


def test_committed_gltfs_match_the_catalog():
    kits = sorted((ROOT / "kits").glob("*.glb")) if (ROOT / "kits").exists() else []
    landmarks = sorted((ROOT / "landmarks").glob("*.glb")) if (ROOT / "landmarks").exists() else []
    known = set(kit_names())
    for path in kits:
        assert path.stem in known
        mesh_count, triangles = _glb_stats(path)
        assert mesh_count == 1
        assert triangles <= 50000
    for path in landmarks:
        assert path.stem in LANDMARK_NAMES
        _mesh_count, triangles = _glb_stats(path)
        assert triangles <= 400000
