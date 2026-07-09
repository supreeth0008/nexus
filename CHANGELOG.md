# Changelog

All notable changes to Nexus are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-08

### Security
- Added API key and Bearer OIDC authentication (`nexus.security.auth`)
- Added constant-time HMAC comparison for API keys
- Added RBAC roles: reader, operator, admin
- Added rate limiting: 120 req/min/IP (token bucket, in-memory)
- Added audit log HMAC-SHA256 signing (`sign_audit()`)
- Added secrets redaction on all log lines and API responses
- Hardened FastAPI: CORS restricted to localhost:5173, no stack traces leaked, 429 on throttle
- Wrapped all Analyzer/Remediator/Validator execution to log errors to `cycle.errors` without crashing the loop

### Added
- `nexus serve` command — runs Uvicorn with proper signal handling
- Web UI: professional SaaS dashboard with KPI grid, incident table with severity badges, MTTR sparkline SVG, policy gate panel, security checklist
- Distroless Dockerfile (Python 3.11 multi-stage)
- GitHub Actions CI with PostgreSQL service, Ruff, MyPy, pytest, build + smoke test
- Documentation: `SECURITY.md`, `docs/ARCHITECTURE.md`, `SETUP.md`, `TROUBLESHOOTING.md`, `PLUGIN_DEV.md`

### Fixed
- Provider validation: added `prometheus` to `VALID_PROVIDERS`
- CLI command registration: removed silent try/except that hid Phase 3+ commands after pip editable reinstall
- `.gitignore`: removed `/nexus` entry that shadowed the Python `nexus/` package source

### Changed
- Upgraded to version 1.0.0 (from 0.6.1) — production-ready release

## [0.6.0] - 2026-07-07

### Added
- **Phase 6 — Production Readiness**
  - Security hardening (auth, rate limiting, audit signing, secrets redaction)
  - FastAPI server with `/health`, `/v1/incidents`, `/v1/metrics`
  - Distroless Docker image
  - Complete CI pipeline
  - Production documentation suite
- **Phase 5 — Learn + Dashboard**
  - `LearningEngine` — pattern frequency and fix-success tracking
  - `RunbookGenerator` — auto-generates Markdown runbooks from incidents
  - React/TypeScript dashboard (Vite) with live KPIs, incident timeline
  - CLI: `nexus dashboard`, `nexus learn stats`, `nexus runbook generate`
- **Phase 4 — Apply + Verify (Closed Loop)**
  - `GitOpsEngine` — PR creation, branch manager `nexus/fix/<id>-<type>`
  - `PolicyGate` + `OPAClient` — L0–L4 progressive autonomy
  - `Verifier` — post-apply metrics comparison
  - `AuditLedger` — append-only JSONL + Loki export
  - `FullLoopEngine` — Observe→Detect→Diagnose→Generate→Validate→Policy→Apply→Verify→Document
  - CLI: `nexus run --autonomy 0-4`
- **Phase 3 — Fix + Validate**
  - `Remediator` interface and registry
  - `OpenTofuRemediator` — 6 HCL templates
  - `KubernetesRemediator` — HPA manifest generation
  - `HelmRemediator` — values override generation
  - `ShadowValidator` — isolated tempdir, `tofu validate`
  - CLI: `nexus fix generate`, `nexus fix preview`
- **Phase 2 — Detect + Diagnose (Python Rewrite)**
  - Migrated Phase 0 from Go → Python (Typer, Pydantic, SQLAlchemy, structlog)
  - Preserved 100% data model parity — incident state machine identical
  - 5 analyzers: statistical, cost, security, reliability, compliance
  - `DiagnosisEngine` — root cause correlation
  - CLI: `nexus detect`, `nexus incidents list`
- **Phase 1 — Observe**
  - Probes: Prometheus, Kubernetes, LocalStack (AWS local simulation)
  - Observe runner and cycle execution
- **Phase 0 — Foundation**
  - Typer CLI with commands: `init`, `status`, `version`, `observe`, `cycle`, `migrate`
  - Pydantic Settings configuration from `nexus.yaml` with `NEXUS_` env overrides
  - Structured logging via structlog
  - Core models: Incident (state machine), Target, Cycle, Policy, Action
  - SQLAlchemy 2.0 + PostgreSQL with embedded migrations
  - Stores for incidents, targets, cycles

## [0.1.0] - 2026-07-06

### Added
- Initial Go scaffold (archived): Cobra CLI, Viper config, slog logging, PostgreSQL migrations, core models
- Git history preserves Go version at pre-0.2.0 tags
- Rewritten in Python for maintainability (commit 5624b5c)

---

## Release Tags

| Version | Tag | Date | Notes |
|---------|-----|------|-------|
| 1.0.0 | `v1.0.0` | 2026-07-08 | Production-ready, security hardened |
| 0.6.0 | `v0.6.0` | 2026-07-07 | Phase 6 complete |
| 0.5.0 | `v0.5.0` | 2026-07-07 | Phase 5 complete |
| 0.4.0 | `v0.4.0` | 2026-07-07 | Phase 4 complete |
| 0.3.0 | `v0.3.0` | 2026-07-07 | Phase 3 complete |
| 0.2.0 | `v0.2.0` | 2026-07-07 | Phase 2 complete (Python rewrite) |
| 0.1.0 | `v0.1.0` | 2026-07-06 | Phase 0 Go scaffold |