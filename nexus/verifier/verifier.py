import random
import time

from ..models.action import Action
from ..models.incident import Incident


# I verify post-apply recovery
class Verifier:
    def verify(self, incident: Incident, action: Action) -> dict:
        # I simulate post-apply metric collection
        # In production I would re-query Prometheus / health endpoints
        time.sleep(0.1)  # I simulate observation delay
        # I produce a plausible recovery check
        # Success rate improves with lower risk and higher confidence
        base_success = 0.85
        if action.risk.value == "low":
            base_success += 0.1
        if action.risk.value == "high":
            base_success -= 0.2
        base_success += (incident.confidence * 0.1)
        success = random.random() < base_success
        # I return verification details
        return {
            "verified": success,
            "metrics_improved": success,
            "error_rate_delta": -0.75 if success else 0.1,
            "latency_p95_delta_ms": -120 if success else 15,
            "checked_at": time.time(),
            "notes": "I verified recovery via post-apply metrics comparison (simulated)"
        }
