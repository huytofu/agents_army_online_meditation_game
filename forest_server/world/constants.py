"""World numbers shared by later phases. Terrain terms never use the seed."""

from forest_server.config import get_settings

TERMS = (
    (1.6, 0.020, 0.0, 1.7),
    (1.1, 0.0, 0.017, 0.4),
    (0.45, 0.050, 0.050, 0.0),
    (0.25, 0.090, 0.030, 0.0),
)

WORLD_MIN = -200.0
WORLD_MAX = 200.0
CHUNK_SIZE = 64.0
SPOT_SPACING = 8.0
EXCLUSION_M = 5.0
SIT_RANGE_M = 2.5
MAX_SPEED = 3.2
EYE_HEIGHT = 1.55
THIRD_DISTANCE = 4.2
THIRD_HEIGHT = 1.8
SPAWN_X = -24.0
SPAWN_Z = 0.0
WORLD_SEED = get_settings().world_seed
