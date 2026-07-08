from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(dsn:str)->Engine:
    if not dsn: raise ValueError("database DSN empty")
    if dsn.startswith("postgres://"): dsn=dsn.replace("postgres://","postgresql+psycopg2://",1)
    elif dsn.startswith("postgresql://") and "+psycopg2" not in dsn: dsn=dsn.replace("postgresql://","postgresql+psycopg2://",1)
    return create_engine(dsn, pool_pre_ping=True)
MIGRATIONS_DIR=Path(__file__).parent/"migrations"
def migrate(engine:Engine)->None:
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"))
        applied={r[0] for r in conn.execute(text("SELECT version FROM schema_migrations"))}
        for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
            v=f.stem
            if v in applied: continue
            sql=f.read_text()
            conn.execute(text(sql))
            conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:v)"),{"v":v})
class Database:
    def __init__(self, dsn:str):
        self.engine=get_engine(dsn)
        from sqlalchemy.orm import sessionmaker
        self.SessionLocal=sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
    def migrate(self): migrate(self.engine)
    def get_session(self): return self.SessionLocal()
    def close(self): self.engine.dispose()
