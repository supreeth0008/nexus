from datetime import datetime

from ..config.settings import Settings
from ..models.cycle import Cycle, CycleStatus, CycleTrigger
from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from .models import ObserveResult
from .probes.base import get_probe


def observe_target(target):
    try:
        probe = get_probe(target.provider)
        return probe.observe(target)
    except Exception as e:
        return ObserveResult(
            target_name=target.name,
            provider=target.provider,
            status="unreachable",
            signals=[],
            duration_ms=0,
            error=str(e),
        )


def observe_all(
    cfg: Settings,
    target_filter: str | None = None,
) -> list[ObserveResult]:
    targets = cfg.targets
    if target_filter:
        targets = [t for t in targets if t.name == target_filter]
    return [observe_target(t) for t in targets]


def detect_incidents(results: list[ObserveResult]) -> list[Incident]:
    incidents = []
    for r in results:
        if r.status in ("degraded", "unreachable"):
            incidents.append(Incident(
                type=IncidentType.reliability_degradation,
                severity=Severity.high if r.status == "unreachable" else Severity.medium,
                status=IncidentStatus.detected,
                probe_id=f"{r.provider}-probe",
                target_id=r.target_name,
                source_signal=f"observe_status={r.status}",
                root_cause=r.error or f"target {r.target_name} reported {r.status}",
                confidence=0.8,
            ))
    return incidents


def run_cycle(cfg: Settings, trigger: str = "manual") -> Cycle:
    cycle = Cycle(
        trigger=(
            CycleTrigger.manual
            if trigger not in ("scheduled", "event", "manual")
            else CycleTrigger(trigger)
        ),
        status=CycleStatus.running,
    )
    cycle.observe_at = datetime.utcnow()
    results = observe_all(cfg)
    cycle.detect_at = datetime.utcnow()
    incidents = detect_incidents(results)
    cycle.incidents_detected = len(incidents)
    cycle.completed_at = datetime.utcnow()
    cycle.status = CycleStatus.completed
    return cycle
