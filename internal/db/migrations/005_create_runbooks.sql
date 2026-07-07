-- 005_create_runbooks.sql
-- Auto-generated runbooks derived from resolved incidents.

CREATE TABLE IF NOT EXISTS runbooks (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    content_md    TEXT NOT NULL DEFAULT '',
    source_incident_id TEXT REFERENCES incidents (id) ON DELETE SET NULL,
    times_used    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_runbooks_type ON runbooks (incident_type);
