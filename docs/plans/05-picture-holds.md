---
name: Phase 5 Picture Holds
overview: Tune the forest so each region reads at a glance, keep the 3 by 3 instance budget, and prove a seated claim survives a short restart.
todos:
  - id: p5-kits
    content: Lock landmark scales and kit silhouettes with tests
    status: pending
  - id: p5-chunks
    content: Instance and dispose the 3 by 3 window
    status: pending
  - id: p5-visit
    content: Restart-claim test, README two-browser visit
    status: pending
isProject: false
---

# Phase 5 Picture Holds Implementation Plan

> **For agentic workers:** Implement this phase only. No new gameplay, no accounts, no scenery audio, no chat. Adjust kits, motion, fog, and tests until the existing forest holds a two-browser visit.

**Goal:** The phase 4 game still plays, and a minute of walking shows six distinct places. Seats stay composed. Chunks load and unload without leaking meshes.

**Architecture:** Same server and client. This phase changes numbers, materials, and cleanup. Recipe tests from phase 3 still define the legal compositions.

**Tech Stack:** Unchanged. One uvicorn worker. Dedicated `meditation_forest` Postgres.

## Global Constraints

- Do not change spot spacing, the 5 m rule, the ground-height terms, ports, or the snapshot schema.
- Solid kits stay out of the seated view wedge except `behind_sheet`.
- Overworld motion stays deterministic from time and does not get networked.
- Cathedral scatter trees stay scale `>= 1.6` (at least 16 m). Waterfall landmark sheets stay scale `>= 8`.
- Active window remains the player's chunk plus eight neighbors.
- The enter overlay and the one fading hint are the only walk HUD. The YouTube panel appears only while seated.

## Files

- Modify: `web/js/kits/index.js`, `web/js/kits/materials.js`, `web/js/chunks.js`, `web/js/diorama.js`, `web/css/forest.css`, `forest_server/world/scatter.py`, `forest_server/world/landmarks.py`, `forest_server/world/recipes.py`, `README.md`
- Create: `tests/test_landmarks.py`, `tests/test_restart_claims.py`
- Do not add a physics library, a model CDN, or a new route.

## Task 1: Silhouettes

Make these true in code and in `tests/test_landmarks.py`:

- `landmarks` for the great fall include a `waterfall_sheet` with `scale >= 8` and at least one `cliff_wall` and one `pool_disc`.
- Cathedral heart trees are scale `2` (20 m) and there are 7 of them.
- Spore well includes at least 12 `spore` and 6 `spiral_tree`.
- West ridge includes 5 `ridge_card` with `scale >= 3`.
- A cathedral chunk's scatter trees all have `scale >= 1.6`.

Visual rules for `makeKit`, without changing kit names:

- `tree`: trunk is a tapered cylinder, three canopy blobs, canopy `#1d3328`, trunk `#4a382c`. The unscaled mesh is 10 m, so scale 1.6 is 16 m.
- `waterfall_sheet`: double-sided, opacity about `0.45`, color `#c5ddd8`, UVs scroll every frame.
- `ridge_card`: a flat card tall enough that scale 3 reads as a ridge from 30 m, color `#9aa7b0`.
- `spore`: additive, color `#d7f28a`. `glow_moth`: additive, `#f2c9ff`, circling when motion is `path_circle` and also a slow circle in overworld scatter.
- `lantern_frog`: hop with `amount` about `0.35` and period `6` s where scatter sets that motion. Set that motion on strange-fauna frogs in scatter.
- Ferns and reeds sway. Amount about `0.07`, period about `5` s.
- `seat_cushion`: stone disc plus a moss ring, still under 1.5 m across.

If a seated view is blocked, change only that archetype's tuple in `recipes.py`. Re-run `tests/test_recipes.py`. Do not turn the view filter off for any archetype except `behind_sheet`.

Biome light and border fog from phase 2 stay. Strange fauna clear color stays dusk `#2a2440`. Moss stays morning `#d5e2d2`.

## Task 2: Chunk budget

In `chunks.js`:

- One `InstancedMesh` per kit per loaded chunk, not one mesh per plant.
- On chunk exit, `dispose()` geometries and materials created for that chunk and remove them from the scene.
- Do not cache more than the 3 by 3 window.
- Seat cushions for spots in loaded chunks only.
- Recipe meshes from a sit are not added to the chunk cache. Standing disposes them.

A small dev-only counter is acceptable in the console (`chunks`, `instances`) and must not be a HUD.

`tests/test_restart_claims.py` against Postgres:

- Create a session, claim a spot, set `last_seen_at` to now. Run the hub's startup loader. The claim remains and the simulated pose is `sit` on that spot.
- Set `last_seen_at` 16 seconds in the past. Run the loader again. The claim is gone.

Use the repository and hub functions directly. Do not sleep for 16 real seconds; write the timestamp.

## Task 3: The visit, written down

`README.md` keeps the original purpose text and the run commands. Add the two-browser check:

1. `docker compose up -d`, activate `.venv`, run one uvicorn on `127.0.0.1:8765`.
2. Open two browser profiles to `http://127.0.0.1:8765/`.
3. Walk both from the moss spawn toward the great fall `(46, 150)` and, separately, toward the spore well `(-120, -140)`.
4. Walk them together and confirm they stop 5 m apart.
5. Sit on two different cushions. Each seated view moves. Play a YouTube id on one. The other window does not show that player or that video.
6. Stand. The iframe is gone.
7. Restart uvicorn within 15 s and confirm the seat is still held. After 15 s of silence the cushion is free.

Add one short paragraph: a future `online-meditation.html` on the marketing site will iframe this origin. Do not edit that site in this repo.

`web/css/forest.css`: the overlay and the YouTube panel stay translucent and quiet. No new panels.

## Done when

- `pytest -q` and `node web/world/check_ground.mjs` pass.
- Landmark and restart tests pass.
- Recipe view-filter tests still pass.
- The two-browser walk above can be done without a reload, and each of the six regions is distinguishable by color and silhouette.

Commit once: the forest is ready to be visited.