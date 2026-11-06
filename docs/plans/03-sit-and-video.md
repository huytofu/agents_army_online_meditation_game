---
name: Phase 3 Sit and Video
overview: Let one player lock a cushion, sit inside a Python-authored moving scene, play a private YouTube video, and keep that seat across a refresh.
todos:
  - id: p3-recipes
    content: Deterministic seated recipes and the view-filter tests
    status: pending
  - id: p3-claims
    content: Anonymous session, pose, first-come claim, private video id
    status: pending
  - id: p3-client
    content: Target ring, sit camera, diorama motion, YouTube panel
    status: pending
isProject: false
---

# Phase 3 Sit and Video Implementation Plan

> **For agentic workers:** Implement this phase only. Walking stays local. There are no other visible players yet. The claim row is real, so a second browser cannot take the same seat.

**Goal:** Target a cushion, sit, watch a composed scene move, play any YouTube video, stand, and return to the same seat after refresh.

**Architecture:** `GET /api/world/spots/{id}/recipe` is computed in Python from the spot id. Session HTTP routes store the walker pose, the claim, and a private video id. The browser fades nearby scatter and draws the recipe in local space.

## The forest these seats belong to

The walkable world is the current 4000 m square, `x` and `z` in `[-2000, 2000]`. It is not one 400 m moss field. Spawn stays `(-24, 0)` in the moss plain, inside the moss gathering, with 14 m of open ground so you do not appear on a cushion.

The 1364 cushions in Postgres are the only seats:

- Twelve gatherings, one in each biome, 100 cushions each. They are rejection-sampled at least 10 m apart, not a hex or a row.
- One hundred sixty-four isolated cushions on the 280 m grid, each at least 10 m from a gathering cushion and 16 m off the wet river.

A clearing cushion and an isolated cushion use the same recipe, claim, and sit rules. The archetype still comes from the spot row, which follows that spot's biome. All twelve biomes have four archetypes. The six that arrived with the wide forest are carnivorous bog, lantern orchard, fern sea, hanging vines, amber herd, and salt mirror. Their layouts are below with the original six.

The corner minimap stays visible while sitting. It still marks only this player.

**Tech Stack:** Phase 2 client and server. YouTube IFrame API loaded only after a sit.

## Global Constraints

- Sit range is `2.5` m horizontally. Exclusion constant `5` m is reserved for phase 4; this phase still rejects a sit that would place the seat within `5` m of another session whose stored pose is fresh (seen in the last `15` s).
- Token: `secrets.token_urlsafe(32)`. Store SHA-256 hex only. The browser keeps the raw token in `localStorage` key `forest_token`.
- Video id matches `^[A-Za-z0-9_-]{11}$` or is null. Any such id is allowed.
- Seated camera: eye height `1.15`, pitch `-4` degrees, yaw drift `1.5` degrees times `sin(time_s / 12)`. No mouse look while seated.
- Local block space: `+Z` is the gaze before yaw. World position:

```javascript
const wx = seatX + block.x * Math.cos(yaw) + block.z * Math.sin(yaw);
const wz = seatZ - block.x * Math.sin(yaw) + block.z * Math.cos(yaw);
const wy = groundHeight(wx, wz) + block.y;
```

- Solid kits stay out of radius `0.8` m and out of the forward wedge `abs(atan2(x, z)) < 0.35 && hypot(x, z) < 4`. Airy kits may enter it. That set is `forest_server.world.biomes.AIRY_KITS`: `mist_card`, `spore`, `glow_moth`, `waterfall_sheet`, `vine_strand`, `dragonfly`, `kite_bird`, `brine_skipper`, `rainbow_card`, `glass_leaf`, `beetle_lamp`, `songbird`, `butterfly`. Archetype `behind_sheet` skips this filter.
- Motion phase is `0.17 * spot_id` seconds. Kinds: `none`, `sway`, `uv_scroll`, `drift`, `bob`, `path_circle`, `hop`.

## Files

- Create: `forest_server/world/recipes.py`, `forest_server/routers/session.py`, `web/js/diorama.js`, `web/js/youtube.js`, `tests/test_recipes.py`, `tests/test_claims.py`
- Modify: `forest_server/database/repository.py`, `forest_server/app.py`, `web/js/main.js`, `web/js/controls.js`, `web/index.html`, `web/css/forest.css`

## Task 1: Recipes

`recipe_for_spot(spot) -> dict` with `spot_id, biome, archetype, yaw, blocks`. Each block has the phase 2 fields and `"space": "local"`.

RNG is `mulberry32(spot_seed(spot.id))`. It does not change yaw or archetype.

```python
def arc(rng, kit, count, radius, center, spread, scale, y, motion, amount, period):
    # angle 0 is +Z. Evenly space `count` items across [center-spread/2, center+spread/2].
    # Jitter angle by (rng()-0.5)*0.12 and radius by 0.92+0.16*rng().
    # variant = int(rng()*VARIANTS.get(kit, 1)) % max(VARIANTS.get(kit, 1), 1)
    # scale *= 0.85+0.3*rng()
```

`VARIANTS`: mushroom 2, boulder 2, tree 3, spiral_tree 2, cliff_wall 2, default 1.

```python
def front(rng, kit, count, z, x_spread, scale, y, motion, amount, period):
    # x runs from -x_spread to x_spread. z stays z. rot_y = 0.
```

`center = math.pi` means behind the sitter. After building, drop illegal solid blocks unless `keep_view` is false. If fewer than 8 blocks remain, append behind-arcs of `fern` at radius `6.5` until there are 8.

Layouts (op, kit, count, radius or z, center or x spread, spread, scale, y, motion, amount, period):

- `dew_clearing`: arc mushroom 9, r 3.0, center pi, spread 2.4, scale 0.8; arc fern 12, r 5.5, center pi, spread 2.8, sway 0.07 period 5; arc moss_mound 6, r 8, center 0, spread 3, scale 1.3; front dead_log 1, z 3.2, x spread 1.4, scale 1.1
- `mushroom_ring`: arc mushroom 14, r 3.2, center pi, spread 5.0 (leave the forward gap); arc fern 8, r 6, center pi, spread 2
- `log_seat`: front dead_log 2, z 2.4, x spread 1.6, scale 1.2; arc fern 10, r 6, center pi, spread 2.5; arc moss_mound 5, r 8, center pi, spread 2
- `mound_overlook`: front moss_mound 2, z 1.5, x spread 2.2, scale 1.8; arc tree 4, r 10, center pi, spread 2.2, scale 0.6
- `between_roots`: arc tree 4, r 6, center pi, spread 2.6, scale 1.8; arc fern 8, r 3.5, center pi, spread 2
- `shaft_clearing`: arc tree 6, r 9, center pi, spread 4.5, scale 2; arc vine_strand 8, r 6, y 4, sway 0.1 period 7
- `hollow`: front tree 1, z 3, x spread 2.2, scale 2.2; arc vine_strand 6, r 4, y 3; arc mushroom 4, r 3, center pi, spread 1.5
- `vine_nave`: front tree 4, z values produced as an arc at x 3.5 and an arc at x -3.5, r from 4 to 12, scale 1.7; arc vine_strand 8, r 3.5, y 4
- `bank_stone`: arc river_stone 8, r 4, center 0, spread 1.4; arc reed 10, r 4.5, center pi/2, spread 1.2; front pool_disc 1, z 5, scale 3
- `reed_pocket`: arc reed 16, r 3.5, center pi, spread 5; arc river_stone 5, r 6, center pi, spread 2
- `shallow_bend`: front pool_disc 1, z 4, scale 4; arc river_stone 6, r 5, center 0.8, spread 1; arc reed 8, r 6, center pi, spread 2
- `boulder_island_view`: front boulder 1, z 4, x spread 2, scale 1.8; arc reed 8, r 5, center pi, spread 2.4
- `pool_ledge`: front pool_disc 1, z 4, scale 3; front waterfall_sheet 1, z 7, y 2, scale 8, uv_scroll amount 0.25 period 4; front cliff_wall 2, z 6, x spread 4, scale 2; arc mist_card 4, r 5, bob amount 0.3 period 6
- `mist_shelf`: arc mist_card 4, r 3, center 0, spread 1, drift amount 0.4 period 8; front cliff_wall 2, z 5, x spread 3, scale 1.2; front waterfall_sheet 1, z 6, x stored via front x spread 3, scale 6, uv_scroll 0.2
- `behind_sheet` with `keep_view` false: front waterfall_sheet 1, z 2.2, y 1, scale 8, uv_scroll 0.25; front pool_disc 1, z 1, scale 2; front cliff_wall 2, z 3, x spread 3, scale 2; arc mist_card 4, r 2.5
- `gorge_floor`: front cliff_wall 6, z from 2 to 8, x spread 2.4, scale 2.4; front waterfall_sheet 1, z 10, y 3, scale 8, uv_scroll 0.25; arc mist_card 4, r 4
- `terrace_lip`: front ridge_card 3 at z 12, 16, 20 with scales 2, 3, 4; arc wildflower 10, r 4, center pi/2, spread 1; arc moss_mound 4, r 6, center pi
- `flower_bowl`: arc wildflower 18, r 3.4, center pi, spread 5
- `ridge_seat`: front ridge_card 4, z -2, x spread 3, scale 1.6; arc wildflower 8, r 5, center 0, spread 1.2
- `amphitheater`: arc ridge_card 5, r 11, center pi, spread 2.2, scale 3; arc wildflower 12, r 4, center pi, spread 2
- `spore_circle`: arc spore 12, r 3, bob amount 0.4 period 5; arc spiral_tree 5, r 7, center pi, spread 2.4; arc glow_moth 4, r 2, path_circle amount 1.6 period 14
- `spiral_cathedral`: arc spiral_tree 5, r 6, scale 1.4; arc spore 10, r 3.5, center pi, bob 0.3 period 6
- `moth_lane`: arc glow_moth 6, r 4, center 0, spread 1.2, drift 0.5 period 9; arc spiral_tree 4, r 7, center pi/2, spread 1
- `violet_hollow`: arc spore 12, r 4, center pi, bob 0.35 period 5; front spiral_tree 1, z 4, x spread 2.5; front lantern_frog 2, z 3, x spread 2, hop amount 0.35 period 6
- `pitcher_ring`: arc pitcher 8, r 5, center pi, spread 2.2, scale 1.2; arc sundew 8, r 3.2, center pi, spread 2; arc acid_cup 4, r 6.5, center pi, spread 1.5
- `sundew_jewel`: arc sundew 10, r 3.5, center pi, spread 4; arc crystal_shard 6, r 6, center pi, spread 2; front bone_rib 1, z 5, scale 1
- `maw_clearing`: arc snap_maw 6, r 4.5, center pi, spread 2; arc vine_noose 6, r 6, y 2, center pi, spread 2, sway 0.1 period 7; arc mud_patch 4, r 7, center pi, spread 1.4
- `acid_cup_seat`: arc acid_cup 8, r 3.6, center pi, spread 2.4; arc pitcher 6, r 6, center pi, spread 2; front bone_rib 2, z 5, x spread 2
- `glow_fruit`: arc blossom_tree 5, r 6, center pi, spread 2; arc beetle_lamp 6, r 3.2, center pi, bob 0.25 period 6; arc butterfly 4, r 4, path_circle amount 1.2 period 10
- `glass_aisle`: arc glass_leaf 10, r 3.5, center pi, spread 2.2, bob 0.2 period 6; arc blossom_tree 4, r 7, center pi, spread 1.5
- `moth_orchard`: arc glow_moth 8, r 3.2, path_circle amount 1.2 period 12; arc blossom_tree 5, r 7, center pi, spread 2
- `lantern_root`: front blossom_tree 1, z 5, scale 2.2; arc flower_gold 8, r 3.5, center pi, spread 2; arc beetle_lamp 6, r 5, center pi, bob 0.2 period 6
- `fiddle_bowl`: arc fiddlehead 12, r 3.4, center pi, spread 4, sway 0.07 period 5; arc fern 8, r 6, center pi, spread 2
- `staghorn_nave`: arc staghorn 8, r 4, center pi, spread 2.2; arc fern 8, r 6.5, center pi, spread 2
- `fern_tunnel`: arc fern 10, r 3.2, center pi, spread 2; arc tree 4, r 7, center pi, spread 1.6, scale 1.2; arc fiddlehead 6, r 5, center pi, spread 1.5
- `curl_overlook`: front tree 2, z 6, x spread 3, scale 1.4; arc fern 8, r 4, center pi, spread 2; arc flower_pink 6, r 5, center pi, spread 1.6
- `root_swing`: arc vine_strand 10, r 4, y 4, sway 0.1 period 7; arc epiphyte 6, r 5, y 3, center pi, spread 2
- `epiphyte_balcony`: arc epiphyte 8, r 3.5, y 3, center pi, spread 2; arc vine_strand 8, r 6, y 4, sway 0.1 period 7; arc blossom_tree 3, r 8, center pi, spread 1.2
- `loris_perch`: arc loris 4, r 3.2, y 2, center pi, bob 0.12 period 5; arc vine_strand 8, r 5, y 3; arc epiphyte 6, r 4, y 3.5, center pi, spread 1.6
- `curtain_gap`: arc vine_strand 12, r 3.2, y 3.5, center pi, spread 4, sway 0.1 period 7; arc monkey 3, r 6, center pi, spread 1.2, bob 0.12 period 4
- `grazer_shade`: arc grazer 4, r 6, center pi, spread 1.5, bob 0.08 period 4; arc seed_head 8, r 4, center pi, spread 2, sway 0.07 period 5; arc tree_yellow 3, r 9, center pi, spread 1.2, scale 1.1
- `seed_ring`: arc seed_head 12, r 3.5, center pi, spread 4, sway 0.07 period 5; arc wildflower 8, r 6, center pi, spread 2
- `dust_bowl`: arc boulder 5, r 6, center pi, spread 2; arc grass_patch 8, r 3.5, center pi, spread 2; arc dirt_patch 4, r 5, center pi, spread 1.4
- `bird_perch`: arc kite_bird 4, r 5, y 3, drift amount 1.2 period 9; arc seed_head 8, r 4, center pi, spread 2; arc tree_yellow 3, r 8, center pi, spread 1.2
- `crust_lip`: arc salt_crust 10, r 4, center pi, spread 2.4; arc crystal_shard 6, r 6, center pi, spread 1.5
- `pink_pool`: front pool_disc 1, z 5, scale 4; arc salt_crust 8, r 6, center pi, spread 2; arc brine_skipper 4, r 3.2, hop amount 0.35 period 6
- `crystal_seat`: arc crystal_shard 8, r 3.5, center pi, spread 2; arc salt_crust 6, r 6, center pi, spread 1.6; front bone_rib 2, z 5.5, x spread 2
- `brine_hollow`: arc brine_skipper 6, r 3, hop amount 0.35 period 6; arc salt_crust 8, r 5, center pi, spread 2; arc crystal_shard 4, r 7, center pi, spread 1.4

For three ridge cards at fixed z, call `front` once per z rather than inventing a new helper. Same for the nave: two `arc` calls are enough if the tests pass. `front` does not jitter, so the `pool_ledge` sheet stays at scale `8`.

The seated camera looks along local `+Z` and cannot turn. When an arrangement would otherwise sit entirely behind the sitter, add a `front` pair near `z 4.6` (or an airy kit closer in). Solids there are past the 4 m wedge, so the gaze stays open and the pieces are still inside the view.

`tests/test_recipes.py`: every archetype name produces at least 8 blocks; every kit is in the phase 2 kit set; the same spot id returns equal JSON; solid blocks of every archetype except `behind_sheet` pass the wedge test; `pool_ledge` includes a `waterfall_sheet` with scale `>= 8`.

`GET /api/world/spots/{id}/recipe` returns that JSON or 404.

## Task 2: One session and one claim

Repository, exact behavior:

- `create_session(token_hash, color, pose) -> UUID`
- `session_by_token_hash(token_hash) -> row or None`
- `update_pose(session_id, pose)` and `touch(session_id)`
- `set_youtube(session_id, video_id or None)`
- `claim_spot(spot_id, session_id) -> bool` using `INSERT ... ON CONFLICT (spot_id) DO NOTHING RETURNING spot_id`
- `release_claim_for_session(session_id)`
- `pose_conflicts(x, z, session_id) -> bool` true when another session with `last_seen_at` within 15 seconds has horizontal distance `< 5`

Color: hue `(int(uuid.hex[:4], 16) % 90) + 25`, saturation `0.28`, lightness `0.42`, returned as `#rrggbb`.

Pose JSON: `{x, y, z, yaw, pitch, mode, spot_id}`. `mode` is `walk` or `sit`. New sessions start at the spawn, mode `walk`, `spot_id` null.

Routes:

- `POST /api/session` body `{token: str|null}`. Unknown or null token creates a session and returns the raw token once. Known token resumes. Response: `{token, session_id, color, pose, youtube_video_id}`.
- `POST /api/pose` body `{token, x, y, z, yaw, pitch}`. Updates the pose only when mode is `walk`. Returns `{ok:true, pose}` or `{ok:false, reason:"missing"}`.
- `POST /api/sit` body `{token, spot_id}`. Load the stored pose. Reject `missing`, `too_far` (farther than 2.5 m), `excluded` (seat is within 5 m of another fresh pose), or `taken`. On success snap pose to the seat, `y = ground_height`, mode `sit`, store the claim. Response `{ok:true, pose}` or `{ok:false, reason}`.
- `POST /api/stand` releases the claim and sets mode `walk` at the same x,z.
- `POST /api/session/youtube` body `{token, video_id: str|null}`. Bad ids return `{ok:false, reason:"bad_video"}`.

`tests/test_claims.py` against Postgres: two concurrent `claim_spot` calls for one spot produce one true and one false; a pose 3 m away gets `too_far`; a video id `not a video` is rejected; `dQw4w9WgXcQ` is stored and returned only by `POST /api/session` for that token.

## Task 3: Sit in the browser

`controls.js`: `F` sets `sitPressed` for one consume. Hint text becomes `WASD move · mouse look · V view · F sit`.

Targeting in `main.js`: among unclaimed spots from loaded chunks, pick the nearest within 12 m and 10 degrees of the horizontal look. Keep it until the angle exceeds 18 degrees or the distance exceeds 14 m. Draw a thin ring. `F` inside 2.5 m calls sit. `F` while seated calls stand. Do not auto-walk and do not orbit the camera.

Every 2 seconds, and immediately before sit, `POST /api/pose` with the current feet position.

On sit success: lerp the camera to the seated pose over `0.8` s, disable mouse look, fade scatter and other cushions inside 25 m to opacity 0, keep this seat's cushion, fetch the recipe, and add those meshes. Apply motion from `performance.now()/1000 + 0.17*spot_id`:

- `sway`: rotate Z by `amount * sin(2π t / period)`
- `uv_scroll`: add `amount * t` to the material's texture offset if present; otherwise move the mesh up by `0` and offset a `time` uniform. A mesh translation of `0` with the material's `polygonOffset` is not enough. For sheets, scroll by shifting vertices' uv attribute each frame.
- `drift`: add `(amount*sin(t), 0, amount*cos(t*0.7))` in local XZ
- `bob`: add `amount * sin(2π t / period)` to Y
- `path_circle`: XZ on a circle of radius `amount`
- `hop`: Y += `amount * max(0, sin(2π t / period))**2`

On stand: remove recipe meshes, restore scatter, enable mouse look, resume walking.

YouTube: a panel `#youtube` in the bottom-left, shown 1.2 s after sit. A text field, Play, and Stop. Load `https://www.youtube.com/iframe_api`, create the player with the 11-character id, and on stand call `destroy()` and remove the iframe. Restore the last id into the field after refresh. Do not autoplay.

Create or resume the session on the first successful enter click.

## Done when

- Recipe and claim tests pass, and phase 1–2 tests still pass.
- Sitting at a moss seat, a gorge seat, and a strange seat shows three different moving sets of kits. An isolated cushion uses the same sit path as a clearing cushion.
- A second browser gets `taken` for that spot.
- Refresh keeps the claim and the video id text. The video does not start by itself. Standing removes the iframe and the sound.

Commit once: a single player can sit and listen.