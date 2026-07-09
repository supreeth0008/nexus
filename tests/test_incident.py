from nexus.models.incident import Incident, IncidentStatus, IncidentType, Severity


def test_incident_state_machine():
    cases = [
        (IncidentStatus.detected, IncidentStatus.diagnosing, True),
        (IncidentStatus.detected, IncidentStatus.resolved, False),
        (IncidentStatus.verifying, IncidentStatus.resolved, True),
    ]
    for frm, to, allowed in cases:
        inc = Incident(type=IncidentType.custom, severity=Severity.low, status=frm)
        assert inc.can_transition(to) == allowed
