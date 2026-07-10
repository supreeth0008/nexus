from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from .incident import IncidentType


class PolicyScope(BaseModel):
    incident_types: list[IncidentType] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    providers: list[str] = Field(default_factory=list)
    time_window: str = "always"


class PolicyDecision(StrEnum):
    allow = "allow"
    deny = "deny"
    require_approval = "require_approval"


class Policy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    rego: str
    scope: PolicyScope = Field(default_factory=PolicyScope)
    autonomy: int = Field(default=0, ge=0, le=4)
    enabled: bool = True
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
