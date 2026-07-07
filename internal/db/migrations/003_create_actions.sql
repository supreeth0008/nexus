-- 003_create_actions.sql
-- Remediation actions generated for incidents.

CREATE TABLE IF NOT EXISTS actions (
    id          TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents (id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('opentofu', 'kubernetes', 'helm')),
    summary     TEXT NOT NULL DEFAULT '',
    diff        TEXT NOT NULL DEFAULT '',
    risk        TEXT NOT NULL DEFAULT 'low' CHECK (risk IN ('low', 'medium', 'high')),
    status      TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN (
                    'proposed', 'validated', 'applied', 'rejected', 'rolled_back')),
    pr_url      TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    applied_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_actions_incident ON actions (incident_id);
