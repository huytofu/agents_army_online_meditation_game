CREATE TABLE last_coordinates (
    session_id uuid PRIMARY KEY REFERENCES sessions (id) ON DELETE CASCADE,
    x double precision NOT NULL,
    y double precision NOT NULL,
    z double precision NOT NULL,
    yaw double precision NOT NULL,
    pitch double precision NOT NULL,
    saved_at timestamptz NOT NULL DEFAULT now()
)
