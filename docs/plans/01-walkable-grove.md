---
name: Phase 1 Walkable Grove
overview: "Stand up the dedicated forest Postgres and a Three.js walk on port 8765: one moss grove, both cameras, and a ground-height contract the later phases reuse."
todos:
  - id: p1-db
    content: Compose Postgres on 5436, config, SQL migrator, and /health
    status: pending
  - id: p1-ground
    content: Shared ground formula with pytest and node parity
    status: pending
  - id: p1-walk
    content: Vendored Three.js grove, both cameras, local stick figure
    status: pending
isProject: false
---

# Phase 1 Walkable Grove Implementation Plan

> **For agentic workers:** Implement this phase only. Do not seed the forest, add seats, YouTube, or other players. Required check: `pytest -q` and `node web/world/check_ground.mjs`.

**Goal:** A person can open `http://127.0.0.1:8765/`, click once, and walk a small moss grove in first or third person while Postgres answers `/health`.

**Architecture:** FastAPI serves `web/` and a dedicated Postgres 16. Walking is local to the browser in this phase. Terrain height comes from one formula both languages share.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2 async, asyncpg, Postgres 16, Three.js 0.170.0 vendored, Node for one parity script.

## Global Constraints

- Repo is only `agents_army_online_meditation_game`. Database `meditation_forest` on `127.0.0.1:5436`, user `forest`, password `forest`, volume `meditation_forest_pg`. No other Entourage database.
- One uvicorn process, host `127.0.0.1`, port `8765`.
- 1 unit = 1 meter. Y is up. Yaw `0` looks toward world `+Z`. Forward is `(sin yaw, cos yaw)`. Right is `(cos yaw, -sin yaw)`. Pitch does not move the body.
- Point the camera with `lookAt` and that forward vector. Three.js cameras look down `-Z` by default, so do not assign `camera.rotation.y = yaw` and expect `+Z`.
- Ground height is only this sum. `WORLD_SEED` does not affect it.

```python
TERMS = (
    (1.6, 0.020, 0.0, 1.7),
    (1.1, 0.0, 0.017, 0.4),
    (0.45, 0.050, 0.050, 0.0),
    (0.25, 0.090, 0.030, 0.0),
)
def ground_height(x: float, z: float) -> float:
    return sum(a * math.sin(kx * x + kz * z + phase) for a, kx, kz, phase in TERMS)
```

- Walk speed `3.2` m/s. Spawn at `(-24, ground_height(-24, 0), 0)`. Clamp X and Z to `[-196, 196]`.
- No chat, accounts, scenery audio, glTF, physics engine, or shadow maps.
- Windows Git Bash: `source .venv/Scripts/activate`. Linux cloud agents: `source .venv/bin/activate`.

## Files

- Create: `docker-compose.yml`, `.env.example`, `.gitignore`, `requirements.txt`, `forest_server/__init__.py`, `forest_server/app.py`, `forest_server/config.py`, `forest_server/database/connection.py`, `forest_server/database/migrate.py`, `forest_server/world/constants.py`, `forest_server/world/ground.py`, `forest_server/routers/health.py`, `migrations/001_init.sql`, `web/index.html`, `web/css/forest.css`, `web/vendor/three.module.js`, `web/js/main.js`, `web/js/ground.js`, `web/js/controls.js`, `web/js/avatar.js`, `web/js/kits/materials.js`, `web/js/kits/index.js`, `web/world/check_ground.mjs`, `tests/test_ground.py`, `tests/test_health.py`
- Modify: `README.md` (add a Run section; keep the purpose text)
- Create if missing: `.cursor/environment.json`, `AGENTS.md`

Later phases add routers. Register health before `app.mount("/")`.

## Task 1: Local database and Python project

`docker-compose.yml`:

```yaml
services:
  forest_postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: meditation_forest
      POSTGRES_USER: forest
      POSTGRES_PASSWORD: forest
    ports:
      - "127.0.0.1:5436:5432"
    volumes:
      - meditation_forest_pg:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U forest -d meditation_forest"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  meditation_forest_pg:
```

`.env.example`:

```text
FOREST_DATABASE_URL=postgresql+asyncpg://forest:forest@127.0.0.1:5436/meditation_forest
FOREST_PORT=8765
WORLD_SEED=20261105
```

`.gitignore`: `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`, `*.pyc`. Commit `web/vendor/three.module.js`.

`requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `pydantic`, `pydantic-settings`, `pytest`, `pytest-asyncio`, `httpx`.

`forest_server/config.py` uses pydantic-settings. Defaults match `.env.example`. Fields: `forest_database_url`, `forest_port`, `world_seed`.

`forest_server/world/constants.py` holds `TERMS`, `WORLD_MIN = -200.0`, `WORLD_MAX = 200.0`, `CHUNK_SIZE = 64.0`, `SPOT_SPACING = 8.0`, `EXCLUSION_M = 5.0`, `SIT_RANGE_M = 2.5`, `MAX_SPEED = 3.2`, `EYE_HEIGHT = 1.55`, `THIRD_DISTANCE = 4.2`, `THIRD_HEIGHT = 1.8`, `SPAWN_X = -24.0`, `SPAWN_Z = 0.0`, and `WORLD_SEED` read from settings.

`forest_server/world/ground.py` exports `ground_height(x, z) -> float` using `TERMS` only.

`web/js/ground.js` exports the same function. Coefficients live in that file as the same four tuples. `web/world/check_ground.mjs` imports it and prints JSON heights for `(0,0)`, `(10,-4)`, `(-80,120)`, `(199,199)`.

`tests/test_ground.py` runs `node web/world/check_ground.mjs`, parses stdout, and asserts each value equals `ground_height` within `1e-9`.

`.cursor/environment.json` for the cloud VM:

```json
{
  "install": "python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt",
  "start": "sudo service docker start"
}
```

`AGENTS.md` tells a cloud agent to read only the assigned file in `docs/plans/`, to start Docker before tests, and to activate `.venv/bin/activate` on Linux.

## Task 2: Migrations and health

`migrations/001_init.sql` creates `schema_migrations`, `spots`, `sessions`, and `spot_claims` exactly:

```sql
CREATE TABLE schema_migrations (
    filename text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE spots (
    id integer PRIMARY KEY,
    biome text NOT NULL,
    archetype text NOT NULL,
    x double precision NOT NULL,
    y double precision NOT NULL,
    z double precision NOT NULL,
    yaw double precision NOT NULL,
    chunk_x integer NOT NULL,
    chunk_z integer NOT NULL
);
CREATE INDEX spots_chunk ON spots (chunk_x, chunk_z);
CREATE TABLE sessions (
    id uuid PRIMARY KEY,
    token_hash text NOT NULL UNIQUE,
    color text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    pose jsonb NOT NULL,
    youtube_video_id text
);
CREATE TABLE spot_claims (
    spot_id integer PRIMARY KEY REFERENCES spots (id),
    session_id uuid NOT NULL REFERENCES sessions (id),
    claimed_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX spot_claims_session ON spot_claims (session_id);
```

`migrate.py` applies `migrations/*.sql` in filename order inside a transaction and records the filename. A second startup applies nothing.

`connection.py` exposes `init_database`, `close_database`, and `async with get_session()`. The engine uses `FOREST_DATABASE_URL` with `pool_pre_ping=True`.

`GET /health` returns `{"status":"ok","db":"ok","spots":0}` when `SELECT 1` and `SELECT COUNT(*) FROM spots` succeed. On failure return `{"status":"degraded","db":"down","spots":0}` with HTTP 200 so the process still serves the page.

`tests/test_health.py` uses `httpx.ASGITransport` against the app. It requires `db == "ok"`. Bring Postgres up first; if Docker cannot start, stop and report that. Do not switch the test to SQLite.

```bash
docker compose up -d
source .venv/Scripts/activate   # Linux: source .venv/bin/activate
python -m uvicorn forest_server.app:app --host 127.0.0.1 --port 8765
pytest -q
node web/world/check_ground.mjs
```

## Task 3: The page and the walk

Vendor Three.js r170:

```bash
curl -L -o web/vendor/three.module.js https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js
```

`web/index.html` title is `Forest`. Import map points `"three"` at `./vendor/three.module.js`. A full-viewport canvas. Overlay `#enter` reads `Click to walk into the forest`. Hint `#hint` reads `WASD move · mouse look · V view`, fades after 5 seconds, and uses a system serif (`Palatino Linotype`, `Palatino`, `Georgia`). No other HUD.

`web/js/controls.js` after the click:

- Request pointer lock on the canvas. `Esc` leaves it.
- `yaw += movementX * 0.002`. `pitch -= movementY * 0.002`.
- First person pitch clamp `-50..70` degrees. Third person `-35..55`.
- `V` toggles `first` and `third`. Default `third`.
- WASD and arrows fill `moveX` and `moveZ` in `-1..1`, camera-relative. Normalize if the vector is longer than 1.
- `consume()` returns `{moveX, moveZ, yaw, pitch, view}` and clears the key edges.

`web/js/avatar.js` builds a 1.7 m stick figure from cylinders: torso, head, two arms, two legs. `setColor(hex)`, `setWalkPhase(phase)`, `setSeated(false)`. Origin at the feet. Phase 1 uses one local avatar.

`web/js/kits/materials.js` exports lambert materials, vertex colors off, no default gray:

- moss `#3e6b45`, mushroom cap `#c4554a`, stem `#efe6d4`, trunk `#4a382c`, canopy `#1d3328`, fog `#d5e2d2`, sun `#ffe0b0`, ground `#6f8f62`

`web/js/kits/index.js` exports `makeKit(name)`:

- `moss_mound`: sphere scaled `(1.4, 0.45, 1.2)`, translated up so the base sits on y `0`
- `mushroom`: stem cylinder plus a flattened cap
- `fern`: three thin cones fanned apart
- `tree`: tapered cylinder 10 m tall (scale multiplies this) plus three canopy spheres. Base at y `0`

`web/js/main.js`:

- FogExp2 color `#d5e2d2`, density `0.018`. Hemisphere light plus a directional sun `#ffe0b0`.
- One `PlaneGeometry` from `(-48,-48)` to `(48,48)` in XZ, 64 segments. Displace each vertex by `groundHeight`. Color `#6f8f62`.
- Place about 40 kits around the spawn by hand in code: mounds, mushrooms, ferns, and two trees at scale `1.6` (16 m).
- Animate: horizontal velocity = `(right * moveX + forward * moveZ) * 3.2`. `y = groundHeight(x, z)`. Clamp XZ to the plane first, and also to `[-196, 196]`.
- First person: camera at feet + `(0, 1.55, 0)`, `lookAt` along forward with pitch. Hide the local avatar.
- Third person: camera at chest height, `4.2` m back along the horizontal forward, `lookAt` the chest. Show the avatar. Arms and legs swing only when speed exceeds `0.15`.
- `dt = min(clock.getDelta(), 0.05)`.

Static mount: `StaticFiles(directory=web, html=True)` on `/` after the health router, so `/health` stays the JSON route.

## README

Add:

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
docker compose up -d
python -m uvicorn forest_server.app:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/`. Keep the original purpose paragraphs.

## Done when

- `pytest -q` is green, including JS/Python ground parity and `db: ok`.
- `node web/world/check_ground.mjs` prints four numbers.
- Click, walk with WASD, look with the mouse, press `V`, and see moss, red caps, ferns, and two tall trunks. The feet stay on the ground.
- `/health` reports `"spots": 0`.

Commit once: the grove is walkable and the database is this game's alone.