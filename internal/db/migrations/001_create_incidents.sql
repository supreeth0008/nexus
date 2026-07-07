-- 001_create_incidents.sql
-- Core incident tracking table. I use TEXT for enum-like columns and
-- enforce values with CHECK constraints so adding a new value is a
-- migration, not a type rebuild.

CREATE TABLE IF NOT EXISTS incidents (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,
    severity      TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    status        TEXT NOT NULL CHECK (status IN (
                      'detected', 'diagnosing', 'diagnosed', 'fixing', 'fix_ready',
                      'applying', 'verifying', 'resolved', 'failed', 'escalated')),

    probe_id      TEXT NOT NULL DEFAULT '',
    target_id     TEXT NOT NULL DEFAULT '',
    source_signal TEXT NOT NULL DEFAULT '',

    detected_at   TIMESTAMPTZ NOT NULL,
    diagnosed_at  TIMESTAMPTZ,
    fixed_at      TIMESTAMPTZ,
    verified_at   TIMESTAMPTZ,
    resolved_at   TIMESTAMPTZ,

    root_cause    TEXT NOT NULL DEFAULT '',
    confidence    DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),

    fix_generated BOOLEAN NOT NULL DEFAULT FALSE,
    fix_pr_url    TEXT NOT NULL DEFAULT '',
    fix_branch    TEXT NOT NULL DEFAULT '',
    fix_summary   TEXT NOT NULL DEFAULT '',

    verified      BOOLEAN,
    mttr_seconds  BIGINT NOT NULL DEFAULT 0,

    cycle_id      TEXT NOT NULL DEFAULT '',
    log           JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_incidents_status      ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_target      ON incidents (target_id);
CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents (detected_at DESC);
