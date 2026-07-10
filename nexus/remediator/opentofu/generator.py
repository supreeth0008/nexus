
from ...models.action import Action, ActionKind, ActionRisk
from ...models.incident import Incident, IncidentType
from ..base import Remediator
from ..registry import register

# I generate OpenTofu HCL fixes from incident types using built-in templates.
TEMPLATES: dict[str, str] = {
    "scale_up": '''
# I generated this fix for scaling bottleneck – {incident_id}
resource "aws_autoscaling_group" "app" {{
  min_size         = {min_size}
  max_size         = {max_size}
  desired_capacity = {desired}
}}
'''.strip(),
    "resize_instance": '''
# I generated this fix for resource exhaustion – {incident_id}
resource "aws_instance" "app" {{
  instance_type = "{instance_type}"
  # previous: {previous_type}
}}
'''.strip(),
    "fix_sg_rule": '''
# I generated this fix for security drift – {incident_id}
resource "aws_security_group_rule" "restricted" {{
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/8"]  # I removed 0.0.0.0/0
  security_group_id = aws_security_group.app.id
  description       = "Nexus auto-remediation {incident_id}"
}}
'''.strip(),
    "add_autoscaling": '''
# I generated this fix for scaling bottleneck
resource "aws_appautoscaling_target" "ecs" {{
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/{cluster}/{service}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}}
'''.strip(),
    "add_tags": '''
# I generated this fix for compliance drift
locals {{
  required_tags = {{
    Owner       = "nexus"
    Environment = "{environment}"
    ManagedBy   = "opentofu"
  }}
}}
'''.strip(),
    "enable_encryption": '''
# I generated this fix for security drift – enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "enc" {{
  bucket = "{bucket}"
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}
'''.strip(),
}
@register("opentofu")
class OpenTofuRemediator(Remediator):
    name = "opentofu"
    def can_remediate(self, incident: Incident) -> bool:
        # I can remediate most infra incidents via IaC, except explicitly Kubernetes-native ones
        provider = incident.metadata.get("target_provider", "")
        if provider == "kubernetes":
            return False
        return incident.type.value in {
            "scaling_bottleneck","resource_exhaustion","security_drift",
            "configuration_drift","compliance_drift","cost_spike",
            "performance_degradation","reliability_degradation"
        }
    def generate(self, incident: Incident) -> list[Action]:
        # I choose a template based on incident type and metadata
        mapping = {
            IncidentType.scaling_bottleneck: "scale_up",
            IncidentType.resource_exhaustion: "resize_instance",
            IncidentType.security_drift: "fix_sg_rule",
            IncidentType.compliance_drift: "add_tags",
            IncidentType.configuration_drift: "add_autoscaling",
            IncidentType.cost_spike: "scale_up",
            IncidentType.performance_degradation: "scale_up",
            IncidentType.reliability_degradation: "add_autoscaling",
        }
        tpl_key = mapping.get(incident.type, "scale_up")
        tpl = TEMPLATES.get(tpl_key, TEMPLATES["scale_up"])
        # I pull context from the incident
        previous_type = incident.metadata.get("previous_instance_type", "t3.medium")
        instance_type = incident.metadata.get("instance_type", "t3.large")
        cluster = incident.metadata.get("cluster", "prod")
        service = incident.metadata.get("service", "api")
        bucket = incident.metadata.get("bucket", "app-data")
        environment = incident.metadata.get("environment", "prod")
        # I render a simple diff
        rendered = tpl.format(
            incident_id=incident.id[:8],
            root_cause=incident.root_cause or "auto-remediation",
            min_size=3, max_size=10, desired=5,
            instance_type=instance_type,
            previous_type=previous_type,
            environment=environment,
            bucket=bucket,
            cluster=cluster, service=service
        )
        diff = f"--- a/main.tf\n+++ b/main.tf\n@@\n+{rendered.replace(chr(10), chr(10)+'+')}\n"
        risk = ActionRisk.low
        if incident.severity.value in ("critical","high"):
            risk = ActionRisk.medium
        if incident.type == IncidentType.security_drift:
            risk = ActionRisk.high
        action = Action(
            incident_id=incident.id,
            kind=ActionKind.opentofu,
            summary=(
                f"I generated OpenTofu fix for {incident.type.value}: "
                f"{tpl_key} ({incident.root_cause or 'no root cause'})"
            ),
            diff=diff,
            risk=risk
        )
        return [action]
