
from .base import Remediator

_registry: dict[str, type[Remediator]] = {}
def register(name: str):
    def deco(cls: type[Remediator]):
        _registry[name] = cls
        return cls
    return deco
def get_remediators() -> list[Remediator]:
    return [cls() for cls in _registry.values()]
