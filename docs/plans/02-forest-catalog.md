---
name: Phase 2 Forest Catalog
overview: "Replace the prototype grove with a streamed 4000 m forest: twelve biomes, a river corridor, thirteen hex clearings, isolated seats, and twelve landmarks. Python places them. Offline open 3D models sculpt the unusual meshes."
todos:
  - id: p2-generate
    content: Biome map, seat fields, isolated seats, scatter, landmarks, and pure tests
    status: pending
  - id: p2-api
    content: Seed Postgres once and serve meta plus chunk JSON
    status: pending
  - id: p2-meshes
    content: Offline WorldClaw-style meshes for unusual kits and landmarks, with procedural fallback
    status: pending
  - id: p2-stream
    content: 3x3 chunk client, kits, committed glTFs, cushions, river, biome light
    status: pending
isProject: false
---

# Phase 2 Forest Catalog Implementation Plan

> **For agentic workers:** Implement this phase only. Phase 1 already walks a 96 m moss pad. Replace that pad with streamed chunks. Do not add sitting, YouTube, or other players.

**This file replaces the phase 2 section of `00-master-plan.md`.** The master plan still says a 400 m square, one hex of thousands of seats, six biomes, and no glTF. Ignore those decisions. When the two files disagree, follow this file. Do not rename phase 1's ground terms, ports, speed, spawn, token rules, or the 5 m exclusion constant. Do not replace `ground_height` with a generated height field.

**Goal:** A person can walk out of the moss spawn, cross a river, and enter a different biome without a reload. Seat cushions appear in scattered clearings of a few hundred seats, and as single cushions in quiet places. They do not carpet the map.

**Architecture:** Python is the only forest generator for layout. It decides biomes, the river, seats, scatter points, and landmark anchors, and serves them as JSON. An offline 3D model, used the way [Hunyuan3D-WorldClaw](https://github.com/Tencent-Hunyuan/Hunyuan3D-WorldClaw) does, sculpts the unusual kit and landmark meshes before the game runs. The browser renders the JSON plus those committed files. It does not keep a second copy of the biome map, and it does not call a model. Spots are inserted once into this game's Postgres.

**Tech Stack:** The phase 1 server and Three.js client, plus committed glTF for the meshes named below. Still no websocket. The play server never loads PyTorch, Blender, or a GPU model.

## Decisions this phase locks

- The forest is a square **4000 m on a side**, `x` and `z` from `-2000` to `2000`. The old `-200..200` square is retired.
- Seats are **not** one world-sized hex lattice. There are **13 clearings**. Each clearing is its own hex field of a few hundred seats. **59 isolated seats** sit far from those clearings and far from each other.
- Biomes are the twelve regions below. The river is a **corridor** along a curve, not a rectangle. It cuts through the rectangles and ends in the waterfall gorge.
- Plants come in two opposing sets: carnivorous kits live in the bog, and the flower valley, fern sea, and moss plain do not use them. Animals are meshes with local motion. They are not AI, not physics bodies, and not players.
- Landmark and scatter variety is the product of this phase. The weird plants, animals, and landmark sculptures come from an offline open 3D generator. Seats, the river curve, and the ground formula do not.
- Sitting, recipes, and other people stay in later phases. Archetype **names** are chosen here so phase 3 can attach recipes without renaming spots.

## Global Constraints

- Keep phase 1 `ground_height` terms, `3.2` m/s, spawn `(-24, ground_height(-24, 0), 0)`, port `8765`, and Postgres on `127.0.0.1:5436`.
- Change `WORLD_MIN` and `WORLD_MAX` in `forest_server/world/constants.py` to `-2000` and `2000`. The walker clamp becomes `[-1996, 1996]`. Delete the phase 1 clamp to the 96 m pad.
- Chunk size stays `64`. `chunk = floor((coord - (-2000)) / 64)`. Legal indexes are `0..62`. A coordinate of `-2000` is chunk `0`. A coordinate of `1999.9` is chunk `62`.
- One unit is one meter. Y is up. Yaw `0` looks toward `+Z`.
- Hex spacing inside a clearing is `8` m. Never nudge a point. Drop it or keep it.
- `spot_seed = (WORLD_SEED + spot_id * 1013904223) & 0xFFFFFFFF`. Yaw = `(spot_seed % 3600) / 3600 * tau`. Archetype = `ARCHETYPES[biome][(spot_seed >> 8) % 4]`. The acceptance hash for isolated seats must not change yaw or archetype.
- Field seats: **4197**. Isolated seats: **59**. Total spots: **4256**. Ids are `1..4256` with no gaps.
- Neighbor distance inside one clearing is at least `7.99` m. Isolated seats are at least `220` m from each other and at least `field radius + 80` m from every clearing center.

## Map

Rectangles tile the square. A band owns `z` from its minimum inclusive to its maximum exclusive, except the north band, which also owns `z = 2000`. Inside a band, a column owns `x` the same way, and the east column also owns `x = 2000`.

```text
z = 2000
  valley_bloom          hanging_vines         waterfall_gorge
  x [-2000, -400)       x [-400, 800)         x [800, 2000]
z = 800
  moss_plain                                  lantern_orchard
  x [-2000, 400)                              x [400, 2000]
z = -200
  fern_sea              carnivorous_bog       amber_herd
  x [-2000, -200)       x [-200, 1100)        x [1100, 2000]
z = -1100
  strange_fauna         cathedral_trees       salt_mirror
  x [-2000, 200)        x [200, 1400)         x [1400, 2000]
z = -2000
```

Spawn `(-24, 0)` is in `moss_plain`.

The river is drawn on top of those rectangles:

```python
def river_z(x: float) -> float:
    return (
        0.55 * x
        + 280
        + 60 * math.sin(x * 0.0018)
        + 22 * math.sin(x * 0.006)
    )
```

`biome_at(x, z)`:

1. Find the rectangle biome.
2. If that biome is `waterfall_gorge` and `abs(z - river_z(x)) <= 90`, return `waterfall_gorge`. The falls keep the river.
3. Else if `abs(z - river_z(x)) < 55`, return `river`.
4. Else return the rectangle biome.

The wet channel is the middle `16` m, `abs(z - river_z(x)) < 16`. No seat is placed there. The water ribbon uses that channel. The wider `55` m corridor is the river biome: reeds, stones, herons, bank seats.

`biome_at(0, river_z(0))` is `river`. `biome_at(1600, river_z(1600))` is `waterfall_gorge`. `biome_at(-24, 0)` is `moss_plain`.

## Files

- Create: `forest_server/world/biomes.py`, `forest_server/world/spots.py`, `forest_server/world/scatter.py`, `forest_server/world/landmarks.py`, `forest_server/database/repository.py`, `forest_server/routers/world.py`, `web/js/meta.js`, `web/js/chunks.js`, `web/js/kits/plants.js`, `web/js/kits/carnivores.js`, `web/js/kits/animals.js`, `web/js/kits/terrain.js`, `web/js/kits/gltf.js`, `web/assets/PROMPTS.md`, `tests/test_spots.py`, `tests/test_scatter.py`, `tests/test_assets.py`
- Modify: `forest_server/world/constants.py` (world extents only), `forest_server/app.py` (seed on startup, include the world router before the static mount), `web/js/main.js`, `web/js/kits/index.js`, `web/js/kits/materials.js`
- Commit generated files only after they pass the mesh rules below: `web/assets/kits/<name>.glb`, `web/assets/landmarks/<name>.glb`, and a copy of the generator license if that license requires it.
- Vendor Three.js r170 `GLTFLoader` and every local file it imports under `web/vendor/`. The import map points at those files. Do not fetch them from a CDN when the page loads.
- Leave `forest_server/world/recipes.py` for phase 3. This phase only stores the archetype name.

`makeKit` stays the only public kit constructor. The new kit modules are implementation files that `index.js` calls.

## Task 1: Pure world generation

### Archetypes

Four names per biome. Phase 3 will build recipes for these exact strings. Do not rename the six original sets.

- `moss_plain`: `dew_clearing`, `mushroom_ring`, `log_seat`, `mound_overlook`
- `cathedral_trees`: `between_roots`, `shaft_clearing`, `hollow`, `vine_nave`
- `river`: `bank_stone`, `reed_pocket`, `shallow_bend`, `boulder_island_view`
- `waterfall_gorge`: `pool_ledge`, `mist_shelf`, `behind_sheet`, `gorge_floor`
- `valley_bloom`: `terrace_lip`, `flower_bowl`, `ridge_seat`, `amphitheater`
- `strange_fauna`: `spore_circle`, `spiral_cathedral`, `moth_lane`, `violet_hollow`
- `carnivorous_bog`: `pitcher_ring`, `sundew_jewel`, `maw_clearing`, `acid_cup_seat`
- `lantern_orchard`: `glow_fruit`, `glass_aisle`, `moth_orchard`, `lantern_root`
- `fern_sea`: `fiddle_bowl`, `staghorn_nave`, `fern_tunnel`, `curl_overlook`
- `hanging_vines`: `root_swing`, `epiphyte_balcony`, `loris_perch`, `curtain_gap`
- `amber_herd`: `grazer_shade`, `seed_ring`, `dust_bowl`, `bird_perch`
- `salt_mirror`: `crust_lip`, `pink_pool`, `crystal_seat`, `brine_hollow`

There is no biome id `valley`. The old valley archetypes now belong to `valley_bloom`.

### Seat clearings

Each clearing is a hex disk. `ROW_H = 8 * sqrt(3) / 2`. Row `0` is the center row and does not stagger. Use Python's `%`, so negative odd rows stagger by `4`.

```python
z = center_z + row * ROW_H
x = center_x + col * 8 + (4 if row % 2 else 0)
```

Search `row` and `col` from `-n` to `n` inclusive, where `n` is `int(radius / ROW_H) + 2` for rows and `int(radius / 8) + 2` for columns. Keep a point when all of these are true:

- distance to the center is `<= radius`
- `x` and `z` are strictly inside `(-2000, 2000)`
- `abs(z - river_z(x)) >= 16`
- `biome_at(x, z)` equals the clearing's biome

Order points by `row`, then `col`. Do not sort after the fact in a different order.

| Field | Biome | x | z | Radius | Seats |
| --- | --- | ---: | ---: | ---: | ---: |
| dew_camp | moss_plain | -1100 | 200 | 76 | 313 |
| mushroom_yard | moss_plain | -400 | 500 | 70 | 283 |
| bloom_bowl | valley_bloom | -1200 | 1400 | 84 | 397 |
| petal_steps | valley_bloom | -700 | 1650 | 72 | 301 |
| vine_loft | hanging_vines | 200 | 1500 | 74 | 313 |
| fall_ledge | waterfall_gorge | 1400 | 1600 | 68 | 253 |
| fern_hollow | fern_sea | -1200 | -700 | 80 | 367 |
| bog_ring | carnivorous_bog | 400 | -700 | 76 | 313 |
| herd_shade | amber_herd | 1550 | -600 | 78 | 349 |
| orchard_glow | lantern_orchard | 1200 | 300 | 82 | 379 |
| spore_camp | strange_fauna | -1200 | -1550 | 74 | 313 |
| nave_roots | cathedral_trees | 700 | -1550 | 80 | 363 |
| mirror_shelf | salt_mirror | 1700 | -1550 | 66 | 253 |

The river biome has no clearing. Bank seats are the isolated ones that happen to land in the corridor but outside the wet channel.

### Isolated seats

Grid coordinates are `-1800 + 220 * i` for `i` in `0..16` inclusive. The last value is `1720`. Enumerate `x` from west to east as `ix` starting at `0`, and for each `x` enumerate `z` from south to north as `iz` starting at `0`.

Keep `(x, z)` when:

- `abs(z - river_z(x)) >= 16`
- distance to every clearing center is `> radius + 80`
- `(WORLD_SEED ^ (ix * 73856093) ^ (iz * 19349663)) & 0xFFFFFFFF` modulo `100` is `< 22`

That keep set has **59** points. Their minimum separation is `220` m.

### Ids, yaw, height

Assign ids after both sets exist. Clearings in the table order, points inside a clearing in row-then-col order, then isolated seats in `ix`, `iz` order. `y = ground_height(x, z)`. Chunk indexes use the formula above.

`tests/test_spots.py`:

- Field counts match the table. Isolated count is `59`. Total is `4256`. Ids are `1..4256`.
- Two calls to `generate_spots()` return equal tuples.
- Every clearing's nearest neighbor is `>= 7.99`. Check within the clearing, not against other clearings.
- Every isolated seat is `>= 220` m from every other seat and `> radius + 80` from every clearing center.
- No spot has `abs(z - river_z(x)) < 16`.
- `biome_at(-24, 0) == "moss_plain"`.
- `biome_at(0, river_z(0)) == "river"`.
- `biome_at(1600, river_z(1600)) == "waterfall_gorge"`.
- Clearing centers have the biomes in the table.
- Great fall chunk is `(54, 50)`, cathedral heart is `(43, 6)`, spore well is `(9, 6)`, dew camp center is `(14, 34)`, heron bend anchor `(-800, river_z(-800))` is chunk `(18, 28)`.

### Scatter

Scatter seed for a chunk: `(WORLD_SEED ^ (cx * 734287 + cz * 912367)) & 0xFFFFFFFF`, then the same mulberry32 as the master plan. Use it only for scatter and landmarks.

For every biome whose rectangle or river corridor intersects the chunk, try to place that biome's counts. Pick a candidate uniformly inside the chunk. Accept it only when `biome_at` equals that biome. Give up one instance after `40` rejects. A border chunk may therefore be short. An interior chunk should hit the full count.

Each item is a world-space block: `kit, variant, x, y, z, rot_y, scale, motion, motion_period, motion_amount`, plus `"space": "world"`. `y` is `ground_height(x, z)` plus a kit offset. `vine_strand`, `vine_noose`, and `epiphyte` use `2 + rng * 6`. Others use `0`.

Default motion, overridden only when a landmark says otherwise:

- `fern`, `reed`, `fiddlehead`, `staghorn`, `vine_strand`, `seed_head`, `wildflower`, `epiphyte`: sway `0.07`, period `5`
- `glow_moth`: `path_circle` amount `1.4`, period `12`
- `dragonfly`: drift `0.8`, period `6`
- `kite_bird`: drift `1.2`, period `9`
- `lantern_frog`, `brine_skipper`: hop `0.35`, period `6`
- `grazer`: bob `0.08`, period `4`
- `heron`: sway `0.04`, period `7`
- `loris`: bob `0.12`, period `5`
- `snap_maw`: sway `0.15`, period `8`
- `waterfall_sheet`, `rainbow_card`: `uv_scroll` amount `0.2`, period `4`
- `spore`, `glass_leaf`, `beetle_lamp`, `mist_card`: bob `0.25`, period `6`
- `pitcher`: sway `0.03`, period `9`

Counts per biome:

- moss: tree `3` at scale `0.5..0.8`, moss_mound `28`, fern `18`, mushroom `14`, dead_log `6`, cushion_moss `10`
- cathedral: tree `10` at scale `1.6..2.4`, fern `12`, vine_strand `8`, boulder `4`
- river: reed `22`, river_stone `16`, lily_pad `8`, dragonfly `4`, heron `1`
- waterfall: cliff_wall `14`, boulder `8`, mist_card `10`, rainbow_card `3`
- valley_bloom: wildflower `36`, blossom_tree `6`, seed_head `8`, kite_bird `3`, moss_mound `6`
- carnivorous_bog: pitcher `16`, sundew `18`, snap_maw `8`, vine_noose `6`, acid_cup `6`, bone_rib `4`
- strange: spiral_tree `8`, spore `20`, glow_moth `8`, lantern_frog `6`, beetle_lamp `6`
- lantern_orchard: blossom_tree `8`, glass_leaf `16`, beetle_lamp `8`, glow_moth `10`, seed_head `6`
- fern_sea: fern `40`, fiddlehead `16`, staghorn `10`, tree `2` at scale `0.6`
- hanging_vines: vine_strand `18`, epiphyte `14`, blossom_tree `4`, loris `5`, cliff_wall `4`
- amber_herd: seed_head `16`, grazer `5`, kite_bird `4`, wildflower `10`, boulder `4`
- salt_mirror: salt_crust `16`, crystal_shard `12`, pool_disc `4`, brine_skipper `10`, bone_rib `3`

Carnivorous kit names are only `pitcher`, `sundew`, `snap_maw`, `vine_noose`, `acid_cup`. They are legal in `carnivorous_bog` only.

`tests/test_scatter.py`:

- The chunk containing `(-1100, 200)` is all moss counts, and every instance's biome is `moss_plain`.
- The chunk containing `(700, -1550)` is the cathedral set, and every tree scale is `>= 1.6`.
- The chunk containing `(400, -700)` includes at least one `pitcher` and no `wildflower`, `blossom_tree`, `fern`, or `mushroom`.
- The chunk containing `(-1200, 1400)` includes `wildflower` and no carnivorous kit.

### Landmarks

World-space blocks added to the chunk that contains the anchor. They are not spots.

- `(1500, 1250)` great fall, `waterfall_gorge`: an arc of `cliff_wall`, four `waterfall_sheet` blocks whose scale means at least `8` m tall, one `pool_disc`, six `mist_card`, two `rainbow_card`.
- `(800, -1600)` cathedral heart: `7` trees at scale `2.2` on a `14` m radius.
- `(-1400, -1600)` spore well: `14` spore, `8` spiral_tree, `6` glow_moth.
- `(-1500, 1700)` bloom ridge, `valley_bloom`: `7` ridge_card at scale `>= 3`, a ring of `wildflower`, `4` kite_bird.
- `(500, -800)` pitcher throne: `9` pitcher, one of them at scale `>= 4`, `8` sundew, `4` snap_maw, one `acid_cup`.
- `(1500, 400)` lantern monarch: one `blossom_tree` at scale `>= 3.2`, a ring of `glass_leaf`, `8` glow_moth.
- `(1750, -1500)` mirror pan: one `pool_disc` at scale `>= 14`, a ring of `salt_crust`, `8` crystal_shard, `6` brine_skipper.
- `(-800, river_z(-800))` heron bend: `3` heron, an arc of `reed`, `6` river_stone, `4` dragonfly.
- `(100, 1600)` vine gate: two `cliff_wall` posts, a curtain of `vine_strand` between them, `6` epiphyte, `4` loris.
- `(1600, -700)` amber circle: `6` grazer turned inward, a ring of `seed_head`, `3` kite_bird.
- `(-1400, -650)` fern nave: two rows of `staghorn` and `fern`, at least `12` fern and `6` staghorn, plus `8` fiddlehead. No solid kit within `1.2` m of the anchor, so the nave reads as a path.
- `(200, -500)` sundew jewel: one `sundew` at scale `>= 3.5`, a ring of smaller sundew, `4` crystal_shard.

Water samples: `x` from `-2000` to `2000` step `8`, `z = river_z(x)`, `y = ground_height(x, z) - 0.35`. A chunk includes a sample only when the sample lies in that chunk and `biome_at` is `river`. The gorge draws its water as the landmark pool and sheets, not as this ribbon.

## Task 2: Persist spots and serve chunks

On startup, after migrate, if `COUNT(*) FROM spots` is `0`, insert `generate_spots()` in one transaction. A second startup does not insert again.

`GET /api/world/meta` returns:

- extents `-2000` and `2000`, chunk size, spacing `8`, exclusion `5`, sit range `2.5`, max speed, spawn
- ground `TERMS`
- the rectangle table and the river coefficients `0.55`, `280`, sines `(60, 0.0018)` and `(22, 0.006)`, corridor `55`, wet channel `16`
- every kit name, and the airy list: `mist_card`, `spore`, `glow_moth`, `waterfall_sheet`, `vine_strand`, `dragonfly`, `kite_bird`, `brine_skipper`, `rainbow_card`, `glass_leaf`, `beetle_lamp`
- the twelve palettes below, plus river

Palettes are fog, sun, and the colors the kits actually use:

- moss: fog `#d5e2d2` density `0.018`, sun `#ffe0b0`, ground `#6f8f62`, moss `#3e6b45`, cap `#c4554a`, stem `#efe6d4`
- cathedral: fog `#9aa89a` density `0.028`, sun `#f3e2b8`, trunk `#4a382c`, canopy `#1d3328`
- river: fog `#d5e4e2` density `0.016`, sun `#ffe0b0`, water `#6e9aa3`, stone `#8a8178`, reed `#7ea15a`
- waterfall: fog `#d0ddd8` density `0.02`, sun `#f4f0e4`, rock `#6d7270`, sheet `#c5ddd8`, mist `#ffffff`, rainbow `#f2c9ff`
- valley_bloom: fog `#f3e4ef` density `0.012`, sun `#ffe0b0`, grass `#8aaa62`, flowers `#d47aa6`, `#e6c85a`, `#7ec8e3`, ridge `#9aa7b0`
- strange: fog `#6a6288` density `0.03`, clear `#2a2440`, sun `#d7c4f2`, ground `#3a3550`, spiral `#6a4a78`, spore `#d7f28a`, moth `#f2c9ff`
- carnivorous_bog: fog `#c8d2a4` density `0.026`, clear `#3e4630`, sun `#e6d48a`, pitcher `#6f8f3a`, throat `#c4554a`, acid `#d6e25a`, bone `#efe6d4`
- lantern_orchard: fog `#f7e2b0` density `0.014`, sun `#ffe0b0`, blossom `#e25b8a` and `#f2c14e`, glass `#7ee0c8` and `#f2a3c7`, lamp `#d7f28a`
- fern_sea: fog `#d5e6cf` density `0.02`, sun `#ffe8c4`, fern `#3e6b45`, staghorn `#7ea15a`
- hanging_vines: fog `#d7e4c8` density `0.022`, sun `#ffe0b0`, vine `#3e6b45`, epiphyte `#c4554a`, eye `#f2c9ff`
- amber_herd: fog `#f0ddb8` density `0.014`, sun `#ffd39a`, hide `#c47a3a`, seed `#e6c85a`, bird `#e25b4a`
- salt_mirror: fog `#f4efe6` density `0.01`, clear `#efe8dc`, sun `#fff6e8`, crust `#efe6d4`, crystal `#d7f0ff`, pool `#e7a0b4`

`GET /api/world/chunks/{cx}/{cz}` returns `{cx, cz, spots, scatter, landmarks, water}`. Indexes outside `0..62` return `404`. Spots in that chunk do not include recipe blocks.

`/health` `spots` becomes `4256`.

## Task 3: Offline meshes for biomes and landmarks

Use the WorldClaw pattern, not a live model. [Hunyuan3D-WorldClaw](https://github.com/Tencent-Hunyuan/Hunyuan3D-WorldClaw) (paper [arXiv:2608.05248](https://arxiv.org/abs/2608.05248)) plans a scene from one text prompt, builds a terrain, then reconstructs editable textured meshes and places them on that terrain. This phase keeps the terrain, seats, and placement in Python. The model only sculpts meshes.

The public WorldClaw repository currently contains the paper announcement and assets. It does not contain source, weights, an install command, or a license. Do not block this phase on cloning it and expecting it to run. Do not vendor an unofficial reimplementation.

Generator order:

1. If Tencent has published WorldClaw code and a license that allows committing the outputs in this repo, use that pipeline for the prompts below.
2. Otherwise use a released open Hunyuan3D image-to-3D model. The WorldClaw paper refines object meshes with Hunyuan3D. The public weights for that step are [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2), under the Tencent Hunyuan 3D 2.0 Community License. That license does not cover the European Union, the United Kingdom, or South Korea, and distributing the weights has notice rules. Read the license before committing a mesh. Tencent's text says outputs by themselves are not model derivatives, and that Tencent claims no rights in outputs you generate. If the license still forbids committing the file, skip the file and keep the procedural builder.
3. If no licensed generator is available, ship the procedural builders and write the reason in `web/assets/PROMPTS.md`. The walk must still work.

How to run it, once, on a machine with a GPU. Not in `pytest`, not in uvicorn, not in the browser:

- One prompt, one object. The prompt may not ask for a forest map, a river, or seats. Those already exist.
- Make a single object on a plain background, then run image-to-3D. Export one glTF binary, Y-up, base on `y = 0`, 1 unit = 1 meter, at the unscaled size named in the kit and landmark sections. The chunk `scale` field multiplies that file.
- A scatter kit used more than ten times in one chunk must be a single geometry and a single material, at most `5000` triangles, with one albedo at most `1024` px. Merge parts before commit so `InstancedMesh` can draw it.
- A landmark file may be a group, at most `80000` triangles, textures at most `2048` px. Only one copy of each landmark is drawn.
- No skeleton and no embedded clip. Sway, bob, hop, and scroll stay in the client and move the whole instance.
- Write the prompt, the generator name, and the revision into `web/assets/PROMPTS.md` next to the filename.

Kits that should be generated when a generator is available: `pitcher`, `sundew`, `snap_maw`, `acid_cup`, `vine_noose`, `spiral_tree`, `blossom_tree`, `glass_leaf`, `staghorn`, `fiddlehead`, `epiphyte`, `heron`, `grazer`, `loris`, `dragonfly`, `kite_bird`, `glow_moth`, `lantern_frog`, `beetle_lamp`, `brine_skipper`.

Kits that stay code, because they repeat or they are the ground language: `moss_mound`, `mushroom`, `fern`, `tree`, `cushion_moss`, `dead_log`, `boulder`, `river_stone`, `reed`, `wildflower`, `seed_head`, `lily_pad`, `vine_strand`, `cliff_wall`, `waterfall_sheet`, `mist_card`, `pool_disc`, `ridge_card`, `rainbow_card`, `spore`, `crystal_shard`, `salt_crust`, `bone_rib`, `seat_cushion`.

Landmark files, one each, named `great_fall`, `cathedral_heart`, `spore_well`, `bloom_ridge`, `pitcher_throne`, `lantern_monarch`, `mirror_pan`, `heron_bend`, `vine_gate`, `amber_circle`, `fern_nave`, `sundew_jewel`. The Python block list still exists and is still what the chunk JSON and the tests assert. If the glTF loaded, the client draws the file at the anchor and does not also draw those blocks. If it did not load, the client draws the blocks.

Prompts, used as written:

- `pitcher`: a single carnivorous pitcher plant, 1.6 m tall, green vase `#6f8f3a`, red throat `#c4554a`, one lid, no ground
- `sundew`: a low sundew, pink stalks, pale sticky drops, no pot
- `snap_maw`: one open snap trap, red lobes, pale inner mouth, no ground
- `acid_cup`: a low cup of yellow-green liquid, translucent, no ground
- `vine_noose`: one hanging purple vine loop, no tree
- `spiral_tree`: one twisted spiral trunk, `#6a4a78`, no forest
- `blossom_tree`: one small tree with pink and gold blossom spheres, no ground
- `glass_leaf`: one translucent leaf, teal and pink, no stem forest
- `staghorn`: one staghorn fern, flat antlers, `#7ea15a`
- `fiddlehead`: one green fern crozier
- `epiphyte`: one air plant with green leaves and a red bract
- `heron`: one still heron, 1.3 m, long pale legs, blue-grey body, beak, no water
- `grazer`: one four-legged grazer, amber hide `#c47a3a`, 1.8 m long, head lowered, no herd
- `loris`: one small clinging animal, 0.45 m, two pale glowing eyes
- `dragonfly`: one dragonfly, four translucent wings
- `kite_bird`: one red bird in a wing chevron, wingspan under 1 m
- `glow_moth`: one moth, pale pink glowing wings
- `lantern_frog`: one small frog with a yellow-green glowing belly
- `beetle_lamp`: one beetle, dark shell, one glowing yellow-green spot
- `brine_skipper`: one tiny pink shrimp-like animal
- `great_fall`: a short waterfall cliff, pale sheets of water, mist, one pool, no people
- `cathedral_heart`: seven huge dark trees in a ring, trunks and canopy only
- `spore_well`: a ring of spiral trees and glowing yellow-green spores
- `bloom_ridge`: a flower ridge with tall pale cards and pink, gold, and blue flowers
- `pitcher_throne`: one giant pitcher surrounded by smaller carnivorous plants, no people
- `lantern_monarch`: one huge blossom tree and a ring of glass leaves and moths
- `mirror_pan`: a wide pink salt pool, white crust, pale crystal spikes
- `heron_bend`: three herons, reeds, and river stones, no boat
- `vine_gate`: two rock posts with a curtain of vines, air plants, and small clinging animals
- `amber_circle`: six amber grazers standing in a circle, seed heads, three red birds
- `fern_nave`: a path between two rows of tall ferns and staghorns, center empty
- `sundew_jewel`: one giant sundew with smaller sundews and pale crystals

`tests/test_assets.py` does not run a model. It fails if a committed `.glb` is named for an unknown kit or landmark, if a scatter-kit file has more than one mesh or more than `5000` triangles, or if a landmark file has more than `80000` triangles. Missing files are allowed. `pytest` must pass on a machine with no GPU.

## Task 4: Stream the client

Replace the phase 1 plane and the hand-placed props. Spawn, pointer lock, both cameras, and the `3.2` m/s walk stay. Clamp to `[-1996, 1996]` only.

`web/js/kits/index.js` exports `makeKit(name)` for every kit above. If `web/assets/kits/<name>.glb` exists, load that file through the vendored glTF loader and return it at the unscaled size. Otherwise build the procedural shape. Shape rules, unscaled, base on `y = 0` unless noted:

- Keep phase 1 `moss_mound`, `mushroom`, `fern`, and `tree` (tapered trunk `10` m, three canopy blobs).
- `cushion_moss`: a flatter brighter mound, moss `#7ea15a`.
- `dead_log`: a cylinder on its side.
- `boulder` and `river_stone`: stone `#8a8178`. The boulder is the larger one.
- `reed`, `wildflower`, `seed_head`: thin stems. Flowers use all three valley flower colors. A seed head ends in an amber oval.
- `fiddlehead`: a green spiral crozier, not a cone fan.
- `staghorn`: two flat antler fronds, `#7ea15a`.
- `blossom_tree`: the tree trunk with blossom spheres `#e25b8a` and `#f2c14e` instead of the dark canopy.
- `glass_leaf`: a translucent double-sided plane, opacity about `0.55`, additive, colors `#7ee0c8` and `#f2a3c7`.
- `epiphyte`: a small clump of leaves and a red bract, meant to hang in the air.
- `lily_pad`: a flat green disc with one pink flower, water height, not a tall mesh.
- `vine_strand` and `vine_noose`: thin ribbons. The noose closes into a loop and is `#6a4a78`.
- `pitcher`: a vase about `1.6` m tall, body `#6f8f3a`, throat `#c4554a`, a lid.
- `sundew`: a low star of stalks with additive drops `#f6f2c4`.
- `snap_maw`: two lobes, open, outer `#c4554a`, inner `#f2e0a0`.
- `acid_cup`: a low bowl, liquid `#d6e25a`, opacity about `0.65`.
- `cliff_wall`, `waterfall_sheet` (double-sided, opacity `0.45`, `#c5ddd8`), `mist_card`, `pool_disc` (opacity `0.65`), `ridge_card`.
- `rainbow_card`: a thin additive arc, `#f2c9ff`.
- `spiral_tree`: a twisted stack, `#6a4a78`.
- `spore`: an additive blob, `#d7f28a`.
- `crystal_shard`: a pale blue spike, `#d7f0ff`.
- `salt_crust`: a flat white flake, `#efe6d4`.
- `bone_rib`: a pale arc, `#efe6d4`.
- `glow_moth`: additive wings `#f2c9ff`.
- `dragonfly`: a `0.5` m body and four translucent wing planes `#9fd8c8`.
- `kite_bird`: a chevron, wingspan about `0.9` m, `#e25b4a`.
- `heron`: about `1.3` m tall, long legs `#efe6d4`, body `#4e6d78`, a beak.
- `grazer`: four legs, body about `1.8` m long, shoulder about `1.1` m, hide `#c47a3a`, head lowered.
- `loris`: about `0.45` m, a clinging body and two emissive eyes `#f2c9ff`.
- `beetle_lamp`: a `0.35` m shell `#1c3b36` with an additive spot `#d7f28a`.
- `lantern_frog`: a small body, four stumps, a lamp belly `#d7f28a`.
- `brine_skipper`: a `0.2` m pink shard `#e7a0b4`.
- `seat_cushion`: a flat stone disc with a moss ring, radius about `0.7`.

`web/js/chunks.js` keeps the chunk under the player and the eight around it. Dispose meshes that leave the window. One displaced ground per chunk, `32` by `32` segments, vertex colors from `biome_at` using the meta rectangles and the river rule. One `InstancedMesh` per kit per chunk. A seat cushion at every spot in the loaded chunks. Empty chunks still draw ground. They do not invent cushions.

Water samples in a chunk become a ribbon `18` m wide with a scrolling UV. Ferns, reeds, vines, fiddleheads, and seed heads sway. Moths and dragonflies move. Sheets and the rainbow scroll. This motion is local and must not wait for phase 3.

When `biome_at` of the player changes, lerp fog color, fog density, and sun color over `1.2` s. Strange clear color stays `#2a2440`. Bog clear color is `#3e4630`. Salt clear color is `#efe8dc`. Within `12` m of a rectangle border, add `0.01` to fog density. The river corridor uses the river palette as soon as `biome_at` says `river`.

## Done when

- `pytest -q` and `node web/world/check_ground.mjs` still pass.
- `/health` reports `"spots": 4256`. Reloading the process does not increase that count.
- From the spawn, a person can walk to the river ribbon and on into the lantern orchard without a reload. The light changes. Cushions are visible inside the loaded part of a clearing and are absent from the open ground between clearings.
- The great-fall chunk payload includes a `waterfall_sheet` whose scale is at least `8`. The bog chunk used in the tests includes a pitcher and no blossom tree.
- Any committed glTF passes `tests/test_assets.py`. A missing glTF still leaves a visible procedural kit. The page does not request a model, a weight file, or a CDN mesh.

Commit once: the walkable forest is a 4000 m catalog of places, not one field of seats.

## What this phase does not do

Do not build seated recipes, claims, YouTube, or other players. Do not call WorldClaw, Hunyuan3D, or any other generator from the game process or from the browser. Do not replace the ground-height terms, the seat coordinates, or the river curve with a generated terrain. Phase 3 must grow a recipe for every new archetype name above before those seats can be sat. The original six archetype sets keep the names phase 3 already lists. That recipe work is a later change to `docs/plans/03-sit-and-video.md`, not part of this build.
