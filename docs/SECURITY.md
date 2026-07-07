# Security Model

I enforce:
- API key / OIDC auth on /v1/* (set NEXUS_API_KEY)
- TLS everywhere – set NEXUS_TLS_CERT / NEXUS_TLS_KEY
- RBAC: reader, operator, admin roles
- Audit ledger: append-only, exportable to Loki
- Secrets: SOPS + Age – I never store credentials in DB
- Policy gate: every action through OPA – see `nexus/policy/rego/`
- Signed commits: I sign GitOps PR commits with GPG when GPG_KEY_ID is set
