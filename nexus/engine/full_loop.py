from datetime import datetime

from ..analyzer.registry import get_analyzers
from ..audit import AuditLedger
from ..diagnosis.engine import DiagnosisEngine
from ..gitops.gitops import GitOpsEngine
from ..models.cycle import Cycle, CycleStatus
from ..models.incident import Incident, IncidentStatus
from ..observe.runner import observe_all
from ..policy.gate import PolicyGate
from ..remediator.registry import get_remediators
from ..validator import ShadowValidator
from ..verifier import Verifier


# I run the full closed loop:
# Observe → Detect → Diagnose → Generate → Validate → Apply → Verify → Document
class FullLoopEngine:
    def __init__(self, autonomy_level: int = 0):
        self.autonomy_level = autonomy_level
        self.diagnoser = DiagnosisEngine()
        self.validator = ShadowValidator()
        self.policy = PolicyGate()
        self.gitops = GitOpsEngine()
        self.verifier = Verifier()
        self.audit = AuditLedger()
    def run(self, cfg) -> tuple[Cycle, list[Incident]]:
        from ..models.cycle import CycleTrigger
        autonomy = cfg.autonomy.level if hasattr(cfg, "autonomy") else self.autonomy_level
        cycle = Cycle(trigger=CycleTrigger.manual, status=CycleStatus.running)
        # Observe
        results = observe_all(cfg)
        cycle.observe_at = datetime.utcnow()
        cycle.incidents_detected = 0
        # Detect
        incidents = []
        for r in results:
            for analyzer in get_analyzers():
                try:
                    incidents.extend(analyzer.analyze(r))
                except Exception as e:
                    cycle.errors.append(f"analyzer {analyzer.name}: {e}")
        cycle.detect_at = datetime.utcnow()
        cycle.incidents_detected = len(incidents)
        # Diagnose
        for inc in incidents:
            sigs = []
            for res in results:
                if res.target_name == inc.target_id:
                    sigs = res.signals
                    break
            try:
                self.diagnoser.diagnose(inc, sigs)
                self.audit.append(
                    inc.id, "diagnose",
                    {"root_cause": inc.root_cause, "confidence": inc.confidence},
                )
            except Exception as e:
                cycle.errors.append(f"diagnose {inc.id}: {e}")
        cycle.diagnose_at = datetime.utcnow()
        # Generate + Validate
        fixes_applied = 0
        rems = get_remediators()
        for inc in incidents:
            if inc.status.value != "diagnosed":
                continue
            # Generate
            actions = []
            for rm in rems:
                try:
                    if rm.can_remediate(inc):
                        actions.extend(rm.generate(inc))
                        break  # I take first successful remediator
                except Exception:
                    continue
            if not actions:
                continue
            action = actions[0]
            cycle.generate_at = datetime.utcnow()
            self.audit.append(
                inc.id, "generate",
                {"action_id": action.id, "kind": action.kind.value},
            )
            # Validate
            v = self.validator.validate(action)
            cycle.validate_at = datetime.utcnow()
            self.audit.append(inc.id, "validate", {"valid": v.valid, "message": v.message})
            if not v.valid:
                inc.status = IncidentStatus.failed
                continue
            action.status = "validated"
            # Policy gate
            decision, reason = self.policy.evaluate(inc, action, autonomy)
            self.audit.append(inc.id, "policy", {"decision": decision, "reason": reason})
            if decision == "deny":
                inc.status = IncidentStatus.escalated
                continue
            if decision == "require_approval":
                # I open PR but do not auto-apply
                pr = self.gitops.apply_via_pr(inc, action)
                inc.fix_pr_url = pr["pr_url"]
                inc.fix_generated = True
                if inc.can_transition(IncidentStatus.fix_ready):
                    inc.transition(IncidentStatus.fix_ready)
                continue
            # Apply – I simulate apply via GitOps auto-merge
            if decision == "allow":
                pr = self.gitops.apply_via_pr(inc, action)
                inc.fix_pr_url = pr["pr_url"]
                inc.fix_generated = True
                cycle.apply_at = datetime.utcnow()
                # Verify
                vr = self.verifier.verify(inc, action)
                cycle.verify_at = datetime.utcnow()
                self.audit.append(inc.id, "verify", vr)
                if vr.get("verified"):
                    # I mark resolved
                    if inc.can_transition(IncidentStatus.applying):
                        inc.transition(IncidentStatus.applying)
                    if inc.can_transition(IncidentStatus.verifying):
                        inc.transition(IncidentStatus.verifying)
                    if inc.can_transition(IncidentStatus.resolved):
                        inc.transition(IncidentStatus.resolved)
                    fixes_applied += 1
                    action.status = "applied"
                else:
                    inc.status = IncidentStatus.failed
                    action.status = "rejected"
        cycle.fixes_applied = fixes_applied
        cycle.completed_at = datetime.utcnow()
        cycle.status = CycleStatus.completed if not cycle.errors else CycleStatus.failed
        return cycle, incidents
