# Troubleshooting

**nexus: command not found**
I install via `pip install -e .` – ensure `~/.local/bin` is in PATH.

**database DSN empty**
I read `database.dsn` from nexus.yaml or `NEXUS_DATABASE_DSN`. Run `nexus init` first.

**observe returns 0 targets**
I load targets from `nexus.yaml` – check `nexus status` lists them. Provider must be one of: aws, azure, gcp, kubernetes, localstack, prometheus.

**policy denies all fixes**
I default to autonomy level 0 (observe only). Set `autonomy.level: 2` in nexus.yaml or `NEXUS_AUTONOMY_LEVEL=2`.

**Migrations fail**
I use SQLAlchemy + raw SQL migrations in `nexus/db/migrations/`. Run `nexus migrate` with a valid PostgreSQL DSN.
