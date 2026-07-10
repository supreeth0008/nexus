from datetime import datetime

import pytest

from nexus.analyzer.reliability import ReliabilityAnalyzer
from nexus.models.incident import IncidentStatus, IncidentType, Severity
from nexus.observe.models import ObserveResult, Signal


@pytest.fixture
def analyzer():
    return ReliabilityAnalyzer()


def _result(*signals: Signal) -> ObserveResult:
    return ObserveResult(
        target_name="demo-k8s",
        provider="kubernetes",
        status="ok",
        signals=list(signals),
        duration_ms=10,
        timestamp=datetime.utcnow(),
    )


def test_detects_error_signal(analyzer):
    result = _result(Signal(name="error_rate", value=5.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.type == IncidentType.reliability_degradation
    assert inc.status == IncidentStatus.detected
    assert inc.target_id == "demo-k8s"


def test_detects_high_latency(analyzer):
    result = _result(Signal(name="p95_latency", value=2500.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    assert incidents[0].type == IncidentType.performance_degradation
    assert incidents[0].severity == Severity.high


def test_ignores_malformed_string_value(analyzer):
    """A non-numeric string value should not crash the analyzer."""
    result = _result(Signal(name="error_rate", value="not-a-number"))
    incidents = analyzer.analyze(result)
    assert incidents == []
