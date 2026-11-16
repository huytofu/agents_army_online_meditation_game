"""The rebuilt kit references are ready to feed to TripoSR. No model runs here."""

from PIL import Image

from tools.prepare_reference import (
    CANVAS,
    REFERENCE_DIR,
    SKIP,
    prepare_image,
    rebuild_names,
    reference_report,
)


def test_rebuilt_references_fill_the_frame():
    names = rebuild_names()
    assert len(names) == 38
    assert SKIP.isdisjoint(names)
    for name in names:
        report = reference_report(Image.open(REFERENCE_DIR / f"{name}.png"))
        assert report["has_alpha"], name
        assert 0.88 <= report["long_side_ratio"] <= 0.92, name
        assert report["components"] == 1, name
        assert report["margin"] >= 40, name
        assert report["center_offset"] < 3, name
        assert report["touches_frame"] is False, name


def test_prepare_image_cuts_a_gray_plate():
    image = Image.new("RGB", (800, 800), (198, 198, 198))
    pixels = image.load()
    for y in range(250, 550):
        for x in range(300, 620):
            pixels[x, y] = (180, 40, 40)
    prepared = prepare_image(image, "example")
    assert prepared.size == (CANVAS, CANVAS)
    assert prepared.mode == "RGBA"
    report = reference_report(prepared)
    assert report["has_alpha"]
    assert 0.88 <= report["long_side_ratio"] <= 0.92
    assert report["components"] == 1
    assert report["margin"] > 0
