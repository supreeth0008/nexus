from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field
class ActionKind(str, Enum):
    opentofu="opentofu"; kubernetes="kubernetes"; helm="helm"
class ActionRisk(str, Enum):
    low="low"; medium="medium"; high="high"
class ActionStatus(str, Enum):
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
    applied_at: Optional[datetime]=None
