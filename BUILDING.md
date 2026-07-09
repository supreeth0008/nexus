# Building Nexus

Nexus was built solo, with heavy use of AI coding agents for scaffolding, boilerplate, and test generation. All architecture, safety design decisions, and code review are mine.

## Build History

See [CHANGELOG.md](CHANGELOG.md) for versioned changes with real dates from git history.

## Security Note

A GitHub PAT was accidentally committed in an early scaffold (commit `c8dd724`, 2026-07-07). It was immediately rotated and purged from history via `git filter-repo` before any public push. No credentials remain in the repository.

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: Typer
- **Config**: Pydantic Settings (YAML + env)
- **DB**: SQLAlchemy 2.0 + PostgreSQL
- **Logging**: structlog
- **API**: FastAPI + Uvicorn
- **Auth**: API keys + OIDC, RBAC, rate limiting
- **GitOps**: GitHub API + OPA policy gate
- **UI**: React 18 + TypeScript + Vite
- **CI**: GitHub Actions (Ruff, MyPy, pytest, PostgreSQL service)
- **Container**: Distroless Python 3.11 multi-stage

## Design Principles

1. **Kubernetes-first** — probes, remediators, and GitOps target K8s natively
2. **Progressive autonomy** — L0 (observe) → L4 (full auto) via OPA policy
3. **Closed loop** — every cycle: observe → detect → diagnose → fix → validate → apply → verify → learn
4. **Audit everything** — append-only ledger, HMAC-signed, secrets redacted
5. **Fail safe** — analyzers/remediators/validators wrapped; errors logged, loop continues