# Security Policy

I take security seriously in Nexus.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.5.x   | yes |
| 0.2.x   | yes |
| <0.2    | no  |

## Reporting a Vulnerability

I ask you to email security@nexus.local (placeholder – open a private GitHub security advisory) with:
- Description
- Steps to reproduce
- Impact assessment

I aim to acknowledge within 48h, triage within 7 days.

## Security Model

I designed Nexus with these principles:

- **GitOps-native**: I never mutate infrastructure directly – all changes go through signed PRs
- **Policy-gated**: I evaluate every autonomous action through OPA before apply
- **Audit everything**: I write an append-only ledger per incident (see `internal/audit`)
- **Secrets**: I recommend Mozilla SOPS + Age – secrets never enter the database, only auth method hints
- **Progressive autonomy**: I start at L0 observe-only – you escalate deliberately
- **mTLS ready**: I support TLS everywhere – set `NEXUS_TLS_*` env vars
- **RBAC**: I enforce API key / OIDC authentication on the HTTP API (Phase 6)
- **Supply chain**: I pin all dependencies, CI runs `pip-audit`, container images signed with cosign

## Threat Model

I mitigate:
- Unauthorized fix application → OPA policy gate + signed commits
- Privilege escalation → Least-privilege RBAC, short-lived tokens
- Data exfiltration → No credentials stored in DB, SOPS encryption at rest
- Supply chain → Pinned versions, SBOM generation in CI

See `docs/SECURITY.md` for full analysis.
