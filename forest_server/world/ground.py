import math

from forest_server.world.biomes import RIVER_NECK, RIVER_SURFACE_LIFT, RIVER_WET, biome_at, river_z
from forest_server.world.constants import TERMS


def terrain_height(x: float, z: float) -> float:
    return sum(a * math.sin(kx * x + kz * z + phase) for a, kx, kz, phase in TERMS)


def river_waterline(x: float) -> float:
    """Uncarved height on the centerline. The sheet sits just above this."""
    return terrain_height(x, river_z(x))


def ground_height(x: float, z: float) -> float:
    base = terrain_height(x, z)
    center_z = river_z(x)
    lateral = abs(z - center_z)
    # The sheet follows the centerline, so the mouth can cross a gorge edge
    # while the center is still river. Carve that whole width.
    if lateral > RIVER_WET or biome_at(x, center_z) != "river":
        return base
    # Cosine bowl: neck-deep on the centerline, level with the waterline at the banks.
    t = lateral / RIVER_WET
    profile = 0.5 * (1.0 + math.cos(math.pi * t))
    return river_waterline(x) - (RIVER_NECK - RIVER_SURFACE_LIFT) * profile
