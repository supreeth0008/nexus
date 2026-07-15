import os
import time
from datetime import datetime

from kubernetes import client, config

from ...config.settings import TargetConfig
from ..models import ObserveResult, Signal
from .base import Probe


class KubernetesProbe(Probe):
    name = "kubernetes"

    def observe(self, target: TargetConfig) -> ObserveResult:
        start = time.time()
        status = "ok"
        error = ""
        signals: list[Signal] = []
        try:
            kubeconfig = os.getenv("KUBECONFIG") or os.path.expanduser("~/.kube/config")
            if os.path.exists(kubeconfig):
                config.load_kube_config(config_file=kubeconfig)
            else:
                config.load_incluster_config()

            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            namespace = target.name
            pods = v1.list_namespaced_pod(namespace=namespace)

            pending = 0
            failed = 0
            crash_loop = 0
            image_pull_fail = 0
            first_pending: dict[str, str] = {}
            first_failed: dict[str, str] = {}
            first_crash: dict[str, str] = {}
            first_image_pull: dict[str, str] = {}

            for pod in pods.items:
                phase = pod.status.phase
                if phase == "Pending":
                    pending += 1
                    if not first_pending:
                        first_pending = self._pod_details(pod, apps_v1)
                elif phase in ("Failed", "Unknown"):
                    failed += 1
                    if not first_failed:
                        first_failed = self._pod_details(pod, apps_v1)

                for cs in pod.status.container_statuses or []:
                    waiting = cs.state.waiting
                    if not waiting:
                        continue
                    reason = waiting.reason or ""
                    if reason == "CrashLoopBackOff":
                        crash_loop += 1
                        if not first_crash:
                            first_crash = self._pod_details(pod, apps_v1)
                    if reason in ("ImagePullBackOff", "ErrImagePull"):
                        image_pull_fail += 1
                        if not first_image_pull:
                            first_image_pull = self._pod_details(pod, apps_v1)

            if pending:
                signals.append(self._problem_signal(
                    "pending_pods", pending, target, namespace, first_pending
                ))
            if failed:
                signals.append(self._problem_signal(
                    "failed_pods", failed, target, namespace, first_failed
                ))
            if crash_loop:
                signals.append(self._problem_signal(
                    "crash_loop_pods", crash_loop, target, namespace, first_crash
                ))
            if image_pull_fail:
                signals.append(self._problem_signal(
                    "image_pull_fail_pods", image_pull_fail, target, namespace, first_image_pull
                ))
            if pending or failed or crash_loop or image_pull_fail:
                status = "degraded"
        except Exception as e:
            error = str(e)
            status = "unreachable"

        duration_ms = int((time.time() - start) * 1000)
        signals.append(Signal(
            name="probe_duration_ms",
            value=float(duration_ms),
            labels={"probe": self.name, "target": target.name},
        ))
        return ObserveResult(
            target_name=target.name,
            provider=target.provider,
            status=status,
            signals=signals,
            duration_ms=duration_ms,
            error=error,
            timestamp=datetime.utcnow(),
        )

    def _pod_details(self, pod, apps_v1: client.AppsV1Api) -> dict[str, str]:
        """Extract deployment, container, image, and resource requests for a pod."""
        details: dict[str, str] = {
            "target_provider": "kubernetes",
            "namespace": pod.metadata.namespace or "default",
        }

        # Resolve deployment name via ReplicaSet owner reference.
        deployment = ""
        for owner in pod.metadata.owner_references or []:
            if owner.kind == "ReplicaSet":
                try:
                    rs = apps_v1.read_namespaced_replica_set(
                        owner.name, details["namespace"]
                    )
                    for rs_owner in rs.metadata.owner_references or []:
                        if rs_owner.kind == "Deployment":
                            deployment = rs_owner.name
                            break
                except Exception:
                    deployment = owner.name.rsplit("-", 1)[0]
                break
        if not deployment:
            deployment = pod.metadata.labels.get("app", pod.metadata.name or "app")
        details["deployment"] = deployment

        # Use the first container for remediation context.
        container_spec = pod.spec.containers[0] if pod.spec.containers else None
        if container_spec:
            details["container"] = container_spec.name
            details["image"] = container_spec.image or ""
            requests = container_spec.resources.requests or {}
            if requests:
                details["resource_requests_cpu"] = requests.get("cpu", "")
                details["resource_requests_memory"] = requests.get("memory", "")
        else:
            details["container"] = "app"
            details["image"] = ""

        return details

    def _problem_signal(
        self,
        name: str,
        count: int,
        target: TargetConfig,
        namespace: str,
        details: dict[str, str],
    ) -> Signal:
        labels = {
            "target": target.name,
            "namespace": namespace,
            **details,
        }
        return Signal(
            name=name,
            value=float(count),
            labels=labels,
        )
