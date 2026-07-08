from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.action import Action


class ValidationResult:
    def __init__(self, valid: bool, message: str="", details: dict=None):
        self.valid=valid; self.message=message; self.details=details or {}
class Validator(ABC):
    @abstractmethod
    def validate(self, action: Action) -> ValidationResult: ...
