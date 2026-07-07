# Nexus

Nexus is an autonomous infrastructure control plane. It observes multi-cloud infrastructure, detects anomalies, diagnoses root causes, generates infrastructure-as-code fixes, validates them in shadow environments, applies them through GitOps pull requests, verifies recovery, and learns from every incident.

## Status: Phase 0 (Foundation)

I have completed the Phase 0 scaffold. The current build provides:

- A working CLI built with Cobra and Viper (`init`, `status`, `version`, `completion`)
- Typed configuration loading from `nexus.yaml` with environment variable overrides (`NEXUS_` prefix) and eager validation
- Structured logging via the standard library `slog` package (text or JSON)
- Core data models: incident (with an enforced state machine), target, cycle, policy, and action
- A PostgreSQL connection layer with embedded, transactional SQL migrations
- Store implementations for incidents, targets, and cycles
- A Makefile, golangci-lint configuration, and a GitHub Actions CI pipeline
- Scripts for one-command development setup and a local Kind cluster

## Quick Start

```bash
# Build
make build

# Verify
./nexus version
./nexus init --name my-project
./nexus status

# Test
make test

# Optional: local Kubernetes cluster for later phases
./scripts/setup-dev.sh
./scripts/setup-kind.sh
```

## Configuration

`nexus init` generates a commented `nexus.yaml`. Every value can be overridden with an environment variable using the `NEXUS_` prefix, for example:

```bash
NEXUS_AUTONOMY_LEVEL=1 ./nexus status
```

## Progressive Autonomy

| Level | Name | Behavior |
|-------|------|----------|
| 0 | Observe only | Detects and logs only. No action. |
| 1 | Recommend | Generates a fix and opens a PR for manual review. |
| 2 | Auto-fix low risk | Auto-applies fixes for low-risk issues. |
| 3 | Auto-fix with policy gate | Auto-applies only if the OPA policy allows. |
| 4 | Full autonomy | All fixes are applied automatically. |

## Project Layout

```
main.go             Entry point
cmd/                CLI commands (Cobra)
internal/config/    Configuration loading and validation
internal/model/     Core data models
internal/db/        PostgreSQL layer with embedded migrations
internal/utils/     Logging, retry, version helpers
deploy/kind/        Local Kind cluster configuration
scripts/            Development environment scripts
.github/workflows/  CI pipeline
```

## Roadmap

| Phase | Name | Outcome |
|-------|------|---------|
| 0 | Foundation | CLI, config, models, database layer, CI (done) |
| 1 | Observe | Probes for Prometheus, Kubernetes, and LocalStack |
| 2 | Detect + Diagnose | Anomaly detection and root cause analysis |
| 3 | Fix + Validate | IaC fix generation and shadow validation |
| 4 | Apply + Verify | GitOps PRs, policy gates, and the full closed loop |
| 5 | Learn + Dashboard | Learning engine and web UI |
| 6 | Production Readiness | Security hardening, docs, release pipeline |

The full architecture and phase plan are documented in the project handover document.

## License

Apache 2.0. See the LICENSE file.
