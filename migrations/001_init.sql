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
