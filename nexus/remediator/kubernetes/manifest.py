
from ...models.action import Action, ActionKind, ActionRisk
from ...models.incident import Incident
from ..base import Remediator
from ..registry import register


@register("kubernetes")
class KubernetesRemediator(Remediator):
    name = "kubernetes"

    def can_remediate(self, incident: Incident) -> bool:
        # I only remediate Kubernetes-targeted incidents
        provider = incident.metadata.get("target_provider", "")
        return provider == "kubernetes" or incident.target_id.startswith("k8s-")

    def generate(self, incident: Incident) -> list[Action]:
        md = incident.metadata
        deployment = md.get("deployment", "app")
        namespace = md.get("namespace", "default")
        container = md.get("container", "app")

        # Determine corrected image
        image = md.get("image", "")
        fixed_image = md.get("fixed_image", "")
        if fixed_image:
            corrected_image = fixed_image
        elif image and ":" in image:
            # Strip the bad tag and default to latest
            corrected_image = image.split(":")[0] + ":latest"
        else:
            corrected_image = "nginx:latest"

        # Determine corrected resource requests
        resources = md.get("resource_requests", {})
        if resources:
            corrected_resources = """        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
"""
        else:
            corrected_resources = ""

        manifest = f"""---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {deployment}
  namespace: {namespace}
  annotations:
    nexus.incident/id: "{incident.id}"
    nexus.incident/type: "{incident.type.value}"
    nexus.fix/reason: "{incident.root_cause or 'auto-remediation'}"
spec:
  template:
    spec:
      containers:
      - name: {container}
        image: {corrected_image}
{corrected_resources}---
# I generated this Kubernetes fix for incident {incident.id[:8]}
# Original image: {image or '(unknown)'}
"""
        diff = manifest
        risk = (
            ActionRisk.medium
            if incident.severity.value in ("critical", "high")
            else ActionRisk.low
        )
        return [Action(
            incident_id=incident.id,
            kind=ActionKind.kubernetes,
            summary=(
                f"I generated K8s Deployment patch for {deployment}: "
                "correct image and resource requests"
            ),
            diff=diff,
            risk=risk,
        )]
