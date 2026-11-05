---
name: Phase 4 Other People
overview: "Make the server the position authority: stick figures, a hard 5 m gap, first-come seats, and private video that never appears in someone else's snapshot."
todos:
  - id: p4-sim
    content: Authoritative tick, slide-out, and exclusion tests
    status: pending
  - id: p4-ws
    content: Websocket hub, private video, claim reuse, snapshot shape
    status: pending
  - id: p4-sticks
    content: Interpolate snapshots and draw other stick figures
    status: pending
isProject: false
---

# Phase 4 Other People Implementation Plan

> **For agentic workers:** Implement this phase only. Do not add chat, names, emotes, or a shared video. One uvicorn worker. Presence stays in memory.

**Goal:** Two browsers share one forest. Bodies never come within 5 m. One cushion seats one person. Nothing on screen can carry a message.

**Architecture:** The browser sends inputs at 10 Hz. `Simulation` integrates them and slides bodies out of the 5 m circle. Postgres remains the claim lock. Snapshots describe bodies and claimed spot ids only.

**Tech Stack:** Phase 3 app, plus FastAPI websockets. Client rendering follows snapshots. No client-side position prediction.

## Global Constraints

- Tick `10` Hz. Integrate with `dt = 0.1`, never a client dt. Speed cap `3.2` m/s.
- Horizontal distance `< 5.0` is illegal. `5.0` exactly is allowed. Ignore Y.
- Interest radius `96` m. Heartbeat timeout `15` s.
- Incoming types are only `hello`, `input`, `sit`, `stand`, `youtube`, `ping`. Ignore anything else.
- Snapshot fields are `tick`, `server_time_ms`, `you`, `others`, `claimed_spot_ids`. Another player is `{session_id, color, pose}`. Pose is `{x,y,z,yaw,pitch,mode,spot_id}`. No field name may contain `name`, `chat`, `message`, or `youtube`.
- Welcome, to that socket only, may include `token`, `color`, `pose`, `youtube_video_id`.
- Forward and right match phase 1. Yaw `0` looks toward `+Z`.

## Files

- Create: `forest_server/realtime/protocol.py`, `forest_server/realtime/simulation.py`, `forest_server/realtime/hub.py`, `web/js/net.js`, `web/js/sticks.js`, `tests/test_exclusion.py`, `tests/test_protocol.py`
- Modify: `forest_server/app.py`, `forest_server/database/repository.py`, `web/js/main.js`, `web/js/avatar.js`

## Task 1: Simulation

```python
class Simulation:
    def spawn(self, session_id: str, color: str, x: float, z: float) -> None: ...
    def set_input(self, session_id: str, yaw: float, pitch: float, move_x: float, move_z: float) -> None: ...
    def tick(self) -> None: ...
    def try_sit(self, session_id: str, spot, claimed: set[int]) -> str | None: ...
    def stand(self, session_id: str) -> None: ...
    def remove(self, session_id: str) -> None: ...
    def pose(self, session_id: str): ...
    def others_near(self, session_id: str, radius: float) -> list: ...
```

`set_input` clamps each axis to `[-1, 1]` and, if the length exceeds 1, divides by that length. `tick` moves walkers by `(right * move_x + forward * move_z) * 3.2 * 0.1`, sets `y` from `ground_height`, and clamps XZ to `[-196, 196]`. Sitting players do not move from input.

After the candidate move, for up to 3 passes, if any pair is closer than 5 m, push each walker outward along the horizontal away vector so the pair lands at 5 m. A sitting body is the immovable one; only the walker slides. If a walker is still inside any circle after 3 passes, restore that walker to the position from the start of the tick.

`try_sit` returns `None` on success or a reason string `missing`, `taken`, `too_far`, `excluded`. Success requires mode `walk`, distance to the seat `<= 2.5`, spot id not in `claimed`, and the seat at least 5 m from every other live body. It then snaps the pose onto the seat and sets mode `sit`.

`tests/test_exclusion.py`:

- Two walkers at `(0, 0)` and `(0, 20)`, yaws `0` and `pi`, forward input for 200 ticks, distance `>= 5`.
- A walker beside a sitter never finishes a tick inside 5 m of that sitter.
- One second of full forward input moves a lone walker `3.2` m, within `1e-6`.
- `try_sit` from 4 m away returns `too_far`. Two `try_sit` calls on one spot in one process: the second returns `taken` when `claimed` was updated from the first. The database race stays covered by phase 3's `claim_spot` test.

## Task 2: Hub and socket

`protocol.py` holds pydantic models for the five incoming messages and for `Snapshot`. A test builds a snapshot and fails if any dumped key contains `name`, `chat`, `message`, or `youtube`.

`hub.py`:

- `hello` with a known token attaches that session. Unknown or null creates one, as `POST /api/session` does, and the welcome includes the raw token.
- One live socket per session. A new socket closes the old one.
- `input` calls `set_input`. `sit` loads the spot, calls `try_sit`, and on `None` calls `claim_spot`. If the insert loses, stand the simulator back up and send `{type:"reject", action:"sit", reason:"taken"}`. Other failures send that reason.
- `stand` calls `release_claim_for_session` and `stand`.
- `youtube` validates the id, stores it, and does not broadcast it.
- `ping` replies `{type:"pong"}`.
- Every 0.1 s, tick once and send each socket its own snapshot: self pose, others within 96 m, claimed spot ids within 96 m.
- A socket silent for 15 s is removed and its claim released.
- On startup, load claims whose session `last_seen_at` is within 15 s, spawn those sessions seated at the spot, and delete older claims. Do not restore walking positions.

`POST /api/pose` returns `{ok:false, reason:"live"}` when that session has a socket. HTTP sit and stand still call the same repository functions so phase 3 tests keep working. The live game path is the socket.

Mount `websocket /ws` before the static files mount.

`tests/test_protocol.py` uses the FastAPI websocket test client: two hellos get two session ids; a `youtube` from one is absent from the other's snapshot; a snapshot model has no banned key substrings.

## Task 3: Render other bodies

`web/js/net.js` opens `ws://127.0.0.1:8765/ws` after the enter click (use the page host, not a hardcoded host, so the port follows the page). Send `hello` with the stored token or null. Save a new token from welcome. Send `input` at 10 Hz with the current yaw, pitch, and move axes. Send `sit`, `stand`, and `youtube` when those actions happen.

Keep the last two snapshots. Render pose is the previous snapshot when two exist, which is one tick of delay. Between ticks, lerp toward the newer snapshot. Do not integrate WASD into the displayed position anymore.

`web/js/sticks.js` uses `avatar.js` for every other session and for the local body in third person. Color comes from the snapshot. Play the walk cycle only above `0.15` m/s of snapshot motion. Lerp into the seated pose over `0.6` s. Hide the local body in first person. Other bodies stay visible.

Occupied spot ids are not targetable. The local seated camera, diorama, and YouTube panel stay as in phase 3, parented to the server pose of the seat.

Remove the 2-second `POST /api/pose` loop from the live path.

## Done when

- `pytest -q` passes, including the head-on 5 m test and the snapshot shape test.
- Two browser profiles on one server: walking into each other stops at 5 m; both pressing sit on one cushion leaves the second standing; the first person's video never appears in the second window; neither screen has a text field for talking.
- Killing the server and returning within 15 s still shows the seated claim. Waiting longer frees the cushion.

Commit once: people can share the forest without meeting or speaking.