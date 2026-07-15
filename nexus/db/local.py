import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from ..models.incident import Incident

DEFAULT_DB_PATH = ".nexus/nexus.db"


class LocalIncidentStore:
    """Lightweight SQLite incident store that requires no Postgres server."""

    def __init__(self, db_path: str | None = None):
        self.db_path: str = db_path or os.getenv("NEXUS_LOCAL_DB_PATH") or DEFAULT_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id            TEXT PRIMARY KEY,
                    type          TEXT NOT NULL,
                    severity      TEXT NOT NULL,
                    status        TEXT NOT NULL,
                    probe_id      TEXT NOT NULL DEFAULT '',
                    target_id     TEXT NOT NULL DEFAULT '',
                    source_signal TEXT NOT NULL DEFAULT '',
                    detected_at   TEXT NOT NULL,
                    root_cause    TEXT NOT NULL DEFAULT '',
                    confidence    REAL NOT NULL DEFAULT 0,
                    metadata      TEXT NOT NULL DEFAULT '{}',
                    cycle_id      TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incidents_detected_at "
                "ON incidents (detected_at DESC)"
            )

    def create(self, incident: Incident) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    id, type, severity, status, probe_id, target_id, source_signal,
                    detected_at, root_cause, confidence, metadata, cycle_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.type.value,
                    incident.severity.value,
                    incident.status.value,
                    incident.probe_id,
                    incident.target_id,
                    incident.source_signal,
                    (
                        incident.detected_at.isoformat()
                        if incident.detected_at
                        else datetime.utcnow().isoformat()
                    ),
                    incident.root_cause,
                    incident.confidence,
                    json.dumps(incident.metadata),
                    incident.cycle_id,
                ),
            )

    def get(self, incident_id: str) -> Incident | None:
        with self._connect() as conn:
            # Allow lookup by full UUID or by short prefix (e.g. CLI display ID).
            if len(incident_id) >= 32:
                row = conn.execute(
                    "SELECT * FROM incidents WHERE id = ?", (incident_id,)
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM incidents WHERE id LIKE ? "
                    "ORDER BY detected_at DESC LIMIT 1",
                    (f"{incident_id}%",),
                ).fetchone()
        if not row:
            return None
        return self._row_to_incident(row)

    def list(self, limit: int = 100) -> list[Incident]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM incidents ORDER BY detected_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_incident(row) for row in rows]

    def _row_to_incident(self, row: sqlite3.Row) -> Incident:
        from ..models.incident import IncidentStatus, IncidentType, Severity
        return Incident(
            id=row["id"],
            type=IncidentType(row["type"]),
            severity=Severity(row["severity"]),
            status=IncidentStatus(row["status"]),
            probe_id=row["probe_id"],
            target_id=row["target_id"],
            source_signal=row["source_signal"],
            detected_at=datetime.fromisoformat(row["detected_at"]),
            root_cause=row["root_cause"],
            confidence=row["confidence"],
            metadata=json.loads(row["metadata"]),
            cycle_id=row["cycle_id"],
        )
