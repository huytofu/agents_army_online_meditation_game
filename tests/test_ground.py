import json
import subprocess

from forest_server.world.ground import ground_height

POINTS = ((0, 0), (10, -4), (-80, 120), (199, 199))


def test_node_ground_matches_python():
    completed = subprocess.run(
        ["node", "web/world/check_ground.mjs"],
        check=True,
        capture_output=True,
        text=True,
    )
    heights = json.loads(completed.stdout)
    for x, z in POINTS:
        assert abs(heights[f"{x},{z}"] - ground_height(x, z)) < 1e-9
