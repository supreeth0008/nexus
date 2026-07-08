from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.incident import Incident
from ..observe.models import ObserveResult


class Analyzer(ABC):
    name: str = "base"
    @abstractmethod
    def analyze(self, result: ObserveResult) -> list[Incident]:
        ...
