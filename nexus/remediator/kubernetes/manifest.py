
from ...models.action import Action, ActionKind, ActionRisk
from ...models.incident import Incident
from ..base import Remediator
from ..registry import register


@register("kubernetes")
class KubernetesRemediator(Remediator):
    name="kubernetes"
    def can_remediate(self, incident: Incident) -> bool:
        return True
    def generate(self, incident: Incident) -> list[Action]:
        # I generate a K8s HPA / resources patch
        manifest = f"""---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nexus-fix-{incident.id[:8]}
  namespace: default
  annotations:
    nexus.incident/id: "{incident.id}"
    nexus.incident/type: "{incident.type.value}"
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
"""
        diff = manifest
        return [Action(
            incident_id=incident.id,
            kind=ActionKind.kubernetes,
            summary=f"I generated K8s HPA fix for {incident.type.value}",
            diff=diff,
            risk=ActionRisk.low
        )]
