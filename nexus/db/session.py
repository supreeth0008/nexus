# Minimal stores to satisfy imports; full implementation can be expanded later.
import json

from sqlalchemy import text


class IncidentStore:
    def __init__(self, session):
        self.session = session

    def create(self, incident):
        self.session.execute(
            text(
                """
                INSERT INTO incidents (
                    id, type, severity, status, probe_id, target_id, source_signal,
                    detected_at, diagnosed_at, fixed_at, verified_at, resolved_at,
                    root_cause, confidence, fix_generated, fix_pr_url, fix_branch,
                    fix_summary, verified, mttr_seconds, cycle_id, log, metadata
                ) VALUES (
                    :id, :type, :severity, :status, :probe_id, :target_id, :source_signal,
                    :detected_at, :diagnosed_at, :fixed_at, :verified_at, :resolved_at,
                    :root_cause, :confidence, :fix_generated, :fix_pr_url, :fix_branch,
                    :fix_summary, :verified, :mttr_seconds, :cycle_id, :log, :metadata
                )
                """
            ),
            {
                "id": incident.id,
                "type": incident.type.value,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "probe_id": incident.probe_id,
                "target_id": incident.target_id,
                "source_signal": incident.source_signal,
                "detected_at": incident.detected_at,
                "diagnosed_at": incident.diagnosed_at,
                "fixed_at": incident.fixed_at,
                "verified_at": incident.verified_at,
                "resolved_at": incident.resolved_at,
                "root_cause": incident.root_cause,
                "confidence": incident.confidence,
                "fix_generated": incident.fix_generated,
                "fix_pr_url": incident.fix_pr_url,
                "fix_branch": incident.fix_branch,
                "fix_summary": incident.fix_summary,
                "verified": incident.verified,
                "mttr_seconds": incident.mttr_seconds,
                "cycle_id": incident.cycle_id,
                "log": json.dumps(incident.log),
                "metadata": json.dumps(incident.metadata),
            },
        )
        self.session.commit()

    def list(self, status=None, limit=20):
        query = "SELECT * FROM incidents"
        params = {}
        if status is not None:
            query += " WHERE status = :status"
            params["status"] = status.value if hasattr(status, "value") else status
        query += " ORDER BY detected_at DESC LIMIT :limit"
        params["limit"] = limit
        result = self.session.execute(text(query), params)
        return [dict(row._mapping) for row in result]

    def get(self, incident_id):
        result = self.session.execute(
            text("SELECT * FROM incidents WHERE id = :id"),
            {"id": incident_id},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None


class TargetStore:
    def __init__(self, session):
        self.session = session


class CycleStore:
    def __init__(self, session):
        self.session = session

    def create(self, cycle):
        self.session.execute(
            text(
                """
                INSERT INTO cycles (
                    id, started_at, completed_at, trigger, status,
                    observe_at, detect_at, diagnose_at, generate_at, validate_at,
                    apply_at, verify_at, incidents_detected, fixes_applied, errors,
                    target_id
                ) VALUES (
                    :id, :started_at, :completed_at, :trigger, :status,
                    :observe_at, :detect_at, :diagnose_at, :generate_at, :validate_at,
                    :apply_at, :verify_at, :incidents_detected, :fixes_applied, :errors,
                    :target_id
                )
                """
            ),
            {
                "id": cycle.id,
                "started_at": cycle.started_at,
                "completed_at": cycle.completed_at,
                "trigger": cycle.trigger.value,
                "status": cycle.status.value,
                "observe_at": cycle.observe_at,
                "detect_at": cycle.detect_at,
                "diagnose_at": cycle.diagnose_at,
                "generate_at": cycle.generate_at,
                "validate_at": cycle.validate_at,
                "apply_at": cycle.apply_at,
                "verify_at": cycle.verify_at,
                "incidents_detected": cycle.incidents_detected,
                "fixes_applied": cycle.fixes_applied,
                "errors": json.dumps(cycle.errors),
                "target_id": cycle.target_id,
            },
        )
        self.session.commit()

    def list(self, limit=20):
        result = self.session.execute(
            text("SELECT * FROM cycles ORDER BY started_at DESC LIMIT :limit"),
            {"limit": limit},
        )
        return [dict(row._mapping) for row in result]
