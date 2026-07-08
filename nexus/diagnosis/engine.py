from __future__ import annotations

from datetime import datetime

from ..models.incident import Incident, IncidentStatus


# I correlate anomalies with recent changes to produce a root cause hypothesis.
class DiagnosisEngine:
    def diagnose(self, incident: Incident, signals: list) -> Incident:
        # I move incident to diagnosing
        if incident.can_transition(IncidentStatus.diagnosing):
            incident.transition(IncidentStatus.diagnosing)
        # I run simple correlation rules
        rc, conf = self._correlate(incident, signals)
        incident.root_cause = rc or incident.root_cause or "unknown – automated correlation found no clear change"
        # blend confidence
        incident.confidence = max(incident.confidence, conf)
        incident.diagnosed_at = datetime.utcnow()
        if incident.can_transition(IncidentStatus.diagnosed):
            incident.transition(IncidentStatus.diagnosed)
        # append to log
        incident.log.append({
            "ts": datetime.utcnow().isoformat(),
            "phase": "diagnose",
            "root_cause": incident.root_cause,
            "confidence": incident.confidence
        })
        return incident
    def _correlate(self, incident: Incident, signals: list) -> tuple[str, float]:
        # I check signal names for hints
        text_blob = " ".join([getattr(s, "name", "") + " " + str(getattr(s, "value", "")) for s in signals]).lower()
        # I map keywords to causes
        rules = [
            ("cpu", "CPU saturation – likely need scale up / resize", 0.75),
            ("memory", "Memory pressure – OOM risk, increase limits", 0.75),
            ("latency", "Upstream latency increase – check dependencies", 0.7),
            ("error", "Error burst – recent deployment likely culprit", 0.8),
            ("5xx", "Server errors – application crash or dependency failure", 0.8),
            ("disk", "Disk pressure – volume full or inode exhaustion", 0.7),
            ("cost", "Cost spike – new expensive resource or scaling event", 0.65),
            ("security", "Security posture drift – IAM / SG change detected", 0.8),
            ("unreachable", "Target connectivity lost – network / credentials", 0.9),
        ]
        for kw, cause, conf in rules:
            if kw in text_blob or kw in incident.source_signal.lower() or kw in incident.target_id.lower():
                return cause, conf
        # I fall back to incident type mapping
        type_map = {
            "performance_degradation": ("Performance regression – resource bottleneck suspected", 0.6),
            "reliability_degradation": ("Reliability drop – error rate / crashloop", 0.65),
            "security_drift": ("Security configuration drift detected", 0.7),
            "cost_spike": ("Unexpected cost increase – scaling or new resource", 0.6),
            "compliance_drift": ("Compliance tag / region policy violation", 0.65),
            "scaling_bottleneck": ("Scaling limit hit – HPA / ASG max reached", 0.75),
            "resource_exhaustion": ("Resource exhaustion – CPU / memory / disk", 0.75),
        }
        t = str(incident.type.value) if hasattr(incident.type, "value") else str(incident.type)
        return type_map.get(t, ("Undetermined – needs human triage", 0.4))
