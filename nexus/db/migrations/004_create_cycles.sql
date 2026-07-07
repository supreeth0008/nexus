-- 004_create_cycles.sql
-- One row per closed-loop cycle run.

CREATE TABLE IF NOT EXISTS cycles (
    id                 TEXT PRIMARY KEY,
    started_at         TIMESTAMPTZ NOT NULL,
    completed_at       TIMESTAMPTZ,
    trigger            TEXT NOT NULL CHECK (trigger IN ('scheduled', 'event', 'manual')),
    status             TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'aborted')),

    observe_at         TIMESTAMPTZ,
    detect_at          TIMESTAMPTZ,
    diagnose_at        TIMESTAMPTZ,
    generate_at        TIMESTAMPTZ,
    validate_at        TIMESTAMPTZ,
    apply_at           TIMESTAMPTZ,
    verify_at          TIMESTAMPTZ,

    incidents_detected INTEGER NOT NULL DEFAULT 0,
    fixes_applied      INTEGER NOT NULL DEFAULT 0,
    errors             JSONB NOT NULL DEFAULT '[]'::jsonb,

    target_id          TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_cycles_started_at ON cycles (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_cycles_target     ON cycles (target_id);
