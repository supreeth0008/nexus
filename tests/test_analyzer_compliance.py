from datetime import datetime

import pytest

from nexus.analyzer.compliance import ComplianceAnalyzer
from nexus.models.incident import IncidentStatus, IncidentType, Severity
from nexus.observe.models import ObserveResult, Signal


@pytest.fixture
def analyzer():
    return ComplianceAnalyzer()


def _result(*signals: Signal) -> ObserveResult:
    return ObserveResult(
        target_name="demo-aws",
        provider="aws",
        status="ok",
        signals=list(signals),
        duration_ms=10,
        timestamp=datetime.utcnow(),
    )


def test_detects_missing_tags(analyzer):
    result = _result(Signal(name="missing_tags", value=3.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.type == IncidentType.compliance_drift
    assert inc.severity == Severity.medium
    assert inc.status == IncidentStatus.detected


def test_detects_forbidden_region(analyzer):
    result = _result(Signal(name="region_forbidden", value=1.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    assert incidents[0].severity == Severity.high


def test_ignores_malformed_string_value(analyzer):
    """A non-numeric string value should not crash the analyzer."""
    result = _result(Signal(name="missing_tags", value="many"))
    incidents = analyzer.analyze(result)
    assert incidents == []
