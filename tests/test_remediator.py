import pytest

from nexus.models.action import ActionKind
from nexus.models.incident import Incident, IncidentType, Severity
from nexus.remediator.registry import get_remediators


def _make_incident(incident_type: IncidentType = IncidentType.scaling_bottleneck) -> Incident:
    return Incident(
        id="inc-rem-001",
        type=incident_type,
        severity=Severity.high,
        target_id="demo-k8s",
        root_cause="HPA max replicas too low",
        confidence=0.8,
    )


def test_opentofu_remediator_generates_action():
    incident = _make_incident(IncidentType.scaling_bottleneck)
    remediators = get_remediators()
    opentofu = next((r for r in remediators if r.name == "opentofu"), None)
    assert opentofu is not None
    assert opentofu.can_remediate(incident) is True

    actions = opentofu.generate(incident)
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == ActionKind.opentofu
    assert action.incident_id == incident.id
    assert len(action.diff) > 0


def test_opentofu_remediator_handles_unsupported_incident():
    incident = _make_incident(IncidentType.custom)
    remediators = get_remediators()
    opentofu = next((r for r in remediators if r.name == "opentofu"), None)
    assert opentofu is not None
    assert opentofu.can_remediate(incident) is False
    actions = opentofu.generate(incident)
    assert len(actions) == 1  # falls back to default template


def test_remediators_handle_minimal_incident_without_crashing():
    """A bare-minimum incident should not crash generate()."""
    incident = Incident(
        id="inc-rem-minimal",
        type=IncidentType.security_drift,
        severity=Severity.critical,
    )
    for remediator in get_remediators():
        try:
            if remediator.can_remediate(incident):
                remediator.generate(incident)
        except Exception as exc:
            pytest.fail(f"{remediator.name} crashed on minimal incident: {exc}")
