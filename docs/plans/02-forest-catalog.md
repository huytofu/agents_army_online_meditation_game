---
name: Phase 2 Forest Catalog
overview: "Replace the prototype grove with a streamed 400 m forest: six biomes, a hex field of thousands of seats, a river, and four landmarks, all generated in Python."
todos:
  - id: p2-generate
    content: Biome map, hex spots, scatter, landmarks, and pure tests
    status: pending
  - id: p2-api
    content: Seed Postgres once and serve meta plus chunk JSON
    status: pending
  - id: p2-stream
    content: 3x3 chunk client, all kits, cushions, river, biome light
    status: pending
isProject: false
---

# Phase 2 Forest Catalog Implementation Plan

> **For agentic workers:** Implement this phase only. Phase 1 already walks a 96 m moss pad. Replace that pad with streamed chunks. Do not add sitting, YouTube, or other players.

**Goal:** Walk from the moss plain to the waterfall, the cathedral, the strange grove, and the valley ridge. Thousands of seat cushions exist. Only nearby chunks are in memory.

**Architecture:** Python is the only forest generator. `GET /api/world/meta` and `GET /api/world/chunks/{cx}/{cz}` return JSON. The client renders it. Spots are inserted once into this game's Postgres.

**Tech Stack:** The phase 1 server and Three.js client. Still no websocket.

## Global Constraints

- Keep phase 1 formulas and ports. `ground_height` stays the four-term sum. Speed `3.2`. Spawn `(-24, ground, 0)`.
- World square is `x,z` strictly inside `(-200, 200)`. Chunk size `64`. `chunk = floor((coord - (-200)) / 64)`. Legal indexes are `0..6`.
- Hex spots, spacing `8` m. Never nudge a point. Drop river-water points only.

```python
ROW_H = 8.0 * math.sqrt(3) / 2
z = -200 + (row + 0.5) * ROW_H
x = -196 + col * 8 + (4 if row % 2 else 0)
```

- Biomes, half-open on the low edges: `valley` x `[-200,0)` z `[67,200]`; `waterfall_gorge` x `[0,200]` z `[67,200]`; `moss_plain` x `[-200,0)` z `[-67,67)`; `river` x `[0,200]` z `[-67,67)`; `strange_fauna` x `[-200,0)` z `[-200,-67)`; `cathedral_trees` x `[0,200]` z `[-200,-67)`.
- `river_z(x) = 6*sin(x*0.035) + 2.5*sin(x*0.11)`. Skip a spot when its biome is `river` and `abs(z - river_z(x)) < 5`.
- Number kept points from `1` in row-major order (`row`, then `col`). `y = ground_height(x, z)`.
- `spot_seed = (WORLD_SEED + spot_id * 1013904223) & 0xFFFFFFFF`. Yaw = `(spot_seed % 3600) / 3600 * tau`. Archetype = `ARCHETYPES[biome][(spot_seed >> 8) % 4]`. Recipe RNG must not change these.
- Archetype names, four each: moss `dew_clearing`, `mushroom_ring`, `log_seat`, `mound_overlook`; cathedral `between_roots`, `shaft_clearing`, `hollow`, `vine_nave`; river `bank_stone`, `reed_pocket`, `shallow_bend`, `boulder_island_view`; waterfall `pool_ledge`, `mist_shelf`, `behind_sheet`, `gorge_floor`; valley `terrace_lip`, `flower_bowl`, `ridge_seat`, `amphitheater`; strange `spore_circle`, `spiral_cathedral`, `moth_lane`, `violet_hollow`.
- Expect 2500 to 3200 spots and at least 300 in every biome. Neighbor distance at least `7.99` m.

## Files

- Create: `forest_server/world/biomes.py`, `forest_server/world/spots.py`, `forest_server/world/scatter.py`, `forest_server/world/landmarks.py`, `forest_server/database/repository.py`, `forest_server/routers/world.py`, `web/js/meta.js`, `web/js/chunks.js`, `tests/test_spots.py`, `tests/test_scatter.py`
- Modify: `forest_server/app.py` (seed on startup, include the world router before the static mount), `web/js/main.js`, `web/js/kits/index.js`
- Leave `forest_server/world/recipes.py` for phase 3. This phase only chooses the archetype name.

## Task 1: Pure world generation

`biome_at(x, z) -> str` uses the rectangles above. A point on `x = 0` belongs to the east biome.

`generate_spots() -> list[Spot]` returns frozen spots with `id, biome, archetype, x, y, z, yaw, chunk_x, chunk_z`.

`tests/test_spots.py`:

- Count in `[2500, 3200]`, every biome `>= 300`, ids are `1..n` with no gaps.
- Calling `generate_spots()` twice returns equal tuples.
- For every spot, the nearest other spot is `>= 7.99`. Check the spot's chunk and the eight neighbors, not a blind all-pairs search only; either method is fine if the assertion is the distance.
- `biome_at(46, 150) == "waterfall_gorge"`, `biome_at(80, -140) == "cathedral_trees"`, `biome_at(-120, -140) == "strange_fauna"`, `biome_at(-150, 150) == "valley"`, `biome_at(-24, 0) == "moss_plain"`.
- Great-fall chunk is `(3, 5)`, cathedral heart and spore well are in `cz == 0`, west ridge chunk is `(0, 5)`. Compute with the chunk function and assert those indexes.

Scatter seed for a chunk: `(WORLD_SEED ^ (cx * 734287 + cz * 912367)) & 0xFFFFFFFF`, then the same mulberry32 as below. Use mulberry32 only inside scatter and landmarks, not to renumber spots.

```python
def mulberry32(seed: int):
    a = seed & 0xFFFFFFFF
    def next_f() -> float:
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        mixed = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
        t = (t ^ ((t + mixed) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return (t ^ (t >> 14)) / 4294967296
    return next_f
```

Each scatter item is a world-space block: `kit, variant, x, y, z, rot_y, scale, motion, motion_period, motion_amount`, plus `"space": "world"`. `y` is `ground_height(x, z)` plus a kit offset (`vine_strand` uses `2 + rng*6`; others use `0`).

Attempt placements until the counts below are accepted. Accept only when `biome_at` matches the kit's biome. Give up a single instance after 40 rejects.

- moss: tree 4 at scale `0.5`, moss_mound 40, fern 30, mushroom 16, dead_log 8, boulder 10
- cathedral: tree 12 at scale `1.6..2.4`, fern 20, vine_strand 8, boulder 6
- river: reed 30, river_stone 24, fern 10
- waterfall: cliff_wall 16, boulder 10, mist_card 8
- valley: wildflower 20, moss_mound 14, boulder 10, ridge_card 6
- strange: spiral_tree 10, spore 24, glow_moth 8, lantern_frog 6

`tests/test_scatter.py` checks a moss chunk and a cathedral chunk: kit names are in the allowed set, counts match, every instance's biome matches, and cathedral trees have scale `>= 1.6`.

Landmarks, world space, added on top of scatter for the chunk that contains the point:

- `(46, 150)` great fall: an arc of `cliff_wall`, three `waterfall_sheet` blocks whose scale means at least 8 m tall, one `pool_disc`, four `mist_card`
- `(80, -140)` cathedral heart: 7 `tree` at scale `2` on a 10 m radius
- `(-120, -140)` spore well: 12 `spore`, 6 `spiral_tree`
- `(-150, 150)` west ridge: 5 `ridge_card` with scale `>= 3`

Water samples: for `x` from `0` to `200` step `4`, `z = river_z(x)`, `y = ground_height(x, z) - 0.35`. A chunk payload includes the samples that fall inside it.

## Task 2: Persist spots and serve chunks

On startup, after migrate, if `COUNT(*) FROM spots` is `0`, insert `generate_spots()` in one transaction. A second startup does not insert again.

`GET /api/world/meta` returns extents, chunk size, spacing, exclusion `5`, sit range `2.5`, max speed, spawn, `TERMS`, biome rectangles, river coefficients, kit names, and the six palette groups from the art list (moss, cathedral, river, waterfall, valley, strange) with the hex colors already used in phase 1 plus river water `#6e9aa3`, stone `#8a8178`, reed `#7ea15a`, waterfall rock `#6d7270`, sheet `#c5ddd8`, mist `#ffffff`, valley grass `#8aaa62`, flowers `#d47aa6` and `#e6c85a`, ridge `#9aa7b0`, strange ground `#3a3550`, spiral `#6a4a78`, spore `#d7f28a`, moth `#f2c9ff`.

`GET /api/world/chunks/{cx}/{cz}` returns `{cx, cz, spots, scatter, landmarks, water}`. Unknown chunks return 404. Spots are the rows in that chunk only, without recipe blocks.

`/health` `spots` becomes the real count.

## Task 3: Stream the client

Extend `makeKit` for every kit name above. Shape rules:

- `dead_log`: a cylinder on its side
- `boulder` and `river_stone`: scaled icosahedra or spheres, stone `#8a8178`, boulder larger
- `reed` and `wildflower`: thin stems; flowers use both flower colors
- `vine_strand`: a thin vertical ribbon
- `cliff_wall`: a tall box, rock `#6d7270`
- `waterfall_sheet`: a double-sided transparent plane, opacity `0.45`, color `#c5ddd8`
- `mist_card` and `spore` and `glow_moth`: additive transparent sprites or planes
- `pool_disc`: a flat circle, water `#6e9aa3`, opacity `0.65`
- `ridge_card`: a tall unlit plane, `#9aa7b0`
- `spiral_tree`: a twisted stack of boxes, `#6a4a78`
- `lantern_frog`: a small body and four stumps, a dull green
- `seat_cushion`: a flat stone disc with a moss ring, radius about `0.7`

`web/js/chunks.js` keeps the chunk under the player and the eight around it. Dispose meshes that leave the window. Build one displaced ground per chunk (32 by 32 segments) and color vertices by `biome_at` using rectangles from meta. One `InstancedMesh` per kit per chunk. A seat cushion at every spot. Water samples in a chunk become a ribbon 9 m wide with a scrolling UV (`material.map` offset or `onBeforeCompile`; a simple `time` uniform is enough).

Replace the phase 1 single plane and the 40 hand-placed props. Spawn and controls stay.

When the player's biome changes, lerp fog color and density and the sun color over `1.2` s. Fixed preset per biome, not a day clock. Within 12 m of a rectangle border, add `0.01` to fog density.

Moss fog `#d5e2d2` density `0.018`. Cathedral fog `#9aa89a` density `0.028`. River `#d5e4e2` `0.016`. Waterfall `#d0ddd8` `0.02`. Valley `#e4ecf1` `0.012`. Strange `#6a6288` `0.03` and a darker clear color `#2a2440`.

Ferns, reeds, vines: sway in the vertex shader or by rotating the instance matrix with `0.07 * sin(time / 5)`. Moths circle. Sheets scroll. This motion is local decoration and must not wait for phase 3.

## Done when

- `pytest -q` and the ground node check still pass.
- `/health` reports a spot count inside `[2500, 3200]`.
- Reloading the process does not increase that count.
- From the spawn, a person can walk to all four landmarks and see the biome light change, the river ribbon, and cushions only for loaded chunks.

Commit once: the walkable forest and its seat catalog are in this database.