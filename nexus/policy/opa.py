from typing import Dict, Any
from ..models.incident import Incident
from ..models.action import Action
# I evaluate OPA-style policies – MVP is a Python rules engine mimicking Rego
class OPAClient:
    def evaluate(self, incident: Incident, action: Action, autonomy_level: int) -> Dict[str, Any]:
        # I implement progressive autonomy gates
        # Level 0: always deny
        # Level 1: require_approval
        # Level 2: allow low risk
        # Level 3: allow low+medium if policy permits
        # Level 4: allow all
        decision = "deny"
        reason = ""
        if autonomy_level == 0:
            decision = "deny"; reason = "Observe only mode"
        elif autonomy_level == 1:
            decision = "require_approval"; reason = "Recommend mode – PR opened for manual review"
        elif autonomy_level == 2:
            if action.risk.value == "low":
                decision = "allow"; reason = "Auto-fix low risk permitted"
            else:
                decision = "require_approval"; reason = f"Risk {action.risk.value} requires approval at L2"
        elif autonomy_level == 3:
            # I check a simple policy: no critical severity auto-apply outside 9-17 UTC, etc.
            # MVP: allow low+medium
            if action.risk.value in ("low","medium"):
                decision = "allow"; reason = "Policy gate passed at L3"
            else:
                decision = "require_approval"; reason = "High risk requires approval at L3"
        elif autonomy_level >= 4:
            decision = "allow"; reason = "Full autonomy"
        # I also deny critical incidents at <L4 unless explicit
        if incident.severity.value == "critical" and autonomy_level < 4:
            # I escalate critical
            if decision == "allow":
                decision = "require_approval"; reason = "Critical severity escalated to human"
        return {"decision": decision, "reason": reason, "autonomy_level": autonomy_level}
