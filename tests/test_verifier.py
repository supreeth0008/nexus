from datetime import datetime
from unittest.mock import patch

from nexus.config.settings import Settings, TargetConfig
from nexus.models.action import Action, ActionKind, ActionRisk
from nexus.models.incident import Incident, IncidentStatus, IncidentType, Severity
from nexus.observe.models import ObserveResult, Signal
from nexus.verifier.verifier import Verifier


def _make_incident(source_signal: str) -> Incident:
    return Incident(
        id="inc-verify-001",
        type=IncidentType.reliability_degradation,
        severity=Severity.high,
        target_id="demo-target",
        source_signal=source_signal,
        status=IncidentStatus.diagnosed,
        root_cause="pod failure",
        confidence=0.8,
    )


def _make_action() -> Action:
    return Action(
        incident_id="inc-verify-001",
        kind=ActionKind.kubernetes,
        risk=ActionRisk.low,
    )


def _make_cfg() -> Settings:
    return Settings(
        targets=[
            TargetConfig(
                name="demo-target",
                provider="prometheus",
                endpoint="http://localhost:9090",
            )
        ]
    )


def _observe_result(value: float | None) -> ObserveResult:
    signals = []
    if value is not None:
        signals.append(Signal(name="failed_pods", value=float(value)))
    return ObserveResult(
        target_name="demo-target",
        provider="prometheus",
        status="ok",
        signals=signals,
        duration_ms=10,
        timestamp=datetime.utcnow(),
    )


def test_verify_returns_success_when_signal_clears():
    """Verification succeeds when the triggering signal drops to zero."""
    incident = _make_incident("failed_pods=2.0")
    action = _make_action()
    cfg = _make_cfg()
    verifier = Verifier()

    with patch("nexus.observe.runner.observe_target", return_value=_observe_result(0.0)):
        result = verifier.verify(incident, action, cfg)

    assert result["verified"] is True
    assert result["metrics_improved"] is True
    assert result["new_value"] == 0.0
    assert result["old_value"] == 2.0


def test_verify_returns_failure_when_signal_persists():
    """Verification fails when the triggering signal is still elevated."""
    incident = _make_incident("failed_pods=2.0")
    action = _make_action()
    cfg = _make_cfg()
    verifier = Verifier()

    with patch("nexus.observe.runner.observe_target", return_value=_observe_result(3.0)):
        result = verifier.verify(incident, action, cfg)

    assert result["verified"] is False
    assert result["metrics_improved"] is False
    assert result["new_value"] == 3.0
    assert result["old_value"] == 2.0


def test_verify_returns_success_when_signal_absent():
    """Verification succeeds when the triggering signal is no longer emitted."""
    incident = _make_incident("failed_pods=2.0")
    action = _make_action()
    cfg = _make_cfg()
    verifier = Verifier()

    with patch("nexus.observe.runner.observe_target", return_value=_observe_result(None)):
        result = verifier.verify(incident, action, cfg)

    assert result["verified"] is True
    assert result["metrics_improved"] is True
    assert result["new_value"] is None


def test_verify_returns_failure_without_config():
    """Without a config the verifier cannot re-observe and must fail safe."""
    incident = _make_incident("failed_pods=2.0")
    action = _make_action()
    verifier = Verifier()

    result = verifier.verify(incident, action, cfg=None)

    assert result["verified"] is False
    assert "no config provided" in result.get("error", "")
