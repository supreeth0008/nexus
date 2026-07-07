from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
class CloudProvider(str, Enum):
    aws="aws"; azure="azure"; gcp="gcp"; kubernetes="kubernetes"; localstack="localstack"
class TargetStatus(str, Enum):
    active="active"; unreachable="unreachable"; disabled="disabled"
class TargetAuth(BaseModel):
    method: str = "env"; profile: Optional[str]=None; region: Optional[str]=None
class Target(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str; provider: CloudProvider
    regions: List[str] = Field(default_factory=list)
    endpoint: str = ""
    auth: TargetAuth = Field(default_factory=TargetAuth)
    status: TargetStatus = TargetStatus.active
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
