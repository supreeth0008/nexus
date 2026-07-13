
from ..models.incident import Incident, IncidentStatus, IncidentType, Severity
from ..observe.models import ObserveResult
from ..utils.logging import get_logger
from .base import Analyzer
from .registry import register

logger = get_logger(__name__)


@register("cost")
class CostAnalyzer(Analyzer):
    name="cost"
    def analyze(self, result: ObserveResult) -> list[Incident]:
        incidents=[]
        # Look for cost-related signals
        for s in result.signals:
            n=s.name.lower()
            if "cost" in n or "spend" in n or "billing" in n:
                try:
                    v=float(s.value)
                    if v>0:
                        # naive spike: if signal has labels with baseline?
                        # For MVP, flag any cost signal > 1000 as spike demo
                        if v>1000:
                            incidents.append(Incident(
                                type=IncidentType.cost_spike,
                                severity=Severity.high,
                                status=IncidentStatus.detected,
                                probe_id=f"{result.provider}-cost",
                                target_id=result.target_name,
                                source_signal=f"{s.name}={v}",
                                root_cause="cost metric exceeded threshold",
                                confidence=0.7,
                                metadata={"cost_value":v}
                            ))
                except Exception:
                    logger.warning(
                        "cost_analyzer_failed_to_parse_signal",
                        signal=s.name,
                        value=s.value,
                    )
        return incidents
