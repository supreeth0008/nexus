# I query Git history to correlate incidents with recent changes.
# MVP: stub that returns empty – in production I would clone the IaC repo and parse git log.


def recent_changes(repo_path: str = ".", hours: int = 24) -> list[dict]:
    # I return an empty list in MVP; Phase 3+ will implement real git log parsing.
    return []
def score_changes(changes: list[dict], incident_type: str) -> list[dict]:
    # I would score each commit by file paths touched vs incident type.
    return []
