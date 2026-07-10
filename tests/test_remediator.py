import pytest

from nexus.models.action import ActionKind
from nexus.models.incident import Incident, IncidentType, Severity
from nexus.remediator.kubernetes.manifest import KubernetesRemediator
from nexus.remediator.registry import get_remediators


def _make_incident(
    incident_type: IncidentType = IncidentType.scaling_bottleneck,
    **kwargs,
) -> Incident:
    defaults = {
        "id": "inc-rem-001",
        "type": incident_type,
        "severity": Severity.high,
        "target_id": "demo-k8s",
        "root_cause": "HPA max replicas too low",
        "confidence": 0.8,
    }
    defaults.update(kwargs)
    return Incident(**defaults)


def test_opentofu_remediator_generates_action():
    incident = _make_incident(IncidentType.scaling_bottleneck)
    remediators = get_remediators()
    opentofu = next((r for r in remediators if r.name == "opentofu"), None)
    assert opentofu is not None
    assert opentofu.can_remediate(incident) is True

    actions = opentofu.generate(incident)
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == ActionKind.opentofu
    assert action.incident_id == incident.id
    assert len(action.diff) > 0


def test_opentofu_remediator_handles_unsupported_incident():
    incident = _make_incident(IncidentType.custom)
    remediators = get_remediators()
    opentofu = next((r for r in remediators if r.name == "opentofu"), None)
    assert opentofu is not None
    assert opentofu.can_remediate(incident) is False
    actions = opentofu.generate(incident)
    assert len(actions) == 1  # falls back to default template


def test_remediators_handle_minimal_incident_without_crashing():
    """A bare-minimum incident should not crash generate()."""
    incident = Incident(
        id="inc-rem-minimal",
        type=IncidentType.security_drift,
        severity=Severity.critical,
    )
    for remediator in get_remediators():
        try:
            if remediator.can_remediate(incident):
                remediator.generate(incident)
        except Exception as exc:
            pytest.fail(f"{remediator.name} crashed on minimal incident: {exc}")


def test_kubernetes_remediator_bad_image_and_resources():
    """A Kubernetes incident with a bad image tag gets a context-specific YAML patch."""
    incident = _make_incident(
        IncidentType.reliability_degradation,
        target_id="nexus-demo",
        root_cause="bad image tag and impossible resource requests",
        metadata={
            "target_provider": "kubernetes",
            "namespace": "nexus-demo",
            "deployment": "broken-app",
            "container": "app",
            "image": "nginx:this-tag-does-not-exist-99999",
            "resource_requests": {"cpu": "999999", "memory": "999999Gi"},
        },
    )

    remediators = get_remediators()

    # Only the Kubernetes remediator should claim this incident
    assert KubernetesRemediator().can_remediate(incident) is True
    for r in remediators:
        if r.name == "kubernetes":
            assert r.can_remediate(incident) is True
        else:
            assert r.can_remediate(incident) is False, f"{r.name} should not remediate k8s incident"

    # Generate the fix
    k8s = next((r for r in remediators if r.name == "kubernetes"), None)
    assert k8s is not None
    actions = k8s.generate(incident)
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == ActionKind.kubernetes
    assert action.incident_id == incident.id

    diff = action.diff
    assert "kind: Deployment" in diff
    assert "name: broken-app" in diff
    assert "namespace: nexus-demo" in diff
    assert "image: nginx:latest" in diff
    assert "cpu: \"100m\"" in diff
    assert "memory: \"128Mi\"" in diff
    assert "cpu: \"500m\"" in diff
    assert "memory: \"512Mi\"" in diff


def test_kubernetes_remediator_uses_fixed_image_when_provided():
    incident = _make_incident(
        IncidentType.reliability_degradation,
        target_id="nexus-demo",
        metadata={
            "target_provider": "kubernetes",
            "deployment": "broken-app",
            "container": "app",
            "image": "nginx:this-tag-does-not-exist-99999",
            "fixed_image": "nginx:1.25.3-alpine",
        },
    )
    k8s = KubernetesRemediator()
    actions = k8s.generate(incident)
    assert "image: nginx:1.25.3-alpine" in actions[0].diff
