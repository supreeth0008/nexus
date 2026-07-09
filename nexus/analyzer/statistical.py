import statistics

from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from ..observe.models import ObserveResult
from .base import Analyzer
from .registry import register


@register("statistical")
class StatisticalAnalyzer(Analyzer):
    name = "statistical"
    def analyze(self, result: ObserveResult) -> list[Incident]:
        incidents: list[Incident] = []
        # Collect numeric signals
        nums = [
            (s.name, float(s.value))
            for s in result.signals
            if isinstance(s.value, (int, float))
        ]
        if len(nums) < 3:
            return incidents
        values = [v for _,v in nums]
        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values)>1 else 0
        except statistics.StatisticsError:
            return incidents
        for name, val in nums:
            if stdev>0:
                z = abs((val-mean)/stdev)
                if z>3.0:
                    incidents.append(Incident(
                        type=IncidentType.performance_degradation,
                        severity=Severity.high if z>4 else Severity.medium,
                        status=IncidentStatus.detected,
                        probe_id=f"{result.provider}-stat",
                        target_id=result.target_name,
                        source_signal=f"{name}={val} z={z:.2f}",
                        root_cause=f"statistical outlier detected: {name}",
                        confidence=min(0.95, z/5.0),
                        metadata={"analyzer":"statistical","z_score":z,"mean":mean,"stdev":stdev}
                    ))
            # moving average spike simple
            if "latency" in name.lower() or "duration" in name.lower():
                if val > mean*2 and val>100:
                    incidents.append(Incident(
                        type=IncidentType.performance_degradation,
                        severity=Severity.medium,
                        status=IncidentStatus.detected,
                        probe_id=f"{result.provider}-stat",
                        target_id=result.target_name,
                        source_signal=f"{name}={val}",
                        root_cause="latency exceeds 2x moving baseline",
                        confidence=0.6
                    ))
        return incidents
