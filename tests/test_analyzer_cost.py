from datetime import datetime

import pytest

from nexus.analyzer.cost import CostAnalyzer
from nexus.models.incident import IncidentStatus, IncidentType, Severity
from nexus.observe.models import ObserveResult, Signal


@pytest.fixture
def analyzer():
    return CostAnalyzer()


def _result(*signals: Signal) -> ObserveResult:
    return ObserveResult(
        target_name="demo-aws",
        provider="aws",
        status="ok",
        signals=list(signals),
        duration_ms=10,
        timestamp=datetime.utcnow(),
    )


def test_detects_cost_spike(analyzer):
    result = _result(Signal(name="daily_spend", value=1500.0))
    incidents = analyzer.analyze(result)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.type == IncidentType.cost_spike
    assert inc.severity == Severity.high
    assert inc.status == IncidentStatus.detected


def test_ignores_low_cost(analyzer):
    result = _result(Signal(name="daily_spend", value=50.0))
    incidents = analyzer.analyze(result)
    assert incidents == []


def test_ignores_malformed_string_value(analyzer):
    """A non-numeric string value should not crash the analyzer."""
    result = _result(Signal(name="daily_spend", value="expensive"))
    incidents = analyzer.analyze(result)
    assert incidents == []
