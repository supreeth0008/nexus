-- 006_create_policies.sql
-- OPA policies stored for the policy gate. The rego column holds the
-- policy source; scope narrows applicability.

CREATE TABLE IF NOT EXISTS policies (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    rego        TEXT NOT NULL,
    scope       JSONB NOT NULL DEFAULT '{}'::jsonb,
    autonomy    INTEGER NOT NULL DEFAULT 0 CHECK (autonomy BETWEEN 0 AND 4),
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    version     INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_policies_enabled ON policies (enabled);
