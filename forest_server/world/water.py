"""River ribbon samples. The gorge keeps its own pool and sheets."""

from forest_server.world.biomes import biome_at, chunk_index, river_z
from forest_server.world.ground import ground_height


def water_in_chunk(cx: int, cz: int) -> list[dict]:
    samples = []
    x = -2000.0
    while x <= 2000.0 + 1e-6:
        z = river_z(x)
        if chunk_index(x) == cx and chunk_index(z) == cz and biome_at(x, z) == "river":
            samples.append({"x": x, "y": ground_height(x, z) - 0.35, "z": z})
        x += 8.0
    return samples
