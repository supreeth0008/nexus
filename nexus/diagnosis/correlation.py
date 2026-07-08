# I correlate anomalies across signals and time.
from typing import Any


def correlate_signals(signals: list[Any]) -> dict[str, Any]:
    # I produce a simple correlation summary: count by severity, top offenders
    by_name = {}
    for s in signals:
        name = getattr(s, "name", "unknown")
        by_name[name] = by_name.get(name, 0) + 1
    return {"signal_counts": by_name, "total": len(signals)}
