# Forest plans

Cloud agents read these files from the repository. Implement one phase file per agent, in order. Do not implement the master plan as a single build.

1. [01-walkable-grove.md](01-walkable-grove.md) — Postgres, port 8765, one walkable grove
2. [02-forest-catalog.md](02-forest-catalog.md) — 4000 m forest, scattered seat fields, twelve biomes, landmarks
3. [03-sit-and-video.md](03-sit-and-video.md) — sit, moving scene, private YouTube
4. [04-other-people.md](04-other-people.md) — stick figures, 5 m gap, first-come seats
5. [05-picture-holds.md](05-picture-holds.md) — silhouettes, chunk cleanup, two-browser visit

[00-master-plan.md](00-master-plan.md) is the shared design. Phase files are the build instructions. When they disagree, follow the phase file.

Start the next phase only after the previous phase is on the remote branch the new agent clones.
