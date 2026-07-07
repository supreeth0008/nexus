from typing import List
from ..base import Remediator
from ..registry import register
from ...models.incident import Incident
from ...models.action import Action, ActionKind, ActionRisk
@register("helm")
class HelmRemediator(Remediator):
    name="helm"
    def can_remediate(self, incident: Incident) -> bool:
        return True
    def generate(self, incident: Incident) -> List[Action]:
        values = f"""# I generated Helm values override for incident {incident.id[:8]}
replicaCount: 5
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 70
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
"""
        return [Action(
            incident_id=incident.id,
            kind=ActionKind.helm,
            summary=f"I generated Helm values fix for {incident.type.value}",
            diff=values,
            risk=ActionRisk.low
        )]
