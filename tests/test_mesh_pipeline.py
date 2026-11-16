"""Orientation and the GLB material. TripoSR itself is not loaded."""

import json
import struct
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image

from tools.generate_kit_mesh import (
    export_pbr_glb,
    fit_ground,
    fit_standing,
    silhouette_iou,
    triposr_to_ground,
    triposr_to_standing,
)
from tools.prepare_reference import GROUND, SKIP


def test_triposr_axes_become_y_up():
    # (x back-to-front toward the camera, y image right, z image up)
    front = triposr_to_standing(np.array([[1.0, 0.0, 0.0]]))
    right = triposr_to_standing(np.array([[0.0, 1.0, 0.0]]))
    up = triposr_to_standing(np.array([[0.0, 0.0, 1.0]]))
    assert front[0].tolist() == pytest.approx([0.0, 0.0, 1.0])
    assert right[0].tolist() == pytest.approx([1.0, 0.0, 0.0])
    assert up[0].tolist() == pytest.approx([0.0, 1.0, 0.0])


def test_overhead_photo_lies_on_the_ground():
    up = triposr_to_ground(np.array([[0.0, 0.0, 1.0]]))
    front = triposr_to_ground(np.array([[1.0, 0.0, 0.0]]))
    assert up[0, 2] == pytest.approx(-1.0)
    assert up[0, 1] == pytest.approx(0.0)
    assert front[0, 1] == pytest.approx(1.0)


def test_fit_seats_and_scales():
    standing = np.array([[0.0, -2.0, 0.0], [0.0, 2.0, 0.0], [1.0, 0.0, -1.0]])
    fitted = fit_standing(standing, 1.3)
    assert fitted[:, 1].min() == pytest.approx(0.0)
    assert fitted[:, 1].max() == pytest.approx(1.3)
    assert fitted[:, 0].min() == pytest.approx(-fitted[:, 0].max())

    flat = np.array([[-2.0, 5.0, -1.0], [2.0, 5.0, 1.0], [0.0, 9.0, 0.0]])
    laid = fit_ground(flat, 1.4)
    assert laid[:, 1].min() == pytest.approx(0.0)
    span = max(laid[:, 0].max() - laid[:, 0].min(), laid[:, 2].max() - laid[:, 2].min())
    assert span == pytest.approx(1.4)


def _triangle():
    vertices = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.2]], dtype=np.float64)
    faces = np.array([[0, 1, 2]])
    uvs = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    normals = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]])
    texture = Image.new("RGBA", (4, 4), (20, 180, 40, 255))
    return vertices, faces, uvs, texture, normals


def test_script_runs_from_the_documented_command():
    result = subprocess.run(
        [sys.executable, "tools/generate_kit_mesh.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "kit-name" in result.stdout or "heron" in result.stdout


def test_exported_glb_is_nonmetallic(tmp_path):
    vertices, faces, uvs, texture, normals = _triangle()
    path = tmp_path / "sample.glb"
    export_pbr_glb(vertices, faces, uvs, texture, normals, path)
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + length])
    material = document["materials"][0]["pbrMetallicRoughness"]
    assert material["metallicFactor"] == 0.0
    assert material["roughnessFactor"] == 1.0
    assert material["baseColorFactor"] == [1.0, 1.0, 1.0, 1.0]
    assert "baseColorTexture" in material
    assert "NORMAL" in document["meshes"][0]["primitives"][0]["attributes"]
    assert len(document["meshes"]) == 1


def test_export_writes_glb_when_the_path_suffix_is_partial(tmp_path):
    """A staging name like kit.glb.partial must still be a glTF binary.

    trimesh picks the format from the last suffix, so `.partial` is not a format.
    """
    vertices, faces, uvs, texture, normals = _triangle()
    path = (tmp_path / "sample.glb").with_suffix(".glb.partial")
    export_pbr_glb(vertices, faces, uvs, texture, normals, path)
    data = path.read_bytes()
    assert data[:4] == b"glTF"
    length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20 : 20 + length])
    assert document["asset"]["version"] == "2.0"


def test_silhouette_accepts_the_same_shape():
    alpha = np.zeros((64, 64), dtype=np.uint8)
    alpha[8:56, 8:56] = 255
    vertices = np.array(
        [[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 2.0, 0.0], [-1.0, 2.0, 0.0]],
        dtype=np.float64,
    )
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    assert silhouette_iou(alpha, vertices, faces, ground=False) > 0.9


def test_kept_kits_are_not_ground_and_not_rebuilt_names():
    assert "rabbit" in SKIP
    assert "tree_branched" in SKIP
    assert SKIP.isdisjoint(GROUND)


def test_size_targets_match_the_committed_kits():
    import json
    from pathlib import Path

    targets = json.loads(Path("tools/kit_targets.json").read_text())
    glbs = {path.stem for path in Path("web/assets/kits").glob("*.glb")}
    assert set(targets) == glbs
    for name in GROUND:
        assert targets[name]["kind"] == "ground"
        assert targets[name]["footprint"] > 0
    assert targets["heron"] == {"kind": "standing", "height": 1.3}
    assert targets["pitcher"] == {"kind": "standing", "height": 1.6}
    assert targets["tree_tall"] == {"kind": "standing", "height": 14.0}
    for name in SKIP:
        assert targets[name]["kind"] == "standing"
