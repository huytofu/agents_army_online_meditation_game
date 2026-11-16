"""Build one scatter-kit GLB from its committed reference image.

The game does not import this module. pytest does not run the model. Torch is
imported only after the reference check, inside ``main``.

    python tools/generate_kit_mesh.py heron
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.prepare_reference import (
    GROUND,
    REFERENCE_DIR,
    SKIP,
    reference_report,
)
KIT_DIR = ROOT / "web" / "assets" / "kits"
TARGETS_PATH = Path(__file__).resolve().parent / "kit_targets.json"
TRIPOSR_DIR = Path.home() / ".cache" / "forest-triposr"
TRIPOSR_REPO = "https://github.com/VAST-AI-Research/TripoSR.git"

MAX_TRIANGLES = 100_000
MARCHING_CUBES = 256
TEXTURE_RESOLUTION = 2048
CHUNK_SIZE = 8192
FOREGROUND_RATIO = 0.90
MIN_SUBJECT_RATIO = 0.88
SILHOUETTE_IOU = 0.25
SILHOUETTE_SIZE = 256

log = logging.getLogger("generate_kit_mesh")


def triposr_to_standing(points: np.ndarray) -> np.ndarray:
    """Map TripoSR axes onto glTF axes.

    Upstream cameras look along -X with image up as +Z and image right as +Y.
    ``(x, y, z) -> (y, z, x)`` sends image right to +X, image up to +Y, and
    the side facing the camera to +Z.
    """
    return np.stack([points[:, 1], points[:, 2], points[:, 0]], axis=1)


def triposr_to_ground(points: np.ndarray) -> np.ndarray:
    """Lay an overhead photo on the ground.

    Standing axes first, then -90 degrees about X: image up, which is +Y,
    becomes -Z, and the side that faced the camera faces +Y.
    """
    standing = triposr_to_standing(points)
    return np.stack([standing[:, 0], standing[:, 2], -standing[:, 1]], axis=1)


def seat_on_ground(points: np.ndarray) -> np.ndarray:
    out = np.array(points, dtype=np.float64, copy=True)
    out[:, 1] -= out[:, 1].min()
    return out


def center_xz(points: np.ndarray) -> np.ndarray:
    out = np.array(points, dtype=np.float64, copy=True)
    out[:, 0] -= (out[:, 0].min() + out[:, 0].max()) / 2
    out[:, 2] -= (out[:, 2].min() + out[:, 2].max()) / 2
    return out


def fit_standing(points: np.ndarray, height: float) -> np.ndarray:
    seated = seat_on_ground(center_xz(points))
    span = float(seated[:, 1].max())
    if span <= 1e-8:
        raise RuntimeError("mesh has no height")
    return seat_on_ground(center_xz(seated * (float(height) / span)))


def fit_ground(points: np.ndarray, footprint: float) -> np.ndarray:
    seated = seat_on_ground(center_xz(points))
    span = max(
        float(seated[:, 0].max() - seated[:, 0].min()),
        float(seated[:, 2].max() - seated[:, 2].min()),
    )
    if span <= 1e-8:
        raise RuntimeError("mesh has no footprint")
    return seat_on_ground(center_xz(seated * (float(footprint) / span)))


def pose_mesh(vertices: np.ndarray, normals: np.ndarray, name: str, target: dict):
    """Return world-space vertices and normals. Vertices stay in model space until bake."""
    if target["kind"] == "ground":
        turned = triposr_to_ground(vertices)
        turned_normals = triposr_to_ground(normals)
        fitted = fit_ground(turned, target["footprint"])
    elif target["kind"] == "standing":
        turned = triposr_to_standing(vertices)
        turned_normals = triposr_to_standing(normals)
        fitted = fit_standing(turned, target["height"])
    else:
        raise RuntimeError(f"unknown target kind for {name}")
    lengths = np.linalg.norm(turned_normals, axis=1, keepdims=True)
    lengths[lengths < 1e-8] = 1.0
    return fitted, turned_normals / lengths


def _normalize_points(xs: np.ndarray, ys: np.ndarray, size: int):
    span = max(float(xs.max() - xs.min()), float(ys.max() - ys.min()), 1e-8)
    scale = (0.90 * size) / span
    cx = (float(xs.min()) + float(xs.max())) / 2
    cy = (float(ys.min()) + float(ys.max())) / 2
    px = (xs - cx) * scale + size / 2
    py = (ys - cy) * scale + size / 2
    return px, py


def mask_from_alpha(alpha: np.ndarray, size: int = SILHOUETTE_SIZE) -> np.ndarray:
    subject = alpha > 32
    ys, xs = np.where(subject)
    if ys.size == 0:
        return np.zeros((size, size), dtype=bool)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    crop = subject[y0 : y1 + 1, x0 : x1 + 1]
    height, width = crop.shape
    scale = (0.90 * size) / max(height, width)
    resized = Image.fromarray((crop.astype(np.uint8) * 255)).resize(
        (max(1, int(round(width * scale))), max(1, int(round(height * scale)))),
        Image.Resampling.NEAREST,
    )
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return np.array(canvas) > 0


def project_mesh(vertices: np.ndarray, faces: np.ndarray, ground: bool, size: int = SILHOUETTE_SIZE) -> np.ndarray:
    """Silhouette. Standing uses X/Y with Y up. Ground uses X/Z with -Z up."""
    xs = vertices[:, 0]
    ys = vertices[:, 2] if ground else -vertices[:, 1]
    px, py = _normalize_points(xs, ys, size)
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    points = np.stack([px, py], axis=1)
    for face in faces:
        tri = points[face]
        draw.polygon([tuple(point) for point in tri], fill=1)
    return np.array(image) > 0


def mask_iou(left: np.ndarray, right: np.ndarray) -> float:
    union = np.logical_or(left, right).sum()
    if union == 0:
        return 0.0
    return float(np.logical_and(left, right).sum() / union)


def silhouette_iou(alpha: np.ndarray, vertices: np.ndarray, faces: np.ndarray, ground: bool) -> float:
    """Overlap of the reference alpha and the mesh silhouette, after both fill 90% of the frame.

    The mesh is also tried mirrored on X. TripoSR sometimes comes out that way,
    and a slab of the gray plate still fails both.
    """
    reference = mask_from_alpha(alpha)
    projected = project_mesh(vertices, faces, ground)
    return max(mask_iou(reference, projected), mask_iou(reference, projected[:, ::-1]))


def export_pbr_glb(vertices, faces, uvs, texture: Image.Image, normals, path: Path) -> None:
    """Write one mesh. baseColor is white, metal is 0, roughness is 1.

    ``SimpleMaterial.to_pbr()`` is not used: its default diffuse is gray and it
    omits metallicFactor, which glTF then treats as fully metal.
    """
    import trimesh
    from trimesh.visual import TextureVisuals
    from trimesh.visual.material import PBRMaterial

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices, dtype=np.float64),
        faces=np.asarray(faces, dtype=np.int64),
        vertex_normals=np.asarray(normals, dtype=np.float64),
        process=False,
    )
    mesh.visual = TextureVisuals(
        uv=np.asarray(uvs, dtype=np.float64),
        material=PBRMaterial(
            baseColorFactor=np.array([1.0, 1.0, 1.0, 1.0]),
            baseColorTexture=texture.convert("RGBA"),
            metallicFactor=0.0,
            roughnessFactor=1.0,
        ),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    # The staging file is "<name>.glb.partial". trimesh would read that last
    # suffix as the format name "partial" and refuse to write.
    mesh.export(path, file_type="glb")


def _ensure_python_headers() -> None:
    import sysconfig

    header = Path(sysconfig.get_path("include")) / "Python.h"
    if header.exists():
        return
    env = {**os_environ(), "DEBIAN_FRONTEND": "noninteractive"}
    subprocess.check_call(["sudo", "apt-get", "update"], env=env)
    subprocess.check_call(["sudo", "apt-get", "install", "-y", "python3-dev"], env=env)


def os_environ() -> dict:
    import os

    return dict(os.environ)


def _has_gpu() -> bool:
    import shutil

    return shutil.which("nvidia-smi") is not None


def _install_triposr(destination: Path) -> None:
    if not (destination / "tsr" / "system.py").exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            ["git", "clone", "--depth", "1", TRIPOSR_REPO, str(destination)]
        )
    requirements = destination / "requirements.txt"
    filtered = []
    mcubes = []
    for line in requirements.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Keep the environment's trimesh and Pillow. Downgrading trimesh changes
        # how metallicFactor is written, which is the bug this script exists to stop.
        if stripped.startswith(("trimesh", "Pillow", "gradio")):
            continue
        if "torchmcubes" in stripped:
            mcubes.append(stripped)
            continue
        filtered.append(stripped)
    filtered_path = destination / "requirements.forest.txt"
    # rembg is imported by TripoSR even when the reference is already cut out,
    # and that import requires an onnxruntime backend.
    filtered_path.write_text("\n".join(filtered) + "\nfast-simplification\nonnxruntime\n")
    # A machine with no GPU gets the CPU wheel. The default PyPI torch pulls
    # a CUDA toolkit this forest does not have. torchmcubes then has to see
    # that torch, so it is built without an isolated environment.
    torch_cmd = [sys.executable, "-m", "pip", "install", "torch"]
    if not _has_gpu():
        torch_cmd += ["--index-url", "https://download.pytorch.org/whl/cpu"]
    subprocess.check_call(torch_cmd)
    if mcubes:
        _ensure_python_headers()
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "scikit-build-core>=1.0",
                "pybind11>=2.10",
                "cmake",
                "ninja",
            ]
        )
    for spec in mcubes:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--no-build-isolation", spec]
        )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", str(filtered_path)]
    )


def _imports_ready() -> bool:
    try:
        import fast_simplification  # noqa: F401
        import torch  # noqa: F401
        import xatlas  # noqa: F401
    except ImportError:
        return False
    return (TRIPOSR_DIR / "tsr" / "system.py").exists()


def ensure_triposr() -> None:
    if not _imports_ready():
        _install_triposr(TRIPOSR_DIR)
    repo = str(TRIPOSR_DIR)
    if repo not in sys.path:
        sys.path.insert(0, repo)


def _load_reference(name: str) -> Image.Image:
    if name in SKIP:
        raise SystemExit(f"{name} is not rebuilt")
    path = REFERENCE_DIR / f"{name}.png"
    if not path.exists():
        raise SystemExit(f"missing reference {path}")
    image = Image.open(path).convert("RGBA")
    report = reference_report(image)
    if report["long_side_ratio"] < MIN_SUBJECT_RATIO:
        raise SystemExit(
            f"{name} subject fills {report['long_side_ratio']:.3f} of the frame, under {MIN_SUBJECT_RATIO}"
        )
    return image


def _load_target(name: str) -> dict:
    import json

    targets = json.loads(TARGETS_PATH.read_text())
    if name not in targets:
        raise SystemExit(f"{name} has no size in {TARGETS_PATH.name}")
    return targets[name]


def _preprocess(image: Image.Image) -> Image.Image:
    from tsr.utils import resize_foreground

    sized = resize_foreground(image, FOREGROUND_RATIO)
    array = np.array(sized).astype(np.float32) / 255.0
    rgb = array[:, :, :3] * array[:, :, 3:4] + (1.0 - array[:, :, 3:4]) * 0.5
    return Image.fromarray((rgb * 255.0).astype(np.uint8))


def _decimate(mesh):
    mesh.merge_vertices()
    faces = len(mesh.faces)
    if faces <= MAX_TRIANGLES:
        return mesh
    reduced = mesh.simplify_quadric_decimation(face_count=MAX_TRIANGLES)
    if len(reduced.faces) > MAX_TRIANGLES:
        raise RuntimeError(f"decimation left {len(reduced.faces)} triangles")
    return reduced


def _vertex_colors(mesh, model, scene_code, device: str) -> np.ndarray:
    import torch

    positions = torch.tensor(np.asarray(mesh.vertices), dtype=torch.float32, device=device)
    with torch.no_grad():
        queried = model.renderer.query_triplane(model.decoder, positions, scene_code)
    color = queried["color"].detach().float().cpu().numpy()
    return np.clip(color, 0.0, 1.0)


def _atlas(mesh):
    import xatlas

    atlas = xatlas.Atlas()
    atlas.add_mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32))
    options = xatlas.PackOptions()
    options.resolution = TEXTURE_RESOLUTION
    options.padding = round(max(2, TEXTURE_RESOLUTION / 256))
    options.bilinear = True
    atlas.generate(pack_options=options)
    vmapping, indices, uvs = atlas[0]
    return vmapping, indices, uvs


def _rasterize_colors(uvs, faces, colors, resolution: int) -> np.ndarray:
    image = np.zeros((resolution, resolution, 4), dtype=np.float32)
    px = np.clip(uvs[:, 0], 0.0, 1.0) * (resolution - 1)
    py = (1.0 - np.clip(uvs[:, 1], 0.0, 1.0)) * (resolution - 1)
    for face in faces:
        triangle = np.stack([px[face], py[face]], axis=1)
        color = colors[face]
        min_x = max(int(np.floor(triangle[:, 0].min())), 0)
        max_x = min(int(np.ceil(triangle[:, 0].max())), resolution - 1)
        min_y = max(int(np.floor(triangle[:, 1].min())), 0)
        max_y = min(int(np.ceil(triangle[:, 1].max())), resolution - 1)
        if max_x < min_x or max_y < min_y:
            continue
        xs = np.arange(min_x, max_x + 1)
        ys = np.arange(min_y, max_y + 1)
        grid_x, grid_y = np.meshgrid(xs, ys)
        points = np.stack([grid_x.ravel(), grid_y.ravel()], axis=1)
        bary = _barycentric(triangle, points)
        inside = (bary >= -1e-4).all(axis=1)
        if not inside.any():
            continue
        chosen = points[inside].astype(int)
        weights = bary[inside]
        painted = weights @ color
        image[chosen[:, 1], chosen[:, 0], :3] = painted
        image[chosen[:, 1], chosen[:, 0], 3] = 1.0
    return _dilate(image)


def _barycentric(triangle: np.ndarray, points: np.ndarray) -> np.ndarray:
    a, b, c = triangle
    v0 = b - a
    v1 = c - a
    v2 = points - a
    dot00 = float(np.dot(v0, v0))
    dot01 = float(np.dot(v0, v1))
    dot11 = float(np.dot(v1, v1))
    dot02 = v2 @ v0
    dot12 = v2 @ v1
    denom = dot00 * dot11 - dot01 * dot01
    if abs(denom) < 1e-12:
        return np.full((len(points), 3), -1.0)
    inv = 1.0 / denom
    beta = (dot11 * dot02 - dot01 * dot12) * inv
    gamma = (dot00 * dot12 - dot01 * dot02) * inv
    alpha = 1.0 - beta - gamma
    return np.stack([alpha, beta, gamma], axis=1)


def _dilate(image: np.ndarray) -> np.ndarray:
    from scipy import ndimage

    filled = image[:, :, 3] > 0
    if filled.all() or not filled.any():
        return image
    distance, indices = ndimage.distance_transform_edt(~filled, return_indices=True)
    padding = round(max(2, image.shape[0] / 256))
    copy = (~filled) & (distance <= padding)
    image[copy] = image[indices[0][copy], indices[1][copy]]
    return image


def _bake(mesh, model, scene_code, device: str):
    """Atlas after decimation, while vertices are still in TripoSR space."""
    try:
        from tsr.bake_texture import bake_texture

        baked = bake_texture(mesh, model, scene_code, TEXTURE_RESOLUTION)
        colors = np.clip(baked["colors"], 0.0, 1.0)
        texture = Image.fromarray((colors * 255.0).astype(np.uint8)).transpose(Image.FLIP_TOP_BOTTOM)
        vmapping = baked["vmapping"]
        return (
            np.asarray(mesh.vertices)[vmapping],
            baked["indices"],
            baked["uvs"],
            np.asarray(mesh.vertex_normals)[vmapping],
            texture,
        )
    except Exception as exc:
        log.warning("moderngl bake failed (%s); rasterizing vertex colors on the CPU", exc)
    colors = _vertex_colors(mesh, model, scene_code, device)
    vmapping, indices, uvs = _atlas(mesh)
    texture_f = _rasterize_colors(uvs, indices, colors[vmapping], TEXTURE_RESOLUTION)
    texture = Image.fromarray((np.clip(texture_f, 0.0, 1.0) * 255.0).astype(np.uint8))
    return (
        np.asarray(mesh.vertices)[vmapping],
        indices,
        uvs,
        np.asarray(mesh.vertex_normals)[vmapping],
        texture,
    )


def reconstruct(name: str) -> Path:
    reference = _load_reference(name)
    target = _load_target(name)
    alpha = np.array(reference)[:, :, 3]
    ensure_triposr()
    import torch
    from tsr.system import TSR

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(min(8, os_cpu_count()))
    log.info("loading TripoSR on %s", device)
    model = TSR.from_pretrained(
        "stabilityai/TripoSR",
        config_name="config.yaml",
        weight_name="model.ckpt",
    )
    model.renderer.set_chunk_size(CHUNK_SIZE)
    model.to(device)
    image = _preprocess(reference)
    with torch.no_grad():
        scene_codes = model([image], device=device)
    meshes = model.extract_mesh(scene_codes, has_vertex_color=False, resolution=MARCHING_CUBES)
    mesh = _decimate(meshes[0])
    log.info("%s triangles after decimation: %s", name, len(mesh.faces))
    vertices, faces, uvs, normals, texture = _bake(mesh, model, scene_codes[0], device)
    posed, posed_normals = pose_mesh(vertices, normals, name, target)
    ground = target["kind"] == "ground"
    overlap = silhouette_iou(alpha, posed, faces, ground)
    log.info("%s silhouette overlap %.3f", name, overlap)
    destination = KIT_DIR / f"{name}.glb"
    if overlap < SILHOUETTE_IOU:
        raise SystemExit(f"{name} silhouette overlap {overlap:.3f} is under {SILHOUETTE_IOU}")
    temporary = destination.with_suffix(".glb.partial")
    try:
        export_pbr_glb(posed, faces, uvs, texture, posed_normals, temporary)
        temporary.replace(destination)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return destination


def os_cpu_count() -> int:
    import os

    return os.cpu_count() or 1


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Rebuild one kit mesh with TripoSR")
    parser.add_argument("name", help="Kit name, such as heron")
    args = parser.parse_args()
    name = args.name.removesuffix(".glb")
    path = reconstruct(name)
    log.info("wrote %s", path)


if __name__ == "__main__":
    main()
