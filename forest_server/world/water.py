"""River ribbon samples. The gorge keeps its own pool and sheets."""

from forest_server.world.biomes import RIVER_SURFACE_LIFT, biome_at, chunk_index, river_z
from forest_server.world.ground import river_waterline

SAMPLE_STEP = 8.0


def river_samples() -> list[dict]:
    samples = []
    x = -2000.0
    while x <= 2000.0 + 1e-6:
        z = river_z(x)
        if biome_at(x, z) == "river":
            samples.append({"x": x, "y": river_waterline(x) + RIVER_SURFACE_LIFT, "z": z})
        x += SAMPLE_STEP
    return samples


def water_in_chunk(cx: int, cz: int) -> list[dict]:
    samples = river_samples()
    chosen = []
    for index, sample in enumerate(samples):
        in_chunk = chunk_index(sample["x"]) == cx and chunk_index(sample["z"]) == cz
        if in_chunk:
            chosen.append(sample)
            continue
        if index == 0:
            continue
        previous = samples[index - 1]
        previous_in_chunk = chunk_index(previous["x"]) == cx and chunk_index(previous["z"]) == cz
        # One step past this chunk closes the seam. A gorge gap is wider than one step.
        if previous_in_chunk and sample["x"] - previous["x"] <= SAMPLE_STEP + 1e-6:
            chosen.append(sample)
    return chosen
