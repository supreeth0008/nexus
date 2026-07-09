"""Test OPA policy evaluation matches builtin for sample incident/action pairs."""

import json
import os
import shutil
import subprocess
import tempfile

import pytest

from nexus.models.action import Action, ActionKind, ActionRisk
from nexus.models.incident import Incident, IncidentStatus, IncidentType, Severity
from nexus.policy.opa import OPAClient


def make_incident(severity: str = "high", confidence: float = 0.9) -> Incident:
    return Incident(
        type=IncidentType.scaling_bottleneck,
        severity=Severity(severity),
        status=IncidentStatus.diagnosed,
        target_id="test-target",
        source_signal="cpu > 85%",
        root_cause="HPA max replicas too low",
        confidence=confidence,
    )


def make_action(risk: str = "low") -> Action:
    return Action(
        incident_id="test-incident",
        kind=ActionKind.opentofu,
        summary="Scale up HPA",
        diff="hpa.spec.maxReplicas: 5 -> 10",
        risk=ActionRisk(risk),
    )


class TestOPAPolicy:
    """Test that OPA Rego policy matches Python builtin logic."""

    @pytest.fixture
    def opa_client(self):
        """Create OPAClient in 'opa' mode if binary available, else skip."""
        if not shutil.which("opa"):
            pytest.skip("OPA binary not installed")
        return OPAClient(mode="opa")

    @pytest.fixture
    def builtin_client(self):
        return OPAClient(mode="builtin")

    @pytest.mark.parametrize(
        "autonomy_level,action_risk,incident_severity,incident_confidence,expected_decision",
        [
            # L0: always deny
            (0, "low", "low", 0.9, "deny"),
            (0, "medium", "high", 0.9, "deny"),
            (0, "high", "critical", 0.9, "deny"),
            # L1: require_approval for all
            (1, "low", "low", 0.9, "require_approval"),
            (1, "medium", "high", 0.9, "require_approval"),
            (1, "high", "critical", 0.9, "require_approval"),
            # L2: allow low risk only
            (2, "low", "low", 0.9, "allow"),
            (2, "medium", "high", 0.9, "require_approval"),
            (2, "high", "critical", 0.9, "require_approval"),
            # L3: allow low+medium (medium needs confidence >= 0.8)
            (3, "low", "low", 0.9, "allow"),
            (3, "medium", "high", 0.9, "allow"),
            (3, "medium", "high", 0.7, "require_approval"),
            (3, "high", "critical", 0.9, "require_approval"),
            # L4: allow all
            (4, "low", "low", 0.9, "allow"),
            (4, "medium", "high", 0.9, "allow"),
            (4, "high", "critical", 0.9, "allow"),
            # Critical severity escalation at < L4
            (2, "low", "critical", 0.9, "require_approval"),
            (3, "low", "critical", 0.9, "require_approval"),
        ],
    )
    def test_opa_matches_builtin(
        self,
        opa_client,
        builtin_client,
        autonomy_level,
        action_risk,
        incident_severity,
        incident_confidence,
        expected_decision,
    ):
        """OPA and builtin must produce identical decisions for all combos."""
        incident = make_incident(incident_severity, incident_confidence)
        action = make_action(action_risk)

        builtin_result = builtin_client.evaluate(incident, action, autonomy_level)
        opa_result = opa_client.evaluate(incident, action, autonomy_level)

        assert builtin_result["decision"] == expected_decision, (
            f"Builtin: L{autonomy_level} risk={action_risk} "
            f"sev={incident_severity} -> {builtin_result['decision']} "
            f"(expected {expected_decision})"
        )
        assert opa_result["decision"] == expected_decision, (
            f"OPA: L{autonomy_level} risk={action_risk} "
            f"sev={incident_severity} -> {opa_result['decision']} "
            f"(expected {expected_decision})"
        )
        assert builtin_result["decision"] == opa_result["decision"], (
            f"Mismatch: builtin={builtin_result['decision']}, "
            f"opa={opa_result['decision']}"
        )


def test_opa_eval_subprocess_direct():
    """Direct subprocess test of OPA eval with sample input."""
    if not shutil.which("opa"):
        pytest.skip("OPA binary not installed")

    policy_path = "nexus/policy/opa/policy.rego"
    input_data = {
        "autonomy_level": 3,
        "action_exists": True,
        "action": {"risk": "medium"},
        "incident": {"severity": "high", "confidence": 0.9},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(input_data, f)
        input_file = f.name

    try:
        cmd = [
            "opa",
            "eval",
            "-i",
            input_file,
            "-d",
            policy_path,
            "data.nexus.policy.decision",
            "-f",
            "json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    finally:
        os.unlink(input_file)

    assert result.returncode == 0, f"OPA eval failed: {result.stderr}"
    output = json.loads(result.stdout)
    decisions = output.get("result", [])
    assert len(decisions) == 1
    value = decisions[0]["expressions"][0]["value"]
    assert value["decision"] == "allow"
    assert value["reason"] == "L3: policy gate passed - auto-applied"
