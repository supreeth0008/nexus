from datetime import datetime

import pytest

from nexus.analyzer.security import SecurityAnalyzer
from nexus.models.incident import IncidentStatus, IncidentType, Severity
from nexus.observe.models import ObserveResult, Signal


@pytest.fixture
def analyzer():
    return SecurityAnalyzer()


def _result(*signals: Signal) -> ObserveResult:
    return ObserveResult(
        target_name="demo-aws",
        provider="aws",
        status="ok",
        signals=list(signals),
        duration_ms=10,
        timestamp=datetime.utcnow(),
    )


def test_detects_open_cidr(analyzer):
    result = _result(Signal(name="security_group", value="0.0.0.0/0"))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.type == IncidentType.security_drift
    assert inc.severity == Severity.critical
    assert inc.status == IncidentStatus.detected


def test_detects_unencrypted_storage(analyzer):
    result = _result(Signal(name="encryption_enabled", value=0.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    assert incidents[0].type == IncidentType.security_drift
    assert incidents[0].severity == Severity.high


def test_ignores_malformed_string_value(analyzer):
    """A non-numeric string value should not crash the analyzer."""
    result = _result(Signal(name="encryption_enabled", value="unexpected"))
    incidents = analyzer.analyze(result)
    assert incidents == []
