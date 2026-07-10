import time
from datetime import datetime

import httpx

from ...config.settings import TargetConfig
from ..models import ObserveResult, Signal
from .base import Probe


class PrometheusProbe(Probe):
    name = "prometheus"

    def observe(self, target: TargetConfig) -> ObserveResult:
        start = time.time()
        signals = []
        status = "ok"
        error = ""
        try:
            with httpx.Client(timeout=3.0) as c:
                r = c.get(target.endpoint, follow_redirects=True)
                signals.append(Signal(
                    name="http_status",
                    value=float(r.status_code),
                    labels={"target": target.name},
                ))
                if r.status_code >= 400:
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
