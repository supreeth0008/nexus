
from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from ..observe.models import ObserveResult
from .base import Analyzer
from .registry import register


@register("compliance")
class ComplianceAnalyzer(Analyzer):
    name="compliance"
    def analyze(self, result: ObserveResult) -> list[Incident]:
        incidents=[]
        # Tagging policy, region restrictions
        for s in result.signals:
            n=s.name.lower()
            if "tag" in n and ("missing" in n or "untagged" in n):
                try:
                    v=float(s.value)
                    if v>0:
                        incidents.append(Incident(
                            type=IncidentType.compliance_drift,
                            severity=Severity.medium,
                            status=IncidentStatus.detected,
                            probe_id=f"{result.provider}-compliance",
                            target_id=result.target_name,
                            source_signal=s.name,
                            root_cause="resource tagging policy violation",
                            confidence=0.65
                        ))
                except Exception:
                    pass
            if "region" in n and "forbidden" in n:
                incidents.append(Incident(
                    type=IncidentType.compliance_drift,
                    severity=Severity.high,
                    status=IncidentStatus.detected,
                    probe_id=f"{result.provider}-compliance",
                    target_id=result.target_name,
                    source_signal=s.name,
                    root_cause="resource deployed in non-compliant region",
                    confidence=0.9
                ))
        return incidents
