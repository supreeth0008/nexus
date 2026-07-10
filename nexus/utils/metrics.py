# I expose Prometheus metrics for Nexus itself
# In-memory counters; replace with prometheus-client registry for production scraping.

_counters: dict[str, int] = {
    "nexus_cycles_total": 0,
    "nexus_incidents_detected_total": 0,
    "nexus_incidents_resolved_total": 0,
    "nexus_fixes_applied_total": 0,
}

_labeled_counters: dict[str, dict[tuple[str, ...], int]] = {
    "nexus_api_requests_total": {},
    "nexus_policy_decisions_total": {},
}

_label_keys: dict[str, tuple[str, ...]] = {
    "nexus_api_requests_total": ("endpoint", "code"),
    "nexus_policy_decisions_total": ("decision",),
}


def inc(name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
    """Increment a counter, with optional Prometheus-style labels."""
    if labels:
        label_key = _label_keys.get(name)
        if label_key is None:
            return
        key = tuple(str(labels.get(k, "")) for k in label_key)
        _labeled_counters[name][key] = _labeled_counters[name].get(key, 0) + value
    elif name in _counters:
        _counters[name] += value


def get_metrics_text() -> str:
    lines: list[str] = []
    for k, v in _counters.items():
        lines.append(f"# HELP {k} Nexus metric")
        lines.append(f"# TYPE {k} counter")
        lines.append(f"{k} {v}")
    for name, data in _labeled_counters.items():
        if not data:
            continue
        lines.append(f"# HELP {name} Nexus metric")
        lines.append(f"# TYPE {name} counter")
        for key, value in data.items():
            label_parts = [
                f'{label_key}="{label_value}"'
                for label_key, label_value in zip(_label_keys[name], key, strict=True)
            ]
            label_str = ",".join(label_parts)
            lines.append(f"{name}{{{label_str}}} {value}")
    return "\n".join(lines) + "\n" if lines else ""
