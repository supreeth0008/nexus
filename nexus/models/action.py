from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ActionKind(StrEnum):
    opentofu="opentofu"; kubernetes="kubernetes"; helm="helm"
class ActionRisk(StrEnum):
    low="low"; medium="medium"; high="high"
class ActionStatus(StrEnum):
    proposed="proposed"; validated="validated"; applied="applied"; rejected="rejected"; rolled_back="rolled_back"
class Action(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    kind: ActionKind
    summary: str=""
    diff: str=""
    risk: ActionRisk=ActionRisk.low
    status: ActionStatus=ActionStatus.proposed
    pr_url: str=""
    created_at: datetime=Field(default_factory=datetime.utcnow)
    applied_at: datetime | None=None
