"""Cut the gray studio plate off a kit reference and scale the subject to 90%."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

CANVAS = 1024
FOREGROUND_RATIO = 0.90
# These four meshes stay as they are, and so do their photographs.
SKIP = frozenset({"rabbit", "spiral_tree", "tree_branched", "tree_broad"})
# Overhead photographs. The mesh script lays these flat; the picture stays overhead.
GROUND = frozenset(
    {"dirt_patch", "mud_patch", "grass_patch", "fallen_leaves", "water_puddle"}
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "web" / "assets" / "kits" / "references"


def rebuild_names() -> list[str]:
    names = sorted(path.stem for path in REFERENCE_DIR.glob("*.png"))
    return [name for name in names if name not in SKIP]


def _corner_color(rgb: np.ndarray) -> np.ndarray:
    patches = [
        rgb[:12, :12],
        rgb[:12, -12:],
        rgb[-12:, :12],
        rgb[-12:, -12:],
    ]
    samples = np.concatenate([patch.reshape(-1, 3) for patch in patches], axis=0)
    return np.median(samples, axis=0)


def _border_connected(candidates: np.ndarray) -> np.ndarray:
    labeled, _count = ndimage.label(candidates, structure=np.ones((3, 3), dtype=int))
    border_ids = np.unique(
        np.concatenate(
            [labeled[0, :], labeled[-1, :], labeled[:, 0], labeled[:, -1]]
        )
    )
    border_ids = border_ids[border_ids != 0]
    if border_ids.size == 0:
        return np.zeros(candidates.shape, dtype=bool)
    return np.isin(labeled, border_ids)


# The white mushroom's edge is barely stronger than the studio gray, so the
# flood has to stop at a weaker gradient than the other kits.
PALE_GRADIENT = {"mushroom_white": 1.2, "heron": 2.0}
DEFAULT_GRADIENT = 5.0
# The brown mushroom's glow is further from the corner gray than a pale leg.
DISTANCE = {"mushroom_brown": 78.0}
DEFAULT_DISTANCE = 62.0
# Plate trapped inside a ring. White petals sit further from the corner gray
# than this, so the flood does not eat them.
PLATE_DISTANCE = 32.0
# Flat pale pixels caught between bare branches. Bark is darker than this.
FLAT_LIGHT = {"tree_dead": (200.0, 18.0)}
# A soft gray shadow sealed under the body. The shell is darker and the lamp
# is saturated, so neither matches this band.
SOFT_SHADOW = frozenset({"beetle_lamp"})


def _gradient(rgb: np.ndarray) -> np.ndarray:
    image = rgb.astype(np.float32)
    gradient_y, gradient_x = np.gradient(image.mean(axis=2))
    return np.hypot(gradient_x, gradient_y)


def backdrop_mask(
    rgb: np.ndarray,
    gradient_max: float = DEFAULT_GRADIENT,
    distance_max: float = DEFAULT_DISTANCE,
) -> np.ndarray:
    """Border-connected studio gray, stopping at the subject's edge.

    A pixel is backdrop only when it is low-chroma, close to the corner gray,
    and the image gradient is too weak to be an outline. Saturated pixels and
    anything not connected to the frame stay, which keeps pale legs and beaks.
    """
    color = _corner_color(rgb).astype(np.float32)
    image = rgb.astype(np.float32)
    distance = np.linalg.norm(image - color, axis=2)
    chroma = image.max(axis=2) - image.min(axis=2)
    near = (_gradient(rgb) < gradient_max) & (distance < distance_max) & (chroma < 26)
    return _border_connected(near)


def drop_enclosed_plate(rgb: np.ndarray, subject: np.ndarray) -> np.ndarray:
    """Remove studio gray sealed inside a loop, such as the vine's center.

    A smooth pixel close to the corner gray is plate. Plate that touches the
    outside is the backdrop glow and is left for the border flood. Plate that
    the outside cannot reach is a hole, and it goes.
    """
    image = rgb.astype(np.float32)
    color = _corner_color(rgb).astype(np.float32)
    distance = np.linalg.norm(image - color, axis=2)
    chroma = image.max(axis=2) - image.min(axis=2)
    plate = subject & (_gradient(rgb) < 2.5) & (chroma < 14) & (distance < PLATE_DISTANCE)
    reached = _border_connected((~subject) | plate)
    return subject & ~(plate & ~reached)


def fill_small_holes(subject: np.ndarray, max_area: int = 180) -> np.ndarray:
    """Close pinholes left where a smooth pale patch met the studio gray.

    Real openings stay open: the vine loop, gaps in a bare crown, and the
    space between legs are all far larger than a pinhole.
    """
    labeled, count = ndimage.label(~subject, structure=np.ones((3, 3), dtype=int))
    if count == 0:
        return subject
    counts = np.bincount(labeled.ravel())
    border_ids = np.unique(
        np.concatenate(
            [labeled[0, :], labeled[-1, :], labeled[:, 0], labeled[:, -1]]
        )
    )
    border_ids = set(int(value) for value in border_ids if value != 0)
    fill = np.zeros(counts.shape, dtype=bool)
    for index, area in enumerate(counts):
        if index == 0 or index in border_ids:
            continue
        if area <= max_area:
            fill[index] = True
    if not fill.any():
        return subject
    filled = subject.copy()
    filled[fill[labeled]] = True
    return filled


def drop_flat_light(rgb: np.ndarray, subject: np.ndarray, luma_min: float, chroma_max: float) -> np.ndarray:
    image = rgb.astype(np.float32)
    luma = image.mean(axis=2)
    chroma = image.max(axis=2) - image.min(axis=2)
    return subject & ~((luma > luma_min) & (chroma < chroma_max))


def drop_soft_shadow(rgb: np.ndarray, subject: np.ndarray) -> np.ndarray:
    """Drop the pale contact shadow under the beetle.

    The lamp sits on the upper shell and is saturated, so the cut is limited
    to the lower part of the subject and to low-chroma pixels.
    """
    image = rgb.astype(np.float32)
    luma = image.mean(axis=2)
    chroma = image.max(axis=2) - image.min(axis=2)
    rows = np.where(subject)[0]
    if rows.size == 0:
        return subject
    y_cut = int(rows.min() + 0.62 * (rows.max() - rows.min()))
    shadow = np.zeros(subject.shape, dtype=bool)
    shadow[y_cut:] = True
    return subject & ~(shadow & (luma > 140) & (chroma < 20))


def _keep_subject(mask: np.ndarray) -> np.ndarray:
    labeled, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
    if count == 0:
        raise RuntimeError("reference has no subject")
    counts = np.bincount(labeled.ravel())
    counts[0] = 0
    largest = int(counts.max())
    keep = [
        index
        for index, area in enumerate(counts)
        if area >= max(64, int(0.02 * largest))
    ]
    return np.isin(labeled, keep)


def prepare_image(image: Image.Image, name: str | None = None) -> Image.Image:
    """Return a 1024 square RGBA image whose subject fills 90% of the long side."""
    rgba = np.array(image.convert("RGBA"))
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]
    if int(alpha.min()) < 255:
        subject = alpha > 16
    else:
        subject = ~backdrop_mask(
            rgb,
            PALE_GRADIENT.get(name or "", DEFAULT_GRADIENT),
            DISTANCE.get(name or "", DEFAULT_DISTANCE),
        )
        subject = drop_enclosed_plate(rgb, subject)
        flat = FLAT_LIGHT.get(name or "")
        if flat is not None:
            subject = drop_flat_light(rgb, subject, *flat)
        if (name or "") in SOFT_SHADOW:
            subject = drop_soft_shadow(rgb, subject)
        # Filling the dead tree's gaps puts the white plate back between twigs.
        if (name or "") not in FLAT_LIGHT:
            subject = fill_small_holes(subject)
    subject = _keep_subject(subject)
    ys, xs = np.where(subject)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    crop = rgba[y0 : y1 + 1, x0 : x1 + 1].copy()
    crop_subject = subject[y0 : y1 + 1, x0 : x1 + 1]
    crop[:, :, 3] = np.where(crop_subject, 255, 0).astype(np.uint8)
    height, width = crop.shape[:2]
    long_side = max(height, width)
    target = FOREGROUND_RATIO * CANVAS
    scale = target / long_side
    resized = Image.fromarray(crop, mode="RGBA").resize(
        (max(1, int(round(width * scale))), max(1, int(round(height * scale)))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    offset_x = (CANVAS - resized.width) // 2
    offset_y = (CANVAS - resized.height) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas


def reference_report(image: Image.Image) -> dict:
    """Measures a prepared reference. `long_side_ratio` is the subject's longer side over the frame."""
    rgba = np.array(image.convert("RGBA"))
    subject = rgba[:, :, 3] > 32
    labeled, count = ndimage.label(subject, structure=np.ones((3, 3), dtype=int))
    counts = np.bincount(labeled.ravel()) if count else np.array([0])
    if count:
        counts = counts.copy()
        counts[0] = 0
        largest = int(counts.max()) if counts.size else 0
        significant = int((counts >= max(64, int(0.02 * largest))).sum()) if largest else 0
    else:
        largest = 0
        significant = 0
    if largest == 0:
        return {
            "has_alpha": bool(rgba[:, :, 3].min() < 255),
            "long_side_ratio": 0.0,
            "components": 0,
            "margin": 0,
            "center_offset": CANVAS,
            "touches_frame": True,
        }
    ys, xs = np.where(labeled == int(np.argmax(counts)))
    # Include every significant component in the bbox, not only the largest.
    if significant > 1:
        keep = np.isin(labeled, np.flatnonzero(counts >= max(64, int(0.02 * counts.max()))))
        ys, xs = np.where(keep)
    height, width = subject.shape
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    long_side = max(y1 - y0 + 1, x1 - x0 + 1)
    margin = min(x0, y0, width - 1 - x1, height - 1 - y1)
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    return {
        "has_alpha": bool(rgba[:, :, 3].min() < 255),
        "long_side_ratio": long_side / max(width, height),
        "components": significant,
        "margin": int(margin),
        "center_offset": float(max(abs(center_x - (width - 1) / 2), abs(center_y - (height - 1) / 2))),
        "touches_frame": bool(margin <= 0),
    }


def prepare_directory(only: list[str] | None = None) -> list[str]:
    names = only or rebuild_names()
    written = []
    for name in names:
        if name in SKIP:
            raise SystemExit(f"{name} is not rebuilt")
        path = REFERENCE_DIR / f"{name}.png"
        prepared = prepare_image(Image.open(path), name)
        prepared.save(path)
        report = reference_report(prepared)
        print(
            f"{name} ratio={report['long_side_ratio']:.3f} "
            f"components={report['components']} margin={report['margin']}"
        )
        written.append(name)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare kit reference images for TripoSR")
    parser.add_argument("--only", nargs="*", help="Kit names to prepare. Default: every rebuilt kit.")
    args = parser.parse_args()
    prepare_directory(args.only)


if __name__ == "__main__":
    main()
