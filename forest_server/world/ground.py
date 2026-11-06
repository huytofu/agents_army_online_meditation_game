import math

from forest_server.world.constants import TERMS


def ground_height(x: float, z: float) -> float:
    return sum(a * math.sin(kx * x + kz * z + phase) for a, kx, kz, phase in TERMS)
