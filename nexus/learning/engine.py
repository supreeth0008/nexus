from collections import defaultdict


# I learn from past incidents to improve future cycles
class LearningEngine:
    def __init__(self):
        self.patterns: dict[str, int] = defaultdict(int)
        self.fix_success: dict[str, list[bool]] = defaultdict(list)

    def record_incident(
        self,
        incident_type: str,
        root_cause: str,
        fix_applied: bool,
        verified: bool,
    ):
        # I track pattern frequency
        key = f"{incident_type}:{root_cause[:40]}"
        self.patterns[key] += 1
        self.fix_success[incident_type].append(verified)

    def predict(self, incident_type: str) -> dict:
        # I return learned statistics
        total = len(self.fix_success.get(incident_type, []))
        if total == 0:
            return {"known": False, "success_rate": 0.5}
        successes = sum(self.fix_success[incident_type])
        return {"known": True, "success_rate": successes / total, "samples": total}

    def top_patterns(self, n=5):
        return sorted(self.patterns.items(), key=lambda x: x[1], reverse=True)[:n]
