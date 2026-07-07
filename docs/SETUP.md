# Setup

I made Nexus one-command installable.

```bash
git clone https://github.com/supreeth0008/nexus
cd nexus
pip install -e .[dev]
nexus version
nexus init --name my-project
nexus status
```

## Dev cluster

I provide Kind + monitoring:

```bash
./scripts/setup-kind.sh
# Prometheus + Grafana auto-deployed via deploy/monitoring/
```

## Database

I support PostgreSQL:

```bash
export NEXUS_DATABASE_DSN=postgres://nexus:secret@localhost:5432/nexus
nexus migrate
```

Without DB, I run stateless – observation results print but are not persisted.
