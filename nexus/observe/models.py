from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Signal(BaseModel):
    name: str
    value: float | str | dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict[str, str] = Field(default_factory=dict)
    severity: str = "info"
class ObserveResult(BaseModel):
    target_name: str
    provider: str
    status: str
    signals: list[Signal] = Field(default_factory=list)
    duration_ms: int = 0
    error: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
