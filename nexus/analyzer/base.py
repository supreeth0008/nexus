from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from ..observe.models import Signal, ObserveResult
from ..models.incident import Incident
class Analyzer(ABC):
    name: str = "base"
    @abstractmethod
    def analyze(self, result: ObserveResult) -> List[Incident]:
        ...
