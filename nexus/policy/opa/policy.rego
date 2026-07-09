package nexus.policy

# Nexus Autonomy Policy
# Evaluates whether an autonomous action should be allowed based on autonomy level
# and action risk profile.
#
# Decisions:
#   - "allow"            -> action can be auto-applied
#   - "require_approval" -> PR opened for manual review
#   - "deny"             -> no action permitted (observe only)

# Compute base decision based on autonomy level and action risk
base_decision = {"decision": "deny", "reason": "default deny"} {
    # L0: Observe only
    input.autonomy_level == 0
    input.action_exists
}

base_decision = {"decision": "require_approval", "reason": "L1: recommend mode - PR opened for manual review"} {
    input.autonomy_level == 1
    input.action_exists
}

base_decision = {"decision": "allow", "reason": "L2: auto-fix low risk permitted"} {
    input.autonomy_level == 2
    input.action_exists
    input.action.risk == "low"
}

base_decision = {"decision": "require_approval", "reason": "L2: medium/high risk requires approval"} {
    input.autonomy_level == 2
    input.action_exists
    input.action.risk != "low"
}

base_decision = {"decision": "allow", "reason": "L3: policy gate passed - auto-applied"} {
    input.autonomy_level == 3
    input.action_exists
    input.action.risk == "low"
}

base_decision = {"decision": "allow", "reason": "L3: policy gate passed - auto-applied"} {
    input.autonomy_level == 3
    input.action_exists
    input.action.risk == "medium"
    input.incident.confidence >= 0.8
}

base_decision = {"decision": "require_approval", "reason": "L3: high risk requires approval"} {
    input.autonomy_level == 3
    input.action_exists
    input.action.risk == "high"
}

base_decision = {"decision": "require_approval", "reason": "L3: medium risk with low confidence requires approval"} {
    input.autonomy_level == 3
    input.action_exists
    input.action.risk == "medium"
    input.incident.confidence < 0.8
}

base_decision = {"decision": "allow", "reason": "L4: full autonomy - all actions auto-applied"} {
    input.autonomy_level == 4
    input.action_exists
}

# Unknown autonomy level
base_decision = {"decision": "deny", "reason": "unknown autonomy level"} {
    input.autonomy_level != 0
    input.autonomy_level != 1
    input.autonomy_level != 2
    input.autonomy_level != 3
    input.autonomy_level != 4
    input.action_exists
}

# L0 with no action
base_decision = {"decision": "deny", "reason": "L0: observe only mode"} {
    input.autonomy_level == 0
    not input.action_exists
}

# Final decision: apply critical severity escalation if needed
decision = base_decision {
    not critical_escalation
}

decision = {"decision": "require_approval", "reason": "Critical severity escalated to human"} {
    critical_escalation
}

# Critical escalation applies when:
# - autonomy level < 4
# - action exists
# - incident severity is critical
# - base decision would be "allow"
critical_escalation {
    input.autonomy_level < 4
    input.action_exists
    input.incident.severity == "critical"
    base_decision.decision == "allow"
}

# Helper: action exists with risk
action_exists = true {
    input.action
    input.action.risk
}