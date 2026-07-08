
from .base import Analyzer

_registry: dict[str, type[Analyzer]] = {}
def register(name: str):
    def deco(cls: type[Analyzer]):
        _registry[name] = cls
        return cls
    return deco
def get_analyzers() -> list[Analyzer]:
    return [cls() for cls in _registry.values()]
def list_registered() -> list[str]:
    return list(_registry.keys())
