import time

from ..config.settings import Settings
from ..models.action import Action
from ..models.incident import Incident


# I verify post-apply recovery by re-observing the target
class Verifier:
    def verify(
        self,
        incident: Incident,
        action: Action,
        cfg: Settings | None = None,
    ) -> dict:
        if cfg is None:
            return self._fallback_verify(incident, action)

        from ..observe.runner import observe_target

        target = next(
            (t for t in cfg.targets if t.name == incident.target_id),
            None,
        )
        if target is None:
            return {
                "verified": False,
                "metrics_improved": False,
                "error": f"target {incident.target_id} not found in config",
                "checked_at": time.time(),
                "notes": "Cannot verify: incident target is not configured",
            }

        result = observe_target(target)
        signal_name = self._parse_signal_name(incident.source_signal)
        old_value = self._parse_signal_value(incident.source_signal)

        new_signal = next(
            (s for s in result.signals if s.name == signal_name),
            None,
        )

        if new_signal is None:
            # Signal no longer present -> considered cleared
            verified = True
            new_value = None
            improved = True
        else:
            try:
                new_value = float(new_signal.value)
            except (ValueError, TypeError):
                return {
                    "verified": False,
                    "metrics_improved": False,
                    "error": f"signal {signal_name} has non-numeric value {new_signal.value!r}",
                    "checked_at": time.time(),
                    "notes": "Cannot verify: non-numeric signal value",
                }

            if old_value is not None:
                improved = new_value < old_value
                cleared = new_value == 0
            else:
                improved = False
                cleared = new_value == 0

            # For pod-failure-style signals, "cleared" means zero.
            # For error-rate-style signals, zero also means cleared.
            verified = cleared

        return {
            "verified": verified,
            "metrics_improved": improved,
            "signal": signal_name,
            "old_value": old_value,
            "new_value": new_value,
            "target_status": result.status,
            "checked_at": time.time(),
            "notes": (
                f"Re-observed {incident.target_id}; signal '{signal_name}' "
                f"{'cleared' if verified else 'still present'}."
            ),
        }

    def _parse_signal_name(self, source_signal: str) -> str:
        if not source_signal:
            return ""
        # source_signal may be "name" or "name=value" or "name=valuems"
        return source_signal.split("=")[0].strip()

    def _parse_signal_value(self, source_signal: str) -> float | None:
        if not source_signal or "=" not in source_signal:
            return None
        value_part = source_signal.split("=", 1)[1].strip()
        # Strip suffixes like "ms"
        for suffix in ("ms",):
            if value_part.endswith(suffix):
                value_part = value_part[: -len(suffix)]
        try:
            return float(value_part)
        except (ValueError, TypeError):
            return None

    def _fallback_verify(self, incident: Incident, action: Action) -> dict:
        # Architecturally unable to re-observe; return a deterministic unknown.
        return {
            "verified": False,
            "metrics_improved": False,
            "error": "no config provided for re-observation",
            "checked_at": time.time(),
            "notes": "Verification requires a Settings config to re-observe the target",
        }
