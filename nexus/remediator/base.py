from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from ..models.incident import Incident
from ..models.action import Action
class Remediator(ABC):
    name: str = "base"
    @abstractmethod
    def can_remediate(self, incident: Incident) -> bool: ...
    @abstractmethod
    def generate(self, incident: Incident) -> List[Action]: ...
