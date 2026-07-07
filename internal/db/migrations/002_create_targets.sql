-- 002_create_targets.sql
-- Observed infrastructure targets. The auth column stores only the
-- authentication method and non-secret hints; credentials never enter
-- the database.

CREATE TABLE IF NOT EXISTS targets (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    provider   TEXT NOT NULL CHECK (provider IN ('aws', 'azure', 'gcp', 'kubernetes', 'localstack')),
    regions    JSONB NOT NULL DEFAULT '[]'::jsonb,
    endpoint   TEXT NOT NULL DEFAULT '',
    auth       JSONB NOT NULL DEFAULT '{}'::jsonb,
    status     TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'unreachable', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_targets_provider ON targets (provider);
