
from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from ..observe.models import ObserveResult
from .base import Analyzer
from .registry import register


@register("security")
class SecurityAnalyzer(Analyzer):
    name="security"
    def analyze(self, result: ObserveResult) -> list[Incident]:
        incidents=[]
        # Heuristic: open ports, 0.0.0.0, public s3, etc.
        # Since observe signals are generic, I look for risky labels/values
        for s in result.signals:
            # Example: security group signal
            if "sg" in s.name.lower() or "security" in s.name.lower():
                # If value is 0.0.0.0 or public
                if "0.0.0.0" in str(s.value) or "public" in str(s.value).lower():
                    incidents.append(Incident(
                        type=IncidentType.security_drift,
                        severity=Severity.critical,
                        status=IncidentStatus.detected,
                        probe_id=f"{result.provider}-security",
                        target_id=result.target_name,
                        source_signal=s.name,
                        root_cause="overly permissive network rule detected",
                        confidence=0.85,
                        metadata={"signal":s.model_dump(mode="json")}
                    ))
            # Unencrypted storage heuristic
            if "encrypt" in s.name.lower():
                try:
                    if float(s.value)==0:
                        incidents.append(Incident(
                            type=IncidentType.security_drift,
                            severity=Severity.high,
                            status=IncidentStatus.detected,
                            probe_id=f"{result.provider}-security",
                            target_id=result.target_name,
                            source_signal=s.name,
                            root_cause="unencrypted resource detected",
                            confidence=0.8
                        ))
                except Exception:
                    pass
        # Also degrade status = degraded/unreachable can imply security?
        if result.status=="degraded" and any("auth" in sig.name.lower() or "tls" in sig.name.lower() for sig in result.signals):
            incidents.append(Incident(
                type=IncidentType.security_drift,
                severity=Severity.medium,
                status=IncidentStatus.detected,
                probe_id=f"{result.provider}-security",
                target_id=result.target_name,
                source_signal="auth_degraded",
                root_cause="authentication layer degraded",
                confidence=0.5
            ))
        return incidents
