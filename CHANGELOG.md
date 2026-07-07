# Changelog

I follow Semantic Versioning. All notable changes to Nexus are documented here – I write in first person.

## [0.6.1] - 2026-07-07
### Security – Hardening Release
- I added `nexus.security.auth`: API key + Bearer OIDC, constant-time HMAC compare, RBAC reader/operator/admin
- I added rate limiting: 120 req/min/IP – token bucket in-memory
- I added audit HMAC-SHA256 signing – `sign_audit()`
- I added secrets redaction – every log / API response passes through `redact()`
- I hardened FastAPI: CORS locked to localhost:5173, I never leak stack traces, I return 429 on throttle
- I improved error handling: every Analyzer/Remediator/Validator wrapped – I log to `cycle.errors`, I never crash the loop
- I upgraded Web UI: professional SaaS dashboard – KPI grid, incident table with severity badges, MTTR sparkline SVG, policy gate panel, security checklist – first-person copy throughout
- I added `nexus serve` – I run Uvicorn with proper signal handling
- CLI: 13 commands total – `init, status, version, observe, cycle, detect, fix, incidents, run, dashboard, learn, runbook, serve, migrate`

### Fixed
- I fixed provider validation – added `prometheus` to `VALID_PROVIDERS`
- I fixed CLI command registration – removed silent try/except shadowing that hid Phase 3+ commands after pip editable reinstall
- I fixed `.gitignore` – removed `/nexus` which was shadowing the Python `nexus/` package source – this was the root cause of the “stuck agent” file-loss bug in earlier chats

## [0.6.0] - 2026-07-07
### Production Readiness – Phase 6
- I added `SECURITY.md`, `docs/ARCHITECTURE.md`, `SETUP.md`, `SECURITY.md`, `TROUBLESHOOTING.md`, `PLUGIN_DEV.md`
- I shipped Dockerfile – distroless python3.11 multi-stage
- I finalized CI: GitHub Actions with Postgres service, ruff, mypy, pytest, build + smoke test
- I tagged `v0.6.0` – production-ready

## [0.5.0] - 2026-07-07
### Learn + Dashboard – Phase 5
- I implemented `LearningEngine` – pattern frequency + fix success tracking
- I implemented `RunbookGenerator` – auto Markdown runbooks
- I shipped FastAPI server – `/health`, `/v1/incidents`, `/v1/metrics`
- I shipped React/TypeScript dashboard – Vite, live KPIs, incident timeline
- CLI: `nexus dashboard`, `nexus learn stats`, `nexus runbook generate`

## [0.4.0] - 2026-07-07
### Apply + Verify – Phase 4 – closed loop
- I implemented `GitOpsEngine` – PR creation, branch manager `nexus/fix/<id>-<type>`
- I implemented `PolicyGate` + `OPAClient` – L0-L4 progressive autonomy
- I implemented `Verifier` – post-apply metrics comparison
- I implemented `AuditLedger` – append-only, JSONL + Loki export
- I implemented `FullLoopEngine` – Observe→Detect→Diagnose→Generate→Validate→Policy→Apply→Verify→Document
- CLI: `nexus run --autonomy 0-4`

## [0.3.0] - 2026-07-07
### Fix + Validate – Phase 3
- I implemented `Remediator` interface + registry
- I implemented `OpenTofuRemediator` – 6 HCL templates
- I implemented `KubernetesRemediator` – HPA manifest
- I implemented `HelmRemediator` – values override
- I implemented `ShadowValidator` – isolated tempdir, tofu validate
- CLI: `nexus fix generate`, `nexus fix preview`

## [0.2.0] - 2026-07-07
### Detect + Diagnose – Phase 2 – Python rewrite
- I migrated Phase 0 from Go → Python – Typer, Pydantic, SQLAlchemy, structlog
- I preserved 100% data model parity – incident state machine identical
- I implemented 5 analyzers: statistical, cost, security, reliability, compliance
- I implemented `DiagnosisEngine` – root cause correlation
- CLI: `nexus detect`, `nexus incidents list`
- I rewrote HANDOVER.md to first-person voice

## [0.1.0] - 2026-07-06
### Foundation – Phase 0 – initial Go scaffold (archived)
- I built Cobra CLI, Viper config, slog logging, PostgreSQL migrations, core models in Go
- I then rewrote in Python per maintainability decision – Git history preserves Go version at pre-0.2.0 tags
