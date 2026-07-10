from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class CycleTrigger(StrEnum):
    scheduled = "scheduled"
    event = "event"
    manual = "manual"


class CycleStatus(StrEnum):
    running = "running"
    completed = "completed"
    failed = "failed"
    aborted = "aborted"


class Cycle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    trigger: CycleTrigger = CycleTrigger.scheduled
    status: CycleStatus = CycleStatus.running
    observe_at: datetime | None = None
    detect_at: datetime | None = None
    diagnose_at: datetime | None = None
    generate_at: datetime | None = None
    validate_at: datetime | None = None
    apply_at: datetime | None = None
    verify_at: datetime | None = None
    incidents_detected: int = 0
    fixes_applied: int = 0
    errors: list[str] = Field(default_factory=list)
    target_id: str = ""
