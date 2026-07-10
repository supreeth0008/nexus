from abc import ABC, abstractmethod


class Probe(ABC):
    name: str = "base"

    @abstractmethod
    def observe(self, target): ...


def get_probe(provider: str):
    if provider == "kubernetes":
        from .kubernetes import KubernetesProbe
        return KubernetesProbe()
    from .prometheus import PrometheusProbe
    return PrometheusProbe()
