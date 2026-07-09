# Nexus

[![CI](https://github.com/supreeth0008/nexus/actions/workflows/ci.yaml/badge.svg)](https://github.com/supreeth0008/nexus/actions/workflows/ci.yaml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](pyproject.toml)

Nexus is an **autonomous infrastructure control plane**. It observes cloud-native infrastructure, detects anomalies, diagnoses root causes, generates infrastructure-as-code fixes, validates them in shadow environments, applies them through GitOps pull requests, verifies recovery, and learns from every incident.

## Status: Phase 6 (Production Readiness) — v1.0.0 (2026-07-07)

The current build provides a complete closed-loop autonomous control plane:

- **CLI** built with Typer: `init`, `status`, `version`, `observe`, `cycle`, `migrate`, `detect`, `incidents`, `fix`, `run`, `dashboard`, `learn`, `runbook`, `serve`
- **Typed configuration** via Pydantic Settings from `nexus.yaml` with `NEXUS_` environment variable overrides
- **Structured logging** via structlog (text or JSON)
- **Core data models**: incident (enforced state machine), target, cycle, policy, action, remediation
- **PostgreSQL** connection layer with embedded, transactional SQL migrations (SQLAlchemy 2.0)
- **Store implementations** for incidents, targets, cycles, audit ledger
- **Observability probes**: Prometheus, Kubernetes, LocalStack (AWS local simulation)
- **5 analyzers**: statistical, cost, security, reliability, compliance
- **Diagnosis engine** with root-cause correlation
- **3 remediators**: OpenTofu (6 HCL templates), Kubernetes (HPA manifests), Helm (values overrides)
- **Shadow validator** for isolated fix validation
- **GitOps engine** with GitHub PR automation, branch management, OPA policy gate (L0–L4 autonomy)
- **Full-loop engine**: Observe → Detect → Diagnose → Generate → Validate → Policy → Apply → Verify → Document
- **Learning engine** with pattern frequency and fix-success tracking
- **Runbook generator** from incident history
- **FastAPI server** with API key + OIDC auth, rate limiting, audit HMAC signing, secrets redaction
- **React/TypeScript dashboard** (Vite) with live KPIs, incident timeline, MTTR sparklines, policy gate panel
- **CI pipeline**: GitHub Actions with PostgreSQL service, Ruff, MyPy, pytest, build + smoke test
- **Distroless Docker image** (Python 3.11 multi-stage)

## Quick Start

```bash
# Install via pipx (recommended) or uv/pip
pipx install nexus
# or: uv pip install nexus

# Initialize a project
nexus init --name my-project

# Configure nexus.yaml (database DSN, targets, autonomy level)
# Example: postgresql://user:pass@localhost:5432/nexus

# Run database migrations
nexus migrate

# Observe targets
nexus observe

# Run a full autonomous cycle (observe → detect → diagnose → fix → validate → apply → verify)
nexus run --autonomy 2   # L2 = auto-fix low risk

# List detected incidents
nexus incidents list

# Generate a fix for an incident
nexus fix generate <incident-id> --kind opentofu

# Start the HTTP API server
nexus serve

# Open the dashboard (Phase 5)
nexus dashboard
```

## Configuration

`nexus init` generates a commented `nexus.yaml`. Every value can be overridden with an environment variable using the `NEXUS_` prefix:

```bash
NEXUS_AUTONOMY_LEVEL=2 nexus run
NEXUS_DATABASE__DSN=postgresql://... nexus migrate
```

Key sections:
- `project` — name, environment
- `autonomy` — level (0–4) and policy
- `database` — PostgreSQL DSN
- `targets` — list of observed targets (Kubernetes, Prometheus, LocalStack)
- `engine` — HTTP port, cycle intervals

## Progressive Autonomy

| Level | Name | Behavior |
|-------|------|----------|
| 0 | Observe only | Detects and logs only. No action. |
| 1 | Recommend | Generates a fix and opens a PR for manual review. |
| 2 | Auto-fix low risk | Auto-applies fixes for low-risk issues. |
| 3 | Auto-fix with policy gate | Auto-applies only if OPA policy allows. |
| 4 | Full autonomy | All fixes applied automatically. |

## Project Layout

```
nexus/
├── api/              FastAPI server, middleware, routes
├── analyzer/         5 detection analyzers
├── audit/            Append-only audit ledger (JSONL + Loki)
├── cli.py            Typer CLI entry point (13 commands)
├── config/           Pydantic Settings, YAML + env loading
├── db/               SQLAlchemy 2.0, migrations, session
├── diagnosis/        Root-cause correlation engine
├── engine/           Cycle runner, full closed-loop engine
├── gitops/           GitHub PR automation, OPA policy gate
├── learning/         Pattern mining, fix-success tracking
├── models/           Pydantic models (incident, cycle, target, policy, action)
├── observe/          Probes (k8s, prometheus, localstack), runner
├── policy/           PolicyGate, OPA client
├── remediator/       OpenTofu, Kubernetes, Helm remediators
├── runbook/          Runbook generator from incidents
├── utils/            Logging, metrics, version info
└── validator/        Shadow validator (isolated tempdir)
```

## Roadmap

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation (CLI, config, models, DB, CI) | ✅ Done (2026-07-06) |
| 1 | Observe (probes for Prometheus, Kubernetes, LocalStack) | ✅ Done (2026-07-07) |
| 2 | Detect + Diagnose (5 analyzers, diagnosis engine) | ✅ Done (2026-07-07) |
| 3 | Fix + Validate (3 remediators, shadow validator) | ✅ Done (2026-07-07) |
| 4 | Apply + Verify (GitOps, OPA gate, verifier, full loop) | ✅ Done (2026-07-07) |
| 5 | Learn + Dashboard (learning engine, runbooks, React UI) | ✅ Done (2026-07-07) |
| 6 | Production Readiness (auth, rate limit, audit, Docker, CI, docs) | ✅ Done (2026-07-07) |
| 7+ | Multi-cloud providers (AWS, GCP, Azure), plugin SDK, HA control plane | 📋 Planned |

> **Note**: Nexus is **cloud-native, Kubernetes-first — multi-cloud on the roadmap**. Current probes target Kubernetes, Prometheus, and LocalStack (AWS local simulation). Real AWS/GCP/Azure providers are planned for Phase 7+.

## License

Apache 2.0. See the [LICENSE](LICENSE) file.