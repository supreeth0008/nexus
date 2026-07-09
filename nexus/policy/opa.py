from typing import Any
import json
import subprocess
from pathlib import Path

from ..models.action import Action
from ..models.incident import Incident
from ..config.settings import load_config


class OPAClient:
    """
    Policy evaluation client supporting two modes:
    - 'builtin': Python rules engine (default, zero dependencies)
    - 'opa': External OPA binary evaluating Rego policies
    """

    def __init__(self, mode: str | None = None):
        self.mode = mode or self._get_mode_from_config()
        self._opa_binary = None
        self._policy_path = None
        if self.mode == "opa":
            self._init_opa()

    def _get_mode_from_config(self) -> str:
        try:
            cfg = load_config(None)
            return getattr(cfg.engine, "policy_mode", "builtin")
        except Exception:
            return "builtin"

    def _init_opa(self):
        # Find OPA binary
        for candidate in ("opa", "/usr/local/bin/opa", "/usr/bin/opa"):
            if Path(candidate).exists() or self._which(candidate):
                self._opa_binary = candidate
                break
        if not self._opa_binary:
            raise RuntimeError("OPA binary not found in PATH. Install opa or set mode='builtin'")

        # Find policy file
        policy_path = Path(__file__).parent / "opa" / "policy.rego"
        if not policy_path.exists():
            raise RuntimeError(f"Policy file not found: {policy_path}")
        self._policy_path = policy_path

    def _which(self, cmd: str) -> bool:
        try:
            subprocess.run([cmd, "version"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def evaluate(self, incident: Incident, action: Action, autonomy_level: int) -> dict[str, Any]:
        if self.mode == "opa":
            return self._eval_opa(incident, action, autonomy_level)
        return self._eval_builtin(incident, action, autonomy_level)

    def _eval_builtin(self, incident: Incident, action: Action, autonomy_level: int) -> dict[str, Any]:
        """Python rules engine mimicking Rego policy (default, no deps)."""
        decision = "deny"
        reason = ""
        if autonomy_level == 0:
            decision = "deny"
            reason = "Observe only mode"
        elif autonomy_level == 1:
            decision = "require_approval"
            reason = "Recommend mode – PR opened for manual review"
        elif autonomy_level == 2:
            if action.risk.value == "low":
                decision = "allow"
                reason = "Auto-fix low risk permitted"
            else:
                decision = "require_approval"
                reason = f"Risk {action.risk.value} requires approval at L2"
        elif autonomy_level == 3:
            if action.risk.value in ("low", "medium"):
                if action.risk.value == "medium" and incident.confidence < 0.8:
                    decision = "require_approval"
                    reason = "Medium risk with low confidence requires approval at L3"
                else:
                    decision = "allow"
                    reason = "Policy gate passed at L3"
            else:
                decision = "require_approval"
                reason = "High risk requires approval at L3"
        elif autonomy_level >= 4:
            decision = "allow"
            reason = "Full autonomy"

        # Critical severity escalation
        if incident.severity.value == "critical" and autonomy_level < 4:
            if decision == "allow":
                decision = "require_approval"
                reason = "Critical severity escalated to human"

        return {"decision": decision, "reason": reason, "autonomy_level": autonomy_level}

    def _eval_opa(self, incident: Incident, action: Action, autonomy_level: int) -> dict[str, Any]:
        """Evaluate policy using OPA binary and Rego policy."""
        input_data = {
            "autonomy_level": autonomy_level,
            "action_exists": action is not None,
            "action": {"risk": action.risk.value} if action else None,
            "incident": {
                "severity": incident.severity.value,
                "confidence": incident.confidence,
            } if incident else None,
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name

        try:
            cmd = [
                self._opa_binary,
                "eval",
                "-i", input_file,
                "-d", str(self._policy_path),
                "data.nexus.policy.decision",
                "-f", "json",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except subprocess.TimeoutExpired:
            return {"decision": "deny", "reason": "OPA evaluation timeout", "autonomy_level": autonomy_level}
        except FileNotFoundError:
            return {"decision": "deny", "reason": "OPA binary not found", "autonomy_level": autonomy_level}
        finally:
            Path(input_file).unlink(missing_ok=True)

        if result.returncode != 0:
            return {"decision": "deny", "reason": f"OPA error: {result.stderr}", "autonomy_level": autonomy_level}

        try:
            output = json.loads(result.stdout)
            decisions = output.get("result", [])
            if decisions:
                decision_obj = decisions[0].get("expressions", [{}])[0].get("value", {})
                # Rego returns {decision, reason} not {allow, reason}
                return {
                    "decision": decision_obj.get("decision", "deny"),
                    "reason": decision_obj.get("reason", "OPA evaluation"),
                    "autonomy_level": autonomy_level,
                }
        except (json.JSONDecodeError, IndexError, KeyError):
            pass

        return {"decision": "deny", "reason": "OPA evaluation failed", "autonomy_level": autonomy_level}