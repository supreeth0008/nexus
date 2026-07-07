from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
class IncidentType(str, Enum):
    cost_spike = "cost_spike"
    performance_degradation = "performance_degradation"
    security_drift = "security_drift"
    compliance_drift = "compliance_drift"
    reliability_degradation = "reliability_degradation"
    scaling_bottleneck = "scaling_bottleneck"
    configuration_drift = "configuration_drift"
    resource_exhaustion = "resource_exhaustion"
    error_burst = "error_burst"
    custom = "custom"
class Severity(str, Enum):
    critical = "critical"; high = "high"; medium = "medium"; low = "low"; info = "info"
class IncidentStatus(str, Enum):
    detected = "detected"; diagnosing = "diagnosing"; diagnosed = "diagnosed"; fixing = "fixing"; fix_ready = "fix_ready"; applying = "applying"; verifying = "verifying"; resolved = "resolved"; failed = "failed"; escalated = "escalated"
VALID_TRANSITIONS: Dict[IncidentStatus, List[IncidentStatus]] = {
    IncidentStatus.detected: [IncidentStatus.diagnosing, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.diagnosing: [IncidentStatus.diagnosed, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.diagnosed: [IncidentStatus.fixing, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.fixing: [IncidentStatus.fix_ready, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.fix_ready: [IncidentStatus.applying, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.applying: [IncidentStatus.verifying, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.verifying: [IncidentStatus.resolved, IncidentStatus.failed, IncidentStatus.escalated],
    IncidentStatus.resolved: [],
    IncidentStatus.failed: [IncidentStatus.diagnosing],
    IncidentStatus.escalated: [IncidentStatus.fix_ready, IncidentStatus.failed],
}
class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: IncidentType
    severity: Severity
    status: IncidentStatus = IncidentStatus.detected
    probe_id: str = ""
    target_id: str = ""
    source_signal: str = ""
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    diagnosed_at: Optional[datetime] = None
    fixed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    root_cause: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fix_generated: bool = False
    fix_pr_url: str = ""
    fix_branch: str = ""
    fix_summary: str = ""
    verified: Optional[bool] = None
    mttr_seconds: int = 0
    cycle_id: str = ""
    log: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    def can_transition(self, to: IncidentStatus) -> bool:
        return to in VALID_TRANSITIONS.get(self.status, [])
    def transition(self, to: IncidentStatus) -> None:
        if not self.can_transition(to):
            raise ValueError(f"illegal status transition {self.status} -> {to} for incident {self.id}")
        self.status = to
        now = datetime.utcnow()
        if to == IncidentStatus.diagnosed: self.diagnosed_at = now
        elif to == IncidentStatus.fix_ready: self.fixed_at = now
        elif to == IncidentStatus.verifying: self.verified_at = now
        elif to == IncidentStatus.resolved:
            self.resolved_at = now
            if self.detected_at: self.mttr_seconds = int((now - self.detected_at).total_seconds())
