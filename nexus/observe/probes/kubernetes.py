from .prometheus import PrometheusProbe


class KubernetesProbe(PrometheusProbe):
    name="kubernetes"
