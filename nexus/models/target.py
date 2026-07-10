from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class CloudProvider(StrEnum):
    aws = "aws"
    azure = "azure"
    gcp = "gcp"
    kubernetes = "kubernetes"
    localstack = "localstack"


class TargetStatus(StrEnum):
    active = "active"
    unreachable = "unreachable"
    disabled = "disabled"


class TargetAuth(BaseModel):
    method: str = "env"
    profile: str | None = None
    region: str | None = None


class Target(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider: CloudProvider
    regions: list[str] = Field(default_factory=list)
    endpoint: str = ""
    auth: TargetAuth = Field(default_factory=TargetAuth)
    status: TargetStatus = TargetStatus.active
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
