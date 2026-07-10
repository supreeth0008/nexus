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
            namespace = target.name
            pods = v1.list_namespaced_pod(namespace=namespace)

            pending = 0
            failed = 0
            crash_loop = 0
            image_pull_fail = 0
            for pod in pods.items:
                phase = pod.status.phase
                if phase == "Pending":
                    pending += 1
                elif phase in ("Failed", "Unknown"):
                    failed += 1

                for cs in pod.status.container_statuses or []:
                    waiting = cs.state.waiting
                    if not waiting:
                        continue
                    reason = waiting.reason or ""
                    if reason == "CrashLoopBackOff":
                        crash_loop += 1
                    if reason in ("ImagePullBackOff", "ErrImagePull"):
                        image_pull_fail += 1

            if pending:
                signals.append(Signal(
                    name="pending_pods",
                    value=float(pending),
                    labels={"target": target.name, "namespace": namespace},
                ))
            if failed:
                signals.append(Signal(
                    name="failed_pods",
                    value=float(failed),
                    labels={"target": target.name, "namespace": namespace},
                ))
            if crash_loop:
                signals.append(Signal(
                    name="crash_loop_pods",
                    value=float(crash_loop),
                    labels={"target": target.name, "namespace": namespace},
                ))
            if image_pull_fail:
                signals.append(Signal(
                    name="image_pull_fail_pods",
                    value=float(image_pull_fail),
                    labels={"target": target.name, "namespace": namespace},
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
