from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.action import Action
from ..models.incident import Incident


class Remediator(ABC):
    name: str = "base"
    @abstractmethod
    def can_remediate(self, incident: Incident) -> bool: ...
    @abstractmethod
    def generate(self, incident: Incident) -> list[Action]: ...
