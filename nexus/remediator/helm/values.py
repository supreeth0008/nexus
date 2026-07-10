
from ...models.action import Action, ActionKind, ActionRisk
from ...models.incident import Incident
from ..base import Remediator
from ..registry import register


@register("helm")
class HelmRemediator(Remediator):
    name = "helm"

    def can_remediate(self, incident: Incident) -> bool:
        # I remediate generic/container incidents unless they are explicitly Kubernetes-native
        provider: str = incident.metadata.get("target_provider", "")
        return provider != "kubernetes"

    def generate(self, incident: Incident) -> list[Action]:
        md = incident.metadata
        replica_count = md.get("replica_count", 5)
        cpu_request = md.get("cpu_request", "500m")
        memory_request = md.get("memory_request", "512Mi")
        cpu_limit = md.get("cpu_limit", "1000m")
        memory_limit = md.get("memory_limit", "1Gi")
        values = f"""# I generated Helm values override for incident {incident.id[:8]}
# Root cause: {incident.root_cause or 'not specified'}
replicaCount: {replica_count}
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 70
resources:
  requests:
    cpu: "{cpu_request}"
    memory: "{memory_request}"
  limits:
    cpu: "{cpu_limit}"
    memory: "{memory_limit}"
"""
        return [Action(
            incident_id=incident.id,
            kind=ActionKind.helm,
            summary=(
                f"I generated Helm values fix for {incident.type.value} "
                f"({incident.root_cause or 'no root cause'})"
            ),
            diff=values,
            risk=ActionRisk.low
        )]
