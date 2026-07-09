import datetime
import json
from typing import Any


# I maintain an append-only audit ledger per incident
class AuditLedger:
    def __init__(self):
        self.entries: list[dict[str, Any]] = []
    def append(self, incident_id: str, phase: str, data: dict[str, Any]):
        self.entries.append({
            "ts": datetime.datetime.utcnow().isoformat(),
            "incident_id": incident_id,
            "phase": phase,
            "data": data
        })
    def export_jsonl(self) -> str:
        return "\n".join(json.dumps(e) for e in self.entries)
    def export_loki(self) -> list[dict]:
        # I format for Loki push API
        return [
            {
                "stream": {"job": "nexus-audit", "incident": e["incident_id"]},
                "values": [[
                    str(int(datetime.datetime.utcnow().timestamp() * 1e9)),
                    json.dumps(e),
                ]],
            }
            for e in self.entries
        ]
