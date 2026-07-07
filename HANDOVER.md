# NEXUS — Autonomous Infrastructure Control Plane

## Complete Project Handover Document
> **Implementation Note (July 2026):** I have migrated the Phase 0+1 implementation from Go to Python to accelerate AI/DevOps iteration while preserving the original architecture, data models, and closed-loop design. All CLI, config, models, DB layer, and observe probes are now Python (Typer, Pydantic, SQLAlchemy, FastAPI-ready). The original Go handover remains authoritative for architecture; this document has been updated to first-person voice and Python stack references where applicable.



---

# Section 1: The Project in One Minute

**Nexus** is a closed-loop autonomous infrastructure control plane. It observes your multi-cloud infrastructure, detects anomalies (cost, performance, security, compliance, reliability), diagnoses root causes, generates IaC fixes, validates them in shadow environments, applies them via GitOps PRs, verifies recovery, and learns from every incident — all without human intervention.

**One-liner:** *Nexus is the autopilot for your cloud infrastructure.*

**The unsolved problem it solves:** Every existing tool covers ONE part of the loop (monitoring sees problems, IaC defines state, GitOps syncs it, alerting notifies humans). **Nobody connects Observe → Detect → Diagnose → Fix → Validate → Apply → Verify → Learn into a single autonomous closed loop.** Nexus does.

**Tagline:** *Your cloud should heal itself. Nexus makes it happen.*

---

# Section 2: Core Architecture

## 2.1 The Closed Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEXUS CONTROL PLANE                       │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ OBSERVE  │──→│ DETECT   │──→│ DIAGNOSE │──→│ GENERATE │    │
│  │ (OTel +  │   │(Anomaly  │   │(Root     │   │(IaC fix  │    │
│  │ all      │   │ Detection)│   │ Cause)   │   │ as code) │    │
│  │ signals) │   │          │   │          │   │          │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│        │                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ VALIDATE │←──│ APPLY    │←──│ VERIFY   │←──│ DOCUMENT │    │
│  │ (Shadow  │   │ (GitOps  │   │ (Post-   │   │ (Auto    │    │
│  │  Env)    │   │  PR)     │   │  recovery│   │  Runbook)│    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│        │                                                         │
│        └──────────────────┬─────────────────────────────────────┘
│                           │
│                    ┌──────────┐
│                    │  LEARN   │
│                    │ (Improves│
│                    │  future  │
│                    │  cycles) │
│                    └──────────┘
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXUS CORE (Go Engine)                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                    Orchestrator                         │     │
│  │  ┌─────┐  ┌─────┐  ┌──────┐  ┌────┐  ┌──────┐       │     │
│  │  │Cycle│  │State│  │Policy│  │Audit│  │Config│       │     │
│  │  │Mgr  │  │Mgr  │  │Gate  │  │Log  │  │Mgr   │       │     │
│  │  └─────┘  └─────┘  └──────┘  └────┘  └──────┘       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                │                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ PROBES   │ │ANALYZERS │ │REMEDIATORS│ │VERIFIERS │          │
│  │(Pluggable│ │(Pluggable│ │(Pluggable │ │(Pluggable│          │
│  │ Adapters)│ │ Modules) │ │ Modules)  │ │ Modules) │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│       │            │            │            │                  │
│       ▼            ▼            ▼            ▼                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │               Integration Layer                         │     │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐       │     │
│  │  │Git/GH  │  │K8s API │  │Cloud   │  │OTel    │       │     │
│  │  │Client  │  │Client  │  │Provider │  │Client  │       │     │
│  │  │        │  │        │  │Clients  │  │        │       │     │
│  │  └────────┘  └────────┘  └────────┘  └────────┘       │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
    ┌────────┐     ┌────────┐      ┌────────┐      ┌────────┐
    │GitHub  │     │K8s     │      │Cloud   │      │OTel    │
    │(PRs)   │     │(Events)│      │(AWS/   │      │Backend │
    │        │     │        │      │GCP/AZ) │      │(Backend│
    └────────┘     └────────┘      └────────┘      └────────┘
```

## 2.3 Progressive Autonomy Levels

| Level | Name | Behavior | Use Case |
|-------|------|----------|----------|
| **0** | Observe Only | Detects and logs only. No action. | Baseline, trust-building |
| **1** | Recommend | Detects, generates fix, opens PR for manual review | Low-risk environments |
| **2** | Auto-Fix Low Risk | Auto-applies fixes for low-risk issues (cost, scaling) | Most production envs |
| **3** | Auto-Fix with Policy Gate | Auto-applies if OPA policy allows. Escalates otherwise | High-security envs |
| **4** | Full Autonomy | All fixes auto-applied. Nexus manages entire closed loop | Experimental/future |

---

# Section 3: Tech Stack — Detailed Rationale

## 3.1 Core Technology Choices

| Component | Choice | Why NOT the alternative | License |
|-----------|--------|------------------------|---------|
| **Core Language** | **Go** | Go is the cloud-native language. Best K8s client libraries, excellent concurrency, single-binary deployment, fast startup, cross-compilation. NOT Python (GIL, slower, harder to distribute) NOT Rust (steep learning curve, slower iteration for a project this size). | Free |
| **CLI Framework** | **Cobra + Viper** | Industry standard for Go CLIs. Used by K8s, Helm, OpenTofu, Docker. Automatic help generation, shell completion, config file binding. | Apache 2.0 |
| **IaC Engine** | **OpenTofu** | 100% Terraform-compatible. Free forever (Apache 2.0). Terraform moved to BSL license. OpenTofu supports state encryption, ephemeral resources, enabled meta-argument — Terraform doesn't. | Apache 2.0 |
| **IaC GitOps** | **Atlantis** | Free, open-source, PR-driven IaC workflow. Self-host in K8s. Terraform Cloud is proprietary and can't be self-hosted on free tier. | Apache 2.0 |
| **Monitoring** | **Prometheus + Grafana + Loki** | Industry standard. 100% free. Datadog is proprietary and expensive ($15+/host/month). Grafana Cloud free tier is limited. Self-hosted = unlimited. | Apache 2.0 |
| **Tracing** | **OpenTelemetry Collector** | Vendor-neutral, CNCF incubating. Supports all observability signals. Can be deployed as agent or gateway. | Apache 2.0 |
| **Policy** | **OPA (Open Policy Agent)** | CNCF graduated. Rego language is purpose-built for policy. Sentinel is proprietary to HashiCorp. Cerbos is narrower (authZ only). | Apache 2.0 |
| **Database** | **PostgreSQL (via CloudNativePG)** | Battle-tested, relational, supports JSONB for flexible schemas. SQLite has no concurrency for multi-agent Nexus. | PostgreSQL |
| **Secrets** | **Mozilla SOPS + Age** | Encrypted files in Git. No HashiCorp Vault dependency. No license fees. Works offline. | MPL 2.0 |
| **Container Runtime** | **Docker + Kind** | Kind is the standard for local K8s testing. Minikube is heavier (VM). K3d is good but has subtle K8s API differences. | Apache 2.0 |
| **CI/CD** | **GitHub Actions** | Free for public repos (unlimited minutes). Native GitHub integration. No separate CI server. | Free tier |
| **Container Registry** | **GitHub Container Registry** | Free, tightly integrated with GitHub Actions. No separate Docker Hub account needed. | Free |
| **AWS Simulation** | **LocalStack** | Free for core services. Simulates AWS APIs locally. No real AWS account needed for MVP. | Apache 2.0 |

## 3.2 Why NOT These Alternatives

| Rejected Option | Reason for Rejection |
|----------------|---------------------|
| **Terraform Cloud** | Proprietary. BSL license. Cannot run `terraform plan` without network access to HashiCorp. Expensive at scale. |
| **Pulumi Cloud** | Proprietary backend. State management requires their cloud. Self-hosted option is Business+ tier ($400+/month). |
| **Crossplane** | Too opinionated (requires K8s control plane). Heavy. Not compatible with existing Terraform/OpenTofu workflows. |
| **Ansible** | Not declarative. No state management. Push-based, not pull-based. Procedural drift is hard to detect. |
| **Datadog** | $15/host/month minimum. Data egress costs. Proprietary query language. No self-hosting option. |
| **HashiCorp Vault** | Heavy. Requires dedicated infrastructure. SOPS + Age handles my use case with zero infrastructure. |
| **Jenkins** | Heavy. Groovy pipelines. Plugin maintenance burden. GitHub Actions is simpler and native. |
| **Dynatrace** | $58/host/month. Proprietary. No self-hosting. AI features are locked behind enterprise tiers. |

## 3.3 Version Pinning (As of June 2026)

| Tool | Version | Notes |
|------|---------|-------|
| Go | 1.24+ | Latest stable |
| OpenTofu | 1.11+ | Not 1.9.x — use 1.11 for state encryption feature |
| Prometheus | 2.54+ | Latest stable |
| Grafana | 11.5+ | Latest OSS |
| Loki | 3.3+ | Latest stable |
| OPA | 0.72+ | Latest stable |
| Kind | 0.25+ | Latest stable |
| Atlantis | 0.32+ | Latest stable |
| OpenTelemetry Collector | 0.118+ | Contrib distribution |
| PostgreSQL (CNPG) | 1.24+ | CloudNativePG operator |
| Helm | 3.17+ | Latest stable |
| Docker | 27+ | Latest stable |
| LocalStack | 4.0+ | Pro free tier for core services |

---

# Section 4: Complete Directory Structure

```
nexus/
│
├── main.go                          # Entry point
├── go.mod                           # Go module definition
├── go.sum
├── Makefile                         # Build, test, lint, deploy targets
├── Dockerfile                       # Multi-stage build
├── .goreleaser.yaml                 # Release automation
├── .github/                         # GitHub configuration
│   ├── workflows/
│   │   ├── ci.yaml                  # CI: test, lint, build
│   │   ├── release.yaml             # CD: build binaries, publish Docker image
│   │   └── docs.yaml                # Documentation site deployment
│   └── CODEOWNERS                   # Code ownership
│
├── cmd/                             # CLI command definitions (Cobra)
│   ├── root.go                      # Root command, global flags, config load
│   ├── init.go                      # `nexus init` — scaffold project
│   ├── deploy.go                    # `nexus deploy` — deploy Nexus to cluster
│   ├── status.go                    # `nexus status` — show system health
│   ├── incidents.go                 # `nexus incidents` — list/view incidents
│   ├── policies.go                  # `nexus policies` — manage OPA policies
│   ├── targets.go                   # `nexus targets` — manage observed infra
│   ├── run.go                       # `nexus run` — execute one cycle manually
│   ├── version.go                   # `nexus version` — show version info
│   └── completion.go                # Shell completion generation
│
├── internal/                        # Private packages (not importable externally)
│   ├── config/
│   │   ├── config.go                # Configuration loading (Viper)
│   │   ├── defaults.go              # Default configuration values
│   │   └── validation.go            # Configuration validation
│   │
│   ├── engine/                      # Core orchestration engine
│   │   ├── engine.go                # Main engine: runs the closed loop
│   │   ├── cycle.go                 # One observation→fix cycle
│   │   ├── scheduler.go             # When to run cycles (cron, event-driven)
│   │   └── lifecycle.go             # Engine start/stop/health
│   │
│   ├── probe/                       # Observability probes (pluggable)
│   │   ├── probe.go                 # Prober interface
│   │   ├── registry.go              # Probe plugin registry
│   │   ├── prometheus/              # Prometheus probe
│   │   │   ├── prometheus.go
│   │   │   └── queries.go           # Predefined PromQL queries
│   │   ├── cloudwatch/              # AWS CloudWatch probe
│   │   │   ├── cloudwatch.go
│   │   │   └── metrics.go
│   │   ├── azuremonitor/            # Azure Monitor probe
│   │   │   ├── azuremonitor.go
│   │   │   └── metrics.go
│   │   ├── gcpmonitoring/           # GCP Cloud Monitoring probe
│   │   │   ├── gcpmonitoring.go
│   │   │   └── metrics.go
│   │   ├── kubernetes/              # K8s API probe (events, pod status)
│   │   │   ├── kubernetes.go
│   │   │   └── watchers.go
│   │   ├── opentelemetry/           # OTel collector integration
│   │   │   ├── otel.go
│   │   │   └── exporter.go
│   │   └── cost/                    # Cost probe (cloud billing APIs)
│   │       ├── cost.go
│   │       ├── aws.go
│   │       └── gcp.go
│   │
│   ├── analyzer/                    # Anomaly detection (pluggable)
│   │   ├── analyzer.go              # Analyzer interface
│   │   ├── registry.go              # Analyzer plugin registry
│   │   ├── statistical/             # Statistical anomaly detection
│   │   │   ├── statistical.go
│   │   │   ├── zscore.go
│   │   │   ├── moving_average.go
│   │   │   └── seasonality.go
│   │   ├── ml/                      # ML-based detection (simple models)
│   │   │   ├── ml.go
│   │   │   ├── isolation_forest.go
│   │   │   └── threshold.go
│   │   ├── cost/                    # Cost anomaly detection
│   │   │   ├── cost_analyzer.go
│   │   │   └── budget.go
│   │   ├── security/                # Security posture detection
│   │   │   ├── security.go
│   │   │   └── drift.go
│   │   ├── compliance/              # Compliance drift detection
│   │   │   └── compliance.go
│   │   └── reliability/             # Reliability/SLO analysis
│   │       ├── reliability.go
│   │       ├── slo.go
│   │       └── error_budget.go
│   │
│   ├── diagnosis/                   # Root cause analysis
│   │   ├── diagnosis.go             # Diagnosis engine
│   │   ├── correlation.go           # Correlate anomalies with changes
│   │   ├── git_history.go           # Query Git history for recent changes
│   │   ├── deployment_events.go     # Query deployment events
│   │   └── change_impact.go         # Assess impact of changes
│   │
│   ├── remediator/                  # Fix generation (pluggable)
│   │   ├── remediator.go            # Remediator interface
│   │   ├── registry.go              # Remediator plugin registry
│   │   ├── opentofu/                # OpenTofu-based fixes
│   │   │   ├── opentofu.go
│   │   │   ├── module_generator.go  # Generate .tf module changes
│   │   │   ├── hcl_templater.go     # HCL template rendering
│   │   │   └── templates/           # HCL templates for common fixes
│   │   │       ├── scale_up.tf.tmpl
│   │   │       ├── resize_instance.tf.tmpl
│   │   │       ├── fix_sg_rule.tf.tmpl
│   │   │       └── add_autoscaling.tf.tmpl
│   │   ├── kubernetes/              # K8s manifest-based fixes
│   │   │   ├── kubernetes.go
│   │   │   └── manifest_templater.go
│   │   └── helm/                    # Helm chart value changes
│   │       ├── helm.go
│   │       └── values_templater.go
│   │
│   ├── validator/                   # Fix validation in shadow environment
│   │   ├── validator.go             # Validator interface
│   │   ├── shadow_env.go            # Shadow environment manager
│   │   ├── opentofu_validate.go     # `tofu plan` in shadow env
│   │   ├── k8s_dry_run.go           # K8s dry-run validation
│   │   └── health_check.go          # Post-deploy health check
│   │
│   ├── gitops/                      # GitOps integration
│   │   ├── gitops.go                # GitOps interface
│   │   ├── github.go                # GitHub PR creation/management
│   │   ├── git.go                   # Git operations (clone, branch, commit, push)
│   │   ├── atlantis.go              # Atlantis webhook integration
│   │   └── branch_manager.go        # Branch naming, cleanup
│   │
│   ├── verifier/                    # Post-apply verification
│   │   ├── verifier.go              # Verifier interface
│   │   ├── metric_check.go          # Verify metrics return to normal
│   │   ├── health_check.go          # Verify service health endpoints
│   │   ├── log_check.go             # Verify no error logs
│   │   └── time_series.go           # Compare pre/post time series
│   │
│   ├── policy/                      # Policy engine integration
│   │   ├── policy.go                # Policy evaluation interface
│   │   ├── opa.go                   # OPA client
│   │   ├── rego/                    # Built-in Rego policies
│   │   │   ├── cost_policy.rego
│   │   │   ├── security_policy.rego
│   │   │   ├── compliance_policy.rego
│   │   │   └── autonomy_policy.rego
│   │   └── gate.go                  # Policy gate evaluation
│   │
│   ├── audit/                       # Audit logging
│   │   ├── audit.go                 # Audit logger
│   │   ├── ledger.go                # Append-only incident ledger
│   │   └── exporter.go              # Export audit data to external systems
│   │
│   ├── learning/                    # Learning from past incidents
│   │   ├── learning.go              # Learning engine
│   │   ├── incident_patterns.go     # Pattern recognition
│   │   ├── runbook_generator.go     # Auto-generate runbooks
│   │   └── feedback.go              # Feedback collection
│   │
│   ├── runbook/                     # Runbook management
│   │   ├── runbook.go               # Runbook data model
│   │   ├── template.go              # Runbook template rendering
│   │   └── store.go                 # Runbook storage
│   │
│   ├── model/                       # Data models
│   │   ├── incident.go              # Incident model
│   │   ├── probe.go                 # Probe config/model
│   │   ├── target.go                # Target (observed infra) model
│   │   ├── action.go                # Remediation action model
│   │   ├── policy.go                # Policy model
│   │   ├── cycle.go                 # Cycle run model
│   │   └── runbook.go               # Runbook model
│   │
│   ├── db/                          # Database layer
│   │   ├── db.go                    # Database connection and migrations
│   │   ├── migrations/              # SQL migration files
│   │   │   ├── 001_create_incidents.sql
│   │   │   ├── 002_create_targets.sql
│   │   │   ├── 003_create_actions.sql
│   │   │   ├── 004_create_cycles.sql
│   │   │   ├── 005_create_runbooks.sql
│   │   │   └── 006_create_policies.sql
│   │   ├── incident_store.go        # Incident CRUD
│   │   ├── target_store.go          # Target CRUD
│   │   └── cycle_store.go           # Cycle history CRUD
│   │
│   └── utils/                       # Shared utilities
│       ├── logger.go                # Structured logging
│       ├── retry.go                 # Retry with backoff
│       ├── version.go               # Build-time version injection
│       └── httputil.go              # HTTP client utilities
│
├── api/                             # API definitions
│   ├── openapi.yaml                 # OpenAPI 3.0 specification
│   ├── nexus/v1/                    # Protobuf definitions (future gRPC)
│   │   ├── nexus.proto
│   │   └── nexus_grpc.proto
│   └── handlers/                    # HTTP API handlers
│       ├── health.go
│       ├── incidents.go
│       ├── targets.go
│       └── metrics.go
│
├── web/                             # Web UI (React/TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Incidents.tsx
│   │   │   ├── Targets.tsx
│   │   │   ├── Policies.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── IncidentCard.tsx
│   │   │   ├── CycleTimeline.tsx
│   │   │   ├── TargetStatus.tsx
│   │   │   ├── PolicyEditor.tsx
│   │   │   └── Navbar.tsx
│   │   ├── hooks/
│   │   │   └── useApi.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── styles/
│   │       └── global.css
│   └── public/
│       └── favicon.svg
│
├── deploy/                          # Deployment manifests
│   ├── kind/
│   │   └── kind-config.yaml         # Local Kind cluster config
│   ├── helm/
│   │   └── nexus/                   # Helm chart for Nexus itself
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       ├── values.dev.yaml
│   │       ├── values.prod.yaml
│   │       └── templates/
│   │           ├── deployment.yaml
│   │           ├── service.yaml
│   │           ├── configmap.yaml
│   │           ├── secrets.yaml
│   │           ├── pvc.yaml
│   │           ├── rbac.yaml
│   │           └── ingress.yaml
│   ├── docker-compose/              # Alternative deployment
│   │   ├── docker-compose.yaml
│   │   └── docker-compose.dev.yaml
│   └── monitoring/                  # Observability stack manifests
│       ├── prometheus/
│       │   ├── prometheus.yaml
│       │   └── rules/
│       │       └── nexus_alerts.yaml
│       ├── grafana/
│       │   ├── grafana.yaml
│       │   ├── datasources/
│       │   │   └── prometheus.yaml
│       │   └── dashboards/
│       │       ├── nexus_overview.json
│       │       └── incident_timeline.json
│       └── loki/
│           ├── loki.yaml
│           └── config.yaml
│
├── examples/                        # Example configurations
│   ├── nexus.yaml                   # Example project config
│   ├── policies/
│   │   ├── cost-anomaly.rego        # Example cost policy
│   │   └── security-drift.rego      # Example security policy
│   └── targets/
│       ├── aws-prod.yaml            # Example AWS production target
│       └── k8s-staging.yaml         # Example K8s staging target
│
├── tests/                           # Test infrastructure
│   ├── integration/                 # Integration tests
│   │   ├── full_cycle_test.go
│   │   ├── policy_eval_test.go
│   │   └── gitops_test.go
│   ├── e2e/                         # End-to-end tests
│   │   ├── e2e_test.go
│   │   └── scenarios/
│   │       ├── cost_spike.yaml
│   │       ├── security_drift.yaml
│   │       └── pod_crash.yaml
│   └── fixtures/                    # Test data
│       ├── sample_metrics.json
│       └── sample_incidents.json
│
├── docs/                            # Documentation
│   ├── README.md                    # Main README
│   ├── ARCHITECTURE.md              # Architecture deep-dive
│   ├── SETUP.md                     # Setup guide
│   ├── PHASES.md                    # Phase-by-phase build plan
│   ├── DESIGN_DECISIONS.md          # Key design decisions and rationale
│   ├── PLUGIN_DEV.md                # How to write a probe/analyzer/remediator
│   ├── POLICY_WRITING.md            # How to write Rego policies
│   ├── SECURITY.md                  # Security model and threat analysis
│   ├── TROUBLESHOOTING.md           # Common issues and solutions
│   └── ROADMAP.md                   # Future plans
│
└── scripts/                         # Development scripts
    ├── setup-dev.sh                 # One-command dev environment setup
    ├── setup-kind.sh                # Kind cluster setup
    ├── deploy-demo-app.sh           # Deploy demo target application
    ├── inject-failure.sh            # Inject test failures
    ├── teardown.sh                  # Cleanup everything
    └── seed-policies.sh             # Load default OPA policies
```

---

# Section 5: Data Models

## 5.1 Incident Model

```go
// internal/model/incident.go

type Incident struct {
    ID           string         `json:"id" db:"id"`
    Type         IncidentType   `json:"type" db:"type"`
    Severity     Severity       `json:"severity" db:"severity"`
    Status       IncidentStatus `json:"status" db:"status"`
    
    // Source
    ProbeID      string         `json:"probe_id" db:"probe_id"`
    TargetID     string         `json:"target_id" db:"target_id"`
    SourceSignal string         `json:"source_signal" db:"source_signal"`
    
    // Timelines
    DetectedAt   time.Time      `json:"detected_at" db:"detected_at"`
    DiagnosedAt  *time.Time     `json:"diagnosed_at,omitempty" db:"diagnosed_at"`
    FixedAt      *time.Time     `json:"fixed_at,omitempty" db:"fixed_at"`
    VerifiedAt   *time.Time     `json:"verified_at,omitempty" db:"verified_at"`
    ResolvedAt   *time.Time     `json:"resolved_at,omitempty" db:"resolved_at"`
    
    // Diagnosis
    RootCause    string         `json:"root_cause" db:"root_cause"`
    Confidence   float64        `json:"confidence" db:"confidence"` // 0.0-1.0
    
    // Fix
    FixGenerated bool           `json:"fix_generated" db:"fix_generated"`
    FixPR        string         `json:"fix_pr_url" db:"fix_pr_url"`
    FixBranch    string         `json:"fix_branch" db:"fix_branch"`
    FixSummary   string         `json:"fix_summary" db:"fix_summary"`
    
    // Verification
    Verified     *bool          `json:"verified,omitempty" db:"verified"`
    MTTRSeconds  int64          `json:"mttr_seconds" db:"mttr_seconds"` // Mean Time To Recover
    
    // Audit
    CycleID      string         `json:"cycle_id" db:"cycle_id"`
    Log          json.RawMessage`json:"log" db:"log"` // Append-only audit trail
    Metadata     map[string]any `json:"metadata" db:"metadata"`
}

type IncidentType string
const (
    IncidentCostSpike        IncidentType = "cost_spike"
    IncidentPerformance      IncidentType = "performance_degradation"
    IncidentSecurityDrift    IncidentType = "security_drift"
    IncidentComplianceDrift  IncidentType = "compliance_drift"
    IncidentReliability      IncidentType = "reliability_degradation"
    IncidentScale            IncidentType = "scaling_bottleneck"
    IncidentConfigDrift      IncidentType = "configuration_drift"
    IncidentResourceExhaust  IncidentType = "resource_exhaustion"
    IncidentErrorBurst       IncidentType = "error_burst"
    IncidentCustom           IncidentType = "custom"
)

type Severity string
const (
    SeverityCritical Severity = "critical"
    SeverityHigh     Severity = "high"
    SeverityMedium   Severity = "medium"
    SeverityLow      Severity = "low"
    SeverityInfo     Severity = "info"
)

type IncidentStatus string
const (
    StatusDetected     IncidentStatus = "detected"
    StatusDiagnosing   IncidentStatus = "diagnosing"
    StatusDiagnosed    IncidentStatus = "diagnosed"
    StatusFixing       IncidentStatus = "fixing"
    StatusFixReady     IncidentStatus = "fix_ready"     // PR open, awaiting approval
    StatusApplying     IncidentStatus = "applying"
    StatusVerifying    IncidentStatus = "verifying"
    StatusResolved     IncidentStatus = "resolved"
    StatusFailed       IncidentStatus = "failed"
    StatusEscalated    IncidentStatus = "escalated"     // Policy gate blocked
)
```

## 5.2 Target Model

```go
type Target struct {
    ID        string        `json:"id" db:"id"`
    Name      string        `json:"name" db:"name"`
    Provider  CloudProvider `json:"provider" db:"provider"` // aws, azure, gcp, kubernetes, localstack
    Regions   []string      `json:"regions" db:"regions"`
    Endpoint  string        `json:"endpoint" db:"endpoint"` // API endpoint
    Auth      TargetAuth    `json:"auth" db:"auth"`         // Encrypted
    Status    TargetStatus  `json:"status" db:"status"`
    CreatedAt time.Time     `json:"created_at" db:"created_at"`
    UpdatedAt time.Time     `json:"updated_at" db:"updated_at"`
}

type TargetAuth struct {
    Method  string `json:"method"`  // env, iam, oidc, static
    Profile string `json:"profile,omitempty"`
    Region  string `json:"region,omitempty"`
}

type CloudProvider string
const (
    ProviderAWS        CloudProvider = "aws"
    ProviderAzure      CloudProvider = "azure"
    ProviderGCP        CloudProvider = "gcp"
    ProviderK8s        CloudProvider = "kubernetes"
    ProviderLocalStack CloudProvider = "localstack"
)
```

## 5.3 Cycle Model

```go
type Cycle struct {
    ID            string        `json:"id" db:"id"`
    StartedAt     time.Time     `json:"started_at" db:"started_at"`
    CompletedAt   *time.Time    `json:"completed_at,omitempty" db:"completed_at"`
    Trigger       CycleTrigger  `json:"trigger" db:"trigger"` // scheduled, event, manual
    Status        CycleStatus   `json:"status" db:"status"`
    
    // Phase timestamps
    ObserveAt     *time.Time    `json:"observe_at,omitempty" db:"observe_at"`
    DetectAt      *time.Time    `json:"detect_at,omitempty" db:"detect_at"`
    DiagnoseAt    *time.Time    `json:"diagnose_at,omitempty" db:"diagnose_at"`
    GenerateAt    *time.Time    `json:"generate_at,omitempty" db:"generate_at"`
    ValidateAt    *time.Time    `json:"validate_at,omitempty" db:"validate_at"`
    ApplyAt       *time.Time    `json:"apply_at,omitempty" db:"apply_at"`
    VerifyAt      *time.Time    `json:"verify_at,omitempty" db:"verify_at"`
    
    // Results
    IncidentsDetected int       `json:"incidents_detected" db:"incidents_detected"`
    FixesApplied      int       `json:"fixes_applied" db:"fixes_applied"`
    Errors            []string  `json:"errors" db:"errors"`
    
    TargetID          string    `json:"target_id" db:"target_id"`
}
```

## 5.4 Policy Model

```go
type Policy struct {
    ID          string         `json:"id" db:"id"`
    Name        string         `json:"name" db:"name"`
    Description string         `json:"description" db:"description"`
    Rego        string         `json:"rego" db:"rego"`          // The Rego policy code
    Scope       PolicyScope    `json:"scope" db:"scope"`         // which incident types this applies to
    Autonomy    AutonomyLevel  `json:"autonomy" db:"autonomy"`   // what level this policy allows
    Enabled     bool           `json:"enabled" db:"enabled"`
    Version     int            `json:"version" db:"version"`
    CreatedAt   time.Time      `json:"created_at" db:"created_at"`
    UpdatedAt   time.Time      `json:"updated_at" db:"updated_at"`
}

type PolicyScope struct {
    IncidentTypes []IncidentType `json:"incident_types,omitempty"`
    Targets       []string       `json:"targets,omitempty"`      // target IDs, empty = all
    Providers     []string       `json:"providers,omitempty"`    // aws, azure, etc.
    TimeWindow    string         `json:"time_window,omitempty"`  // "09:00-17:00", "always"
}
```

---

# Section 6: API Contracts

## 6.1 Internal HTTP API

Nexus exposes an HTTP API on port 8080 (configurable).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/v1/incidents` | List incidents (paginated, filterable) |
| `GET` | `/v1/incidents/:id` | Get incident details |
| `GET` | `/v1/incidents/:id/log` | Get incident audit log |
| `POST` | `/v1/incidents/:id/approve` | Approve a pending fix |
| `POST` | `/v1/incidents/:id/reject` | Reject a pending fix |
| `GET` | `/v1/targets` | List targets |
| `POST` | `/v1/targets` | Register a new target |
| `DELETE` | `/v1/targets/:id` | Remove a target |
| `GET` | `/v1/cycles` | List cycles |
| `GET` | `/v1/cycles/:id` | Get cycle details |
| `POST` | `/v1/cycles` | Trigger a manual cycle |
| `GET` | `/v1/policies` | List policies |
| `POST` | `/v1/policies` | Create/update a policy |
| `GET` | `/v1/metrics` | Prometheus metrics endpoint |
| `POST` | `/v1/webhook/github` | GitHub webhook receiver |

## 6.2 OpenAPI Specification

See `api/openapi.yaml` for the full OpenAPI 3.0 specification.

## 6.3 Protobuf (Future)

See `api/nexus/v1/nexus.proto` for gRPC service definitions (planned for Phase 5).

---

# Section 7: Key Design Decisions (With Rationale)

## 7.1 Why Go, Not Python, Rust, or TypeScript

| Language | Pro | Con | Verdict |
|----------|-----|-----|---------|
| **Go** | Fast compilation, excellent concurrency (goroutines), single-binary deployment, best K8s client libraries, huge cloud-native ecosystem | Slightly verbose error handling | ✅ **Chosen** |
| Python | Easy to write, huge ML ecosystem | GIL, slow, hard to distribute (no single binary), poor concurrency | ❌ Wrong tool for an infrastructure engine |
| Rust | Zero-cost abstractions, memory safety | Steep learning curve, slow compilation, smaller ecosystem for cloud tools | ❌ Too slow to iterate |
| TypeScript/Node | Fast prototyping | Single-threaded, heavy runtime, not native on edge | ❌ Not suitable for core infrastructure engine |

## 7.2 Why OpenTofu Over Terraform

| Factor | OpenTofu | Terraform |
|--------|----------|-----------|
| **License** | Apache 2.0 (free forever) | BSL (source-available, restricted) |
| **State encryption** | Built-in | Not available |
| **Ephemeral resources** | Yes | No |
| **`enabled` meta-argument** | Yes | No |
| **Client-side state encryption** | Yes | No |
| **HCP/TFC dependency** | None | TFC for team features |
| **Self-hostable backend** | S3, GCS, Azure, HTTP, etc. | Same, but TFC is locked |
| **Community growth** | Accelerating (Linux Foundation) | Declining (HashiCorp owned) |
| **Provider compatibility** | 100% with Terraform providers | N/A |

**Decision:** OpenTofu. With one caveat — do NOT use OpenTofu-only features (state encryption, ephemeral resources) until the project is fully committed to OpenTofu, because they break round-trip compatibility with Terraform.

## 7.3 Why PostgreSQL Over SQLite or MongoDB

| Factor | PostgreSQL | SQLite | MongoDB |
|--------|-----------|--------|---------|
| **Concurrent access** | Excellent | Single-writer | Excellent |
| **JSON support** | Native JSONB | Limited JSON | Native documents |
| **Migrations** | Mature tooling (golang-migrate) | Limited | Schema validation |
| **K8s operator** | CloudNativePG (mature) | Not available | MongoDB operator |
| **Self-hosted** | Yes | Yes | Yes |
| **ACID compliance** | Full | Full | Document-level |
| **Backup tooling** | Excellent (pg_dump, WAL archiving) | File copy | mongodump |

**Decision:** PostgreSQL via CloudNativePG operator. SQLite is fine for single-node demos but won't scale to multi-instance Nexus. MongoDB's lack of joins and weaker consistency model makes it harder for a relational incident tracking system.

## 7.4 Why OPA Over Custom Policy Engine

- OPA is CNCF graduated (production trust)
- Rego is declarative and purpose-built for policy
- OPA can run as a sidecar (low latency, no network hop)
- Policy-as-code means policies are versioned in Git
- OPA supports partial evaluation (pre-compute decisions)
- OPA has a rich ecosystem of tools (conftest, regal, opa fmt)

## 7.5 Why Atlantis Over Terraform Cloud

- Atlantis is free (open source)
- Self-hosted in your own K8s cluster
- No data leaves your infrastructure
- PR-driven workflow (works with any Git provider)
- No per-user licensing
- Can be extended with custom workflows

## 7.6 Why LocalStack for MVP, Real Clouds Later

- No AWS account needed for development
- Instant provisioning (no 5-minute EC2 wait times)
- Can simulate failure states that are hard to reproduce in real cloud
- 100% API-compatible with AWS
- Free for core services
- Same OpenTofu provider works against both LocalStack and real AWS

---

# Section 8: Phase-by-Phase Build Plan

---

## PHASE 0: Foundation — "The Scaffold"
**Goal:** Working CLI, config loading, local dev environment, CI pipeline.
**Duration:** 7-10 days
**Burnout Checkpoint:** ✅ After this phase, you have a running CLI and dev env.

### Tasks

- [x] Initialize Go module (`go mod init github.com/arenasys/nexus`)
- [ ] Set up Cobra CLI skeleton (root, version, completion commands)
- [ ] Implement Viper config loading (`nexus.yaml` → struct)
- [ ] Create Makefile with `build`, `test`, `lint`, `clean` targets
- [ ] Set up GitHub repository (public, with topics)
- [ ] Create `.github/workflows/ci.yaml` (lint, test, build on PR/push)
- [ ] Write `scripts/setup-dev.sh` — one-command dev environment
- [ ] Write `deploy/kind/kind-config.yaml` + `scripts/setup-kind.sh`
- [ ] Set up Go linter (golangci-lint) with strict rules
- [ ] Implement structured logging (zerolog or slog)
- [ ] Create database connection layer with migrations framework
- [ ] Write core data models (incident, target, cycle, policy, action)
- [ ] Write initial database migrations (CREATE TABLE statements)
- [ ] Create `HANDOVER.md` checkpoint (you're reading it)

### Success Criteria

```bash
# After this phase:
nexus version          # → "Nexus v0.1.0-dev"
nexus init --name my-project  # → Creates ./nexus.yaml
nexus status           # → "No targets configured"

# Kind cluster is running:
kubectl get nodes      # → 1 node ready
```

### Files Created
- `main.go`, `cmd/root.go`, `cmd/version.go`, `cmd/completion.go`
- `internal/config/config.go`, `internal/utils/logger.go`
- `internal/db/db.go`, `internal/db/migrations/001_*.sql`
- `internal/model/*.go`
- `Makefile`, `.github/workflows/ci.yaml`, `scripts/setup-dev.sh`
- `deploy/kind/kind-config.yaml`

---

## PHASE 1: Observe — "Eyes Open"
**Goal:** Nexus can connect to targets, collect observability data, and store it.
**Duration:** 10-14 days
**Burnout Checkpoint:** ✅ After this phase, you can run `nexus observe` and SEE your infrastructure.

### Tasks

- [ ] Define `Prober` interface in `internal/probe/probe.go`
- [ ] Implement probe plugin registry
- [ ] Implement Prometheus probe:
  - [ ] Connect to Prometheus API
  - [ ] Run predefined PromQL queries
  - [ ] Store results
  - [ ] Support custom queries
- [ ] Implement Kubernetes probe:
  - [ ] Watch for pod state changes
  - [ ] Watch for deployment events
  - [ ] Collect resource utilization
- [ ] Implement LocalStack probe (mock AWS):
  - [ ] EC2 instance status
  - [ ] S3 bucket policies
  - [ ] Security group rules
  - [ ] Cost explorer mock
- [ ] Implement OpenTelemetry Collector integration:
  - [ ] Deploy OTel collector as sidecar
  - [ ] Forward metrics to Nexus
  - [ ] Support traces and logs
- [ ] Create `nexus target add` CLI command
- [ ] Create `nexus target list` CLI command
- [ ] Create `nexus observe` CLI command (one-shot observation)
- [ ] Store observation data in PostgreSQL
- [ ] Deploy demo target application:
  - [ ] Simple Go microservice with metrics
  - [ ] Expose Prometheus metrics endpoint
  - [ ] Deploy to Kind cluster
- [ ] Deploy Prometheus + Grafana stack to Kind

### Success Criteria

```bash
# After this phase:
nexus target add --name demo-k8s --provider kubernetes --endpoint https://...
nexus target add --name demo-aws --provider localstack --endpoint http://...

nexus observe --target demo-k8s  # → Returns pod states, resource usage
nexus observe --target demo-aws  # → Returns EC2 status, S3 bucket info

# Prometheus is scraping:
curl localhost:9090/api/v1/query?query=up  # → Returns target health

# Grafana shows Nexus metrics:
# Dashboard: "Nexus - Target Overview"
```

### New Files Created
- `internal/probe/*.go`, `internal/probe/prometheus/*.go`
- `internal/probe/kubernetes/*.go`, `internal/probe/localstack/*.go` (actually `probe/cloudwatch` but using LocalStack endpoint)
- `cmd/targets.go`, `cmd/observe.go`
- `deploy/monitoring/prometheus/*.yaml`, `deploy/monitoring/grafana/*.yaml`
- `scripts/deploy-demo-app.sh`

---

## PHASE 2: Detect + Diagnose — "The Brain"
**Goal:** Nexus can detect anomalies in observed data and diagnose root causes.
**Duration:** 14-18 days
**Burnout Checkpoint:** ✅ After this phase, Nexus can FIND problems automatically.

### Tasks

- [ ] Define `Analyzer` interface in `internal/analyzer/analyzer.go`
- [ ] Implement analyzer plugin registry
- [ ] Implement statistical anomaly detection:
  - [ ] Z-score based outlier detection
  - [ ] Moving average baseline
  - [ ] Seasonality detection
  - [ ] Configurable sensitivity
- [ ] Implement cost anomaly detection:
  - [ ] Detect cost spikes vs baseline
  - [ ] Track spend by service/resource
  - [ ] Budget-based alerts
- [ ] Implement security posture detection:
  - [ ] Detect open S3 buckets
  - [ ] Detect overly permissive security groups
  - [ ] Detect unencrypted resources
- [ ] Implement reliability degradation detection:
  - [ ] Error rate increase
  - [ ] Latency increase
  - [ ] Pod restart count increase
  - [ ] SLO burn rate
- [ ] Implement compliance drift detection:
  - [ ] Tagging policy violations
  - [ ] Region restrictions
  - [ ] Instance type restrictions
- [ ] Implement Diagnosis Engine:
  - [ ] Correlate anomalies with recent Git commits
  - [ ] Correlate with recent deployment events
  - [ ] Check K8s events for recent changes
  - [ ] Generate root cause hypothesis with confidence score
- [ ] Create `internal/diagnosis/git_history.go`:
  - [ ] Clone target IaC repo
  - [ ] Parse git log for relevant changes
  - [ ] Score changes by likelihood of causing anomaly
- [ ] Create `internal/engine/cycle.go` — one full observation→detection cycle
- [ ] Store incidents in database with proper status tracking
- [ ] Create `nexus incidents list` CLI command
- [ ] Create Grafana dashboard for active incidents

### Success Criteria

```bash
# After this phase:
nexus detect --target demo-k8s      # → Returns detected anomalies
nexus detect --target demo-aws      # → Returns security findings
nexus incidents list                 # → Shows detected incidents
nexus incidents view <id>            # → Shows root cause diagnosis

# Grafana dashboard shows:
# - Active incident count
# - Incident types breakdown
# - Detection latency
# - False positive rate
```

### New Files Created
- `internal/analyzer/*.go`, `internal/analyzer/statistical/*.go`
- `internal/analyzer/cost/*.go`, `internal/analyzer/security/*.go`
- `internal/analyzer/compliance/*.go`, `internal/analyzer/reliability/*.go`
- `internal/diagnosis/*.go`
- `internal/engine/cycle.go`
- `cmd/detect.go`, `cmd/incidents.go`
- `deploy/monitoring/grafana/dashboards/incident_overview.json`

---

## PHASE 3: Fix + Validate — "The Healer"
**Goal:** Nexus can generate IaC fixes and validate them before applying.
**Duration:** 14-18 days
**Burnout Checkpoint:** ✅ After this phase, Nexus can GENERATE fixes. This is the "wow" moment.

### Tasks

- [ ] Define `Remediator` interface in `internal/remediator/remediator.go`
- [ ] Implement remediator plugin registry
- [ ] Implement OpenTofu fix generator:
  - [ ] Module templates for common fixes (scale up, resize, fix security groups)
  - [ ] HCL template rendering engine
  - [ ] Template for: increase ASG min/max
  - [ ] Template for: resize EC2 instance
  - [ ] Template for: fix open security group rule
  - [ ] Template for: add missing tags
  - [ ] Template for: enable encryption
- [ ] Implement K8s manifest fix generator:
  - [ ] Template for: update HPA min/max replicas
  - [ ] Template for: update resource requests/limits
  - [ ] Template for: add pod disruption budget
  - [ ] Template for: update deployment strategy
- [ ] Implement Helm values fix generator:
  - [ ] Template for: update Helm values.yaml
  - [ ] Template for: scale replicas via Helm
- [ ] Implement Validator:
  - [ ] Create shadow environment (namespace in K8s, or `tofu plan` in isolation)
  - [ ] Run `tofu plan` in shadow environment
  - [ ] Run `kubectl apply --dry-run=server` for K8s manifests
  - [ ] Run health checks against shadow deployment
  - [ ] Compare expected outcome vs actual
- [ ] Implement `internal/remediator/opentofu/module_generator.go`:
  - [ ] Read existing .tf files from repo
  - [ ] Parse resource blocks
  - [ ] Generate modified .tf content
  - [ ] Write to branch
- [ ] Create HCL template files in `internal/remediator/opentofu/templates/`
- [ ] Wire fix generation into cycle engine
- [ ] Create `nexus fix generate` CLI command (show generated fix without applying)
- [ ] Create `nexus fix preview` CLI command (preview changes)

### Success Criteria

```bash
# After this phase:
nexus fix generate --incident <id>   # → Shows generated OpenTofu diff
nexus fix preview --incident <id>    # → Runs opentofu plan in shadow env

# Generated fixes look like:
# + resource "aws_autoscaling_group" "app" {
#     min_size         = 2 → 3
#     max_size         = 5 → 10
#   }

# Fix templates exist for:
# - Scale up compute (ASG, ECS, K8s HPA)
# - Resize instance types
# - Fix security group rules
# - Add missing resource tags
# - Enable encryption on storage
```

### New Files Created
- `internal/remediator/*.go`, `internal/remediator/opentofu/*.go`
- `internal/remediator/opentofu/templates/*.tf.tmpl`
- `internal/remediator/kubernetes/*.go`
- `internal/remediator/helm/*.go`
- `internal/validator/*.go`
- `cmd/fix.go`

---

## PHASE 4: Apply + Verify — "The Closed Loop"
**Goal:** The full closed loop: Observe → Detect → Diagnose → Fix → Validate → Apply → Verify → Document.
**Duration:** 14-18 days
**Burnout Checkpoint:** ✅ After this phase, Nexus is AUTONOMOUS. Massive milestone.

### Tasks

- [ ] Implement GitOps integration:
  - [ ] Create Git client (clone, branch, commit, push)
  - [ ] Create GitHub client (create PR, add labels, request reviewers)
  - [ ] Branch naming convention: `nexus/fix/<incident-id>-<type>`
  - [ ] PR template with incident details and expected outcome
- [ ] Implement Atlantis integration:
  - [ ] Configure Atlantis to auto-approve Nexus PRs based on labels
  - [ ] Webhook receiver for Atlantis events (plan succeeded, apply succeeded)
  - [ ] Wait for Atlantis to run plan before proceeding
- [ ] Implement Policy Gate:
  - [ ] OPA client to evaluate policies
  - [ ] Policy input: incident type, severity, target, proposed fix
  - [ ] Policy decision: allow, deny, require_approval
  - [ ] Autonomy level enforcement
- [ ] Implement Verifier:
  - [ ] Post-apply: re-collect metrics
  - [ ] Compare pre/post anomaly scores
  - [ ] Verify metrics return to expected baseline
  - [ ] Verify no new errors introduced
  - [ ] Mark incident resolved or rollback
- [ ] Implement full cycle orchestration in `internal/engine/engine.go`:
  - [ ] Scheduler (run cycle every N minutes)
  - [ ] Event-driven trigger (webhook from monitoring)
  - [ ] Manual trigger via `nexus run`
  - [ ] Graceful error handling at each phase
  - [ ] Phase timeout enforcement
  - [ ] Rollback on verification failure
- [ ] Implement cycle state machine (status transitions with validation)
- [ ] Create `nexus run` CLI command (manual cycle trigger)
- [ ] Create `nexus status` dashboard with cycle health
- [ ] Implement audit logging:
  - [ ] Append-only ledger per incident
  - [ ] Log: raw signals, correlation results, generated fix, policy decision, PR URL, verification results
  - [ ] Export to Loki for long-term storage
- [ ] Write demo scenario: `scripts/inject-failure.sh` that causes a known issue

### Success Criteria

```bash
# After this phase — THIS IS THE MAGIC MOMENT:

# 1. Inject a failure:
./scripts/inject-failure.sh cpu-spike  # Spikes CPU on demo app

# 2. Watch Nexus auto-detect:
nexus incidents list  # → New incident: "CPU utilization exceeds threshold"

# 3. Watch Nexus diagnose:
nexus incidents view <id>  # → "HPA max replicas too low for current traffic"

# 4. Watch Nexus generate and validate fix:
nexus fix preview --incident <id>  # → "Increase HPA max from 5 to 10"

# 5. Watch Nexus apply via GitOps:
# → GitHub PR created: nexus/fix/inc-42-scale-hpa
# → Atlantis runs plan
# → PR auto-approved (Level 2 autonomy)
# → Fix applied

# 6. Watch Nexus verify:
nexus incidents view <id>  # → "Status: resolved, MTTR: 47 seconds"
```

### New Files Created
- `internal/gitops/*.go`
- `internal/policy/*.go`, `internal/policy/rego/*.rego`
- `internal/verifier/*.go`
- `internal/engine/engine.go`, `internal/engine/scheduler.go`
- `internal/audit/*.go`
- `cmd/run.go`
- `scripts/inject-failure.sh`
- GitHub webhook endpoint in `api/handlers/`

---

## PHASE 5: Learn + Dashboard — "The Brain Evolves"
**Goal:** Nexus learns from past incidents, improves future cycles, and has a beautiful UI.
**Duration:** 10-14 days
**Burnout Checkpoint:** ✅ After this phase, Nexus has a UI and learns from experience.

### Tasks

- [ ] Implement Learning Engine:
  - [ ] Store successful fixes as patterns
  - [ ] Recognize similar incidents in future
  - [ ] Prioritize known patterns over novel analysis
  - [ ] Track fix effectiveness over time
- [ ] Implement Runbook Generator:
  - [ ] Convert incident + fix into structured runbook
  - [ ] Make runbooks searchable
  - [ ] Export runbooks as Markdown
- [ ] Build Web UI (React/TypeScript):
  - [ ] Dashboard with live cycle status
  - [ ] Incident list with filters
  - [ ] Incident detail view with timeline
  - [ ] Target management
  - [ ] Policy editor with Rego syntax highlighting
  - [ ] Settings page
  - [ ] Real-time updates via WebSocket
- [ ] Build Grafana dashboards:
  - [ ] "Nexus Overview" — cycle health, incident rate, MTTR
  - [ ] "Incident Timeline" — lifecycle of each incident
  - [ ] "Target Health" — per-target observability
  - [ ] "Autonomy Level" — how many fixes were auto-applied vs manual
- [ ] Implement Prometheus metrics for Nexus itself:
  - [ ] `nexus_cycles_total`
  - [ ] `nexus_incidents_detected_total`
  - [ ] `nexus_incidents_resolved_total`
  - [ ] `nexus_cycle_duration_seconds`
  - [ ] `nexus_mttr_seconds`
  - [ ] `nexus_fix_application_rate` (% auto-applied)
  - [ ] `nexus_policy_denials_total`
- [ ] Create `nexus dashboard` command that opens the UI
- [ ] Implement `nexus runbook generate <incident-id>` command

### Success Criteria

```bash
nexus dashboard              # → Opens web UI in browser

# Web UI shows:
# - Live cycle status
# - Active incidents
# - MTTR trend (decreasing over time)
# - Fix success rate
# - Policy deny rate

nexus runbook generate <id>  # → Prints auto-generated runbook

# Grafana shows Nexus self-metrics
curl localhost:8080/metrics   # → All nexus_* metrics
```

### New Files Created
- `internal/learning/*.go`
- `internal/runbook/*.go`
- `web/` (entire React application)
- `api/handlers/*.go` (for web UI API)

---

## PHASE 6: Production Readiness — "Ship It"
**Goal:** Production-quality security, documentation, testing, and release pipeline.
**Duration:** 10-14 days
**Burnout Checkpoint:** ✅ After this phase, Nexus is ready to show the world.

### Tasks

- [ ] Security hardening:
  - [ ] Authentication for Nexus API (API keys or OIDC)
  - [ ] RBAC for Nexus operations
  - [ ] TLS everywhere (mTLS between components)
  - [ ] Secrets management via SOPS + Age
  - [ ] Audit log integrity verification
  - [ ] Rate limiting
- [ ] Testing:
  - [ ] Unit tests for all core logic (target: >70% coverage)
  - [ ] Integration tests (full cycle against LocalStack)
  - [ ] E2E tests (inject failure → verify resolution)
  - [ ] Chaos tests (what happens when Nexus components fail?)
  - [ ] Performance tests (cycle time under load)
- [ ] Documentation:
  - [ ] Complete README
  - [ ] Architecture deep-dive (ARCHITECTURE.md)
  - [ ] Setup guide (SETUP.md)
  - [ ] Plugin development guide (PLUGIN_DEV.md)
  - [ ] Policy writing guide (POLICY_WRITING.md)
  - [ ] Security model (SECURITY.md)
  - [ ] Troubleshooting guide (TROUBLESHOOTING.md)
  - [ ] Demo script
- [ ] Release pipeline:
  - [ ] GoReleaser for multi-platform binaries
  - [ ] Docker image build and push to GHCR
  - [ ] Helm chart packaging
  - [ ] Semantic versioning
  - [ ] Release notes generation
- [ ] Helm chart for Nexus deployment:
  - [ ] Nexus engine deployment
  - [ ] PostgreSQL (via CloudNativePG)
  - [ ] Prometheus + Grafana + Loki (optional, can use existing)
  - [ ] Atlantis (optional, can use existing)
  - [ ] OPA sidecar
- [ ] Performance optimization:
  - [ ] Profile and optimize hot paths
  - [ ] Database query optimization
  - [ ] Concurrent cycle execution
  - [ ] Resource usage tuning
- [ ] Demo recording script with specific scenarios

### Success Criteria

```bash
# Production deployment:
helm install nexus ./deploy/helm/nexus --values values.prod.yaml

# CI/CD pipeline:
# - PR → lint → test → build → push image
# - Tag → release binaries → publish Helm chart

# Documentation:
# - README explains the project in 30 seconds
# - Architecture doc has diagrams
# - Setup guide is step-by-step
# - Demo script is repeatable
```

### New Files Created
- `Dockerfile`, `.goreleaser.yaml`
- `deploy/helm/nexus/` (full Helm chart)
- `docs/*.md` (all documentation)
- `tests/e2e/*.go`, `tests/integration/*.go`
- Security configuration files

---

## CHECKPOINT SUMMARY

| Phase | Name | Duration | Cumulative | Burnout Check |
|-------|------|----------|------------|---------------|
| **0** | Foundation | 7-10 days | Week 1-2 | ✅ "I have a working CLI and dev env" |
| **1** | Observe | 10-14 days | Week 3-4 | ✅ "I can see my infra through Nexus" |
| **2** | Detect + Diagnose | 14-18 days | Week 5-7 | ✅ "Nexus finds problems automatically" |
| **3** | Fix + Validate | 14-18 days | Week 8-10 | ✅ "Nexus generates fixes — the WOW moment" |
| **4** | Apply + Verify | 14-18 days | Week 11-13 | ✅ "The FULL closed loop works! 🎉" |
| **5** | Learn + Dashboard | 10-14 days | Week 14-15 | ✅ "Beautiful UI + learning engine" |
| **6** | Production Readiness | 10-14 days | Week 16-17 | ✅ "Ready to ship and show the world" |

**Total: ~16-17 weeks (4 months) to a production-quality autonomous infrastructure control plane.**

---

# Section 9: Quick Start — What a New Agent Should Do First

## Day 1: Environment Setup

```bash
# 1. Clone the repo
git clone https://github.com/arenasys/nexus
cd nexus

# 2. Run dev setup
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh

# 3. Start Kind cluster
chmod +x scripts/setup-kind.sh
./scripts/setup-kind.sh

# 4. Build Nexus
make build

# 5. Verify
./nexus version
./nexus status

# 6. Run tests
make test
```

## What `setup-dev.sh` Should Install

```bash
#!/bin/bash
# setup-dev.sh — One-command dev environment

# Prerequisites (check and guide)
echo "Checking prerequisites..."

# Go
if ! command -v go &> /dev/null; then
    echo "Installing Go 1.24..."
    # Platform-specific install
fi

# Docker
if ! command -v docker &> /dev/null; then
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Kind
if ! command -v kind &> /dev/null; then
    echo "Installing Kind 0.25+..."
    go install sigs.k8s.io/kind@latest
fi

# kubectl
if ! command -v kubectl &> /dev/null; then
    echo "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
fi

# Helm
if ! command -v helm &> /dev/null; then
    echo "Installing Helm 3.17+..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# golangci-lint
if ! command -v golangci-lint &> /dev/null; then
    echo "Installing golangci-lint..."
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
fi

# OpenTofu (for fix generation)
if ! command -v tofu &> /dev/null; then
    echo "Installing OpenTofu 1.11+..."
    # Follow OpenTofu install guide
fi

# Go dependencies
echo "Installing Go dependencies..."
go mod download

echo "✅ Dev environment ready!"
```

---

# Section 10: Testing Strategy

## 10.1 Test Levels

| Level | What | Tool | Frequency |
|-------|------|------|-----------|
| **Unit** | Individual functions and methods | `go test` | Every commit |
| **Integration** | Component interaction (probe→analyzer, generator→validator) | `go test` with test containers | Every PR |
| **E2E** | Full closed loop against LocalStack | Custom test harness | Every release |
| **Chaos** | What happens when Nexus components fail | Custom chaos injection | Every milestone |

## 10.2 Key Test Scenarios

1. **Cost Spike Detection**: Simulate cost metric spike → verify incident created
2. **Security Drift Detection**: Create open S3 bucket → verify incident created
3. **Fix Generation**: Given incident → verify correct OpenTofu generated
4. **Fix Validation**: Given fix → verify `tofu plan` succeeds in shadow env
5. **Full Cycle**: Inject failure → verify incident detected → fix generated → PR created
6. **Policy Gate**: Test allow, deny, require-approval decisions
7. **Verification**: Apply fix → verify metrics return to baseline
8. **Rollback**: Fix fails verification → verify rollback occurs
9. **Concurrent Cycles**: Multiple incidents detected simultaneously → verify correct handling
10. **Engine Recovery**: Kill Nexus process → verify it recovers and continues cycles

---

# Section 11: Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **False positives** (Nexus detects non-issues) | Medium | High | Statistical baselines need cold-start period. Allow sensitivity tuning. Auto-escalate low-confidence findings to human review. |
| **False negatives** (Nexus misses real issues) | Medium | High | Multiple probe types per target. Redundant detection via different analyzers. Periodic full-audit cycles. |
| **Autonomous fix causes more damage** | Low | Critical | Always validate in shadow env first. Policy gates prevent dangerous actions. Verification step checks for regression. Rollback on failure. |
| **Nexus itself goes down** | Low | Medium | Stateless engine (state in DB). Health checks and auto-restart via K8s. Multiple replicas. |
| **GitHub API rate limiting** | Medium | Low | Implement backoff and caching. Use GitHub App (higher rate limits) for production. |
| **OpenTofu provider API changes** | Medium | Low | Pin provider versions. Test upgrades in CI. OpenTofu maintains backward compat. |
| **Developer burnout** | High | High | Phases have clear checkpoints. Each phase ends with a celebratable milestone. Don't skip breaks. |

---

# Section 12: Key Principles for the New Agent

1. **Pluggable first, everything else second.** The `Prober`, `Analyzer`, `Remediator`, and `Verifier` interfaces should be designed before the implementations. This is what makes Nexus extensible.

2. **GitOps-native means GitHub-native for MVP.** All fixes go through PRs. No direct mutations. This is what makes Nexus safe.

3. **Audit everything.** Every signal, every decision, every action goes into the append-only ledger. This is what makes Nexus trustworthy.

4. **Progressive autonomy.** Start at Level 0 (observe only). Never jump to Level 4 without proving lower levels first. This is what makes Nexus adoptable.

5. **Policy-gated.** Every autonomous action must pass through OPA. Policies are code, versioned in Git. This is what makes Nexus governable.

6. **Self-healing first, self-optimizing second.** Fix reliability issues before cost issues. Fix security issues before performance issues. Priority: 🔴 Availability > 🟡 Security > 🔵 Cost > ⚪ Performance.

7. **Demo-driven development.** Always have a working end-to-end scenario. If you can't demo it, it's not done.

8. **Free is not optional.** The entire stack must be zero-cost. Every dependency must have a free self-hosted option. This is what makes Nexus accessible.

---

# Section 13: The First Conversation a New Agent Should Have With You

> **"I've finished Phase 0 — the CLI works, Kind cluster is running, and CI passes. I need your input on:**
> 1. **What should be the first real target I observe? (K8s demo app? LocalStack mock AWS?)**
> 2. **How aggressive should the default anomaly detection be? (Low sensitivity to avoid false positives?)**
> 3. **What autonomy level should the first demo run at? (Level 1 — recommend only — for safety?)**
> 4. **Any specific failure scenarios you want the demo to handle first?"**

When you hear those questions, you'll know the agent has understood the project correctly.

---

**End of Handover Document**

*This document should be read in full by any new agent before writing a single line of code. The architecture, decisions, and phased approach have been cross-checked against current (June 2026) tooling and ecosystem realities.*