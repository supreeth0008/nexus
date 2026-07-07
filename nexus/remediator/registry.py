from typing import Dict, List, Type
from .base import Remediator
_registry: Dict[str, Type[Remediator]] = {}
def register(name: str):
    def deco(cls: Type[Remediator]):
        _registry[name] = cls
        return cls
    return deco
def get_remediators() -> List[Remediator]:
    return [cls() for cls in _registry.values()]
