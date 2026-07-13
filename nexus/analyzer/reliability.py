
from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from ..observe.models import ObserveResult
from ..utils.logging import get_logger
from .base import Analyzer
from .registry import register

logger = get_logger(__name__)


@register("reliability")
class ReliabilityAnalyzer(Analyzer):
    name="reliability"
    def analyze(self, result: ObserveResult) -> list[Incident]:
        incidents=[]
        # error rate, crash loops, SLO burn
        error_signals = [
            s for s in result.signals
            if "error" in s.name.lower()
            or "5xx" in s.name.lower()
            or "fail" in s.name.lower()
        ]
        for s in error_signals:
            try:
                v=float(s.value)
                if v>0:
                    sev = Severity.critical if v>10 else Severity.high if v>1 else Severity.medium
                    incidents.append(Incident(
                        type=IncidentType.reliability_degradation,
                        severity=sev,
                        status=IncidentStatus.detected,
                        probe_id=f"{result.provider}-reliability",
                        target_id=result.target_name,
                        source_signal=f"{s.name}={v}",
                        root_cause="elevated error rate detected",
                        confidence=0.75,
                        metadata={"error_value":v}
                    ))
            except Exception:
                logger.warning(
                    "reliability_analyzer_failed_to_parse_error_signal",
                    signal=s.name,
                    value=s.value,
                )
        # pod crash / restart / pending / image pull failures
        for s in result.signals:
            if any(k in s.name.lower() for k in ("restart", "crash", "pending", "image_pull_fail")):
                try:
                    v=float(s.value)
                    if v>0:
                        incidents.append(Incident(
                            type=IncidentType.reliability_degradation,
                            severity=Severity.high,
                            status=IncidentStatus.detected,
                            probe_id=f"{result.provider}-reliability",
                            target_id=result.target_name,
                            source_signal=s.name,
                            root_cause=f"{s.name} detected",
                            confidence=0.7
                        ))
                except Exception:
                    logger.warning(
                        "reliability_analyzer_failed_to_parse_restart_signal",
                        signal=s.name,
                        value=s.value,
                    )
        # latency SLO
        for s in result.signals:
            if "latency" in s.name.lower() or "p95" in s.name.lower() or "p99" in s.name.lower():
                try:
                    v=float(s.value)
                    if v>1000:  # >1s
                        incidents.append(Incident(
                            type=IncidentType.performance_degradation,
                            severity=Severity.high if v>2000 else Severity.medium,
                            status=IncidentStatus.detected,
                            probe_id=f"{result.provider}-reliability",
                            target_id=result.target_name,
                            source_signal=f"{s.name}={v}ms",
                            root_cause="SLO latency threshold breached",
                            confidence=0.8
                        ))
                except Exception:
                    logger.warning(
                        "reliability_analyzer_failed_to_parse_latency_signal",
                        signal=s.name,
                        value=s.value,
                    )
        return incidents
