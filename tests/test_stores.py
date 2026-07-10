import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from nexus.db.session import CycleStore, IncidentStore
from nexus.models.cycle import Cycle, CycleStatus, CycleTrigger
from nexus.models.incident import Incident, IncidentStatus, IncidentType, Severity


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE incidents (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                probe_id TEXT NOT NULL DEFAULT '',
                target_id TEXT NOT NULL DEFAULT '',
                source_signal TEXT NOT NULL DEFAULT '',
                detected_at TEXT NOT NULL,
                diagnosed_at TEXT,
                fixed_at TEXT,
                verified_at TEXT,
                resolved_at TEXT,
                root_cause TEXT NOT NULL DEFAULT '',
                confidence REAL NOT NULL DEFAULT 0,
                fix_generated INTEGER NOT NULL DEFAULT 0,
                fix_pr_url TEXT NOT NULL DEFAULT '',
                fix_branch TEXT NOT NULL DEFAULT '',
                fix_summary TEXT NOT NULL DEFAULT '',
                verified INTEGER,
                mttr_seconds INTEGER NOT NULL DEFAULT 0,
                cycle_id TEXT NOT NULL DEFAULT '',
                log TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}'
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE cycles (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                trigger TEXT NOT NULL,
                status TEXT NOT NULL,
                observe_at TEXT,
                detect_at TEXT,
                diagnose_at TEXT,
                generate_at TEXT,
                validate_at TEXT,
                apply_at TEXT,
                verify_at TEXT,
                incidents_detected INTEGER NOT NULL DEFAULT 0,
                fixes_applied INTEGER NOT NULL DEFAULT 0,
                errors TEXT NOT NULL DEFAULT '[]',
                target_id TEXT NOT NULL DEFAULT ''
            )
            """
        ))
    Session = sessionmaker(bind=engine)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()


def _make_incident(incident_id: str = "inc-001") -> Incident:
    return Incident(
        id=incident_id,
        type=IncidentType.reliability_degradation,
        severity=Severity.high,
        status=IncidentStatus.detected,
        probe_id="probe",
        target_id="target",
        source_signal="cpu",
        detected_at=datetime.utcnow(),
        root_cause="test",
        confidence=0.8,
        log=[{"phase": "detect"}],
        metadata={"region": "us-east"},
    )


def _make_cycle(cycle_id: str = "cyc-001") -> Cycle:
    return Cycle(
        id=cycle_id,
        started_at=datetime.utcnow(),
        trigger=CycleTrigger.manual,
        status=CycleStatus.completed,
        incidents_detected=1,
        errors=["none"],
    )


def test_incident_store_create_and_get(session):
    store = IncidentStore(session)
    inc = _make_incident("inc-store-001")
    store.create(inc)

    row = store.get("inc-store-001")
    assert row is not None
    assert row["id"] == "inc-store-001"
    assert row["type"] == "reliability_degradation"
    assert row["target_id"] == "target"
    assert json.loads(row["log"]) == [{"phase": "detect"}]


def test_incident_store_list_empty(session):
    store = IncidentStore(session)
    assert store.list() == []


def test_incident_store_get_nonexistent(session):
    store = IncidentStore(session)
    assert store.get("does-not-exist") is None


def test_cycle_store_create_and_get(session):
    store = CycleStore(session)
    cyc = _make_cycle("cyc-store-001")
    store.create(cyc)

    result = session.execute(
        text("SELECT * FROM cycles WHERE id = :id"),
        {"id": "cyc-store-001"},
    )
    row = result.fetchone()
    assert row is not None
    assert row._mapping["id"] == "cyc-store-001"
    assert json.loads(row._mapping["errors"]) == ["none"]
