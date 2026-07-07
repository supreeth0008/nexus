from typing import Dict, List, Type
from .base import Analyzer
_registry: Dict[str, Type[Analyzer]] = {}
def register(name: str):
    def deco(cls: Type[Analyzer]):
        _registry[name] = cls
        return cls
    return deco
def get_analyzers() -> List[Analyzer]:
    return [cls() for cls in _registry.values()]
def list_registered() -> List[str]:
    return list(_registry.keys())
