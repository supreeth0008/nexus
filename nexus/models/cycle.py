from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
class CycleTrigger(str, Enum):
    scheduled="scheduled"; event="event"; manual="manual"
class CycleStatus(str, Enum):
    running="running"; completed="completed"; failed="failed"; aborted="aborted"
class Cycle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]=None
    trigger: CycleTrigger = CycleTrigger.scheduled
    status: CycleStatus = CycleStatus.running
    observe_at: Optional[datetime]=None
    detect_at: Optional[datetime]=None
    diagnose_at: Optional[datetime]=None
    generate_at: Optional[datetime]=None
    validate_at: Optional[datetime]=None
    apply_at: Optional[datetime]=None
    verify_at: Optional[datetime]=None
    incidents_detected: int=0
    fixes_applied: int=0
    errors: List[str]=Field(default_factory=list)
    target_id: str=""
