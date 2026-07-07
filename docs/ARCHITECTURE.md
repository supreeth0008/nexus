# Nexus Architecture

I built Nexus as a closed-loop autonomous infrastructure control plane.

## Closed Loop

Observe → Detect → Diagnose → Generate → Validate → Apply → Verify → Learn

I implement each phase as a pluggable interface in Python:
- `Probe` – Prometheus, Kubernetes, LocalStack
- `Analyzer` – statistical, cost, security, reliability, compliance
- `DiagnosisEngine` – I correlate signals → root cause
- `Remediator` – OpenTofu, Kubernetes, Helm
- `Validator` – shadow environment
- `PolicyGate` – OPA-style progressive autonomy
- `Verifier` – post-apply metrics check
- `LearningEngine` – pattern recognition

See HANDOVER.md Section 2 for diagrams – I preserved the original architecture, migrating implementation language Go → Python.
