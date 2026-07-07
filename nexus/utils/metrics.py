# I expose Prometheus metrics for Nexus itself
# MVP: simple in-memory counters
_counters = {
    "nexus_cycles_total": 0,
    "nexus_incidents_detected_total": 0,
    "nexus_incidents_resolved_total": 0,
    "nexus_fixes_applied_total": 0,
}
def inc(name: str, value: int=1):
    if name in _counters:
        _counters[name] += value
def get_metrics_text() -> str:
    lines = []
    for k,v in _counters.items():
        lines.append(f"# HELP {k} Nexus metric")
        lines.append(f"# TYPE {k} counter")
        lines.append(f"{k} {v}")
    return "\n".join(lines)+"\n"
