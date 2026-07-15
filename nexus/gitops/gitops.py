from ..models.action import Action, ActionStatus
from ..models.incident import Incident
from .github import BranchManager, GitHubClient


# I orchestrate GitOps PR flow
class GitOpsEngine:
    def __init__(self, github_token: str="", repo: str="supreeth0008/nexus"):
        self.gh = GitHubClient(github_token, repo)
        self.branches = BranchManager()
    def apply_via_pr(self, incident: Incident, action: Action) -> dict:
        # I create a branch
        branch = self.branches.create_fix_branch(incident.id, incident.type.value)
        title = f"fix({incident.type.value}): auto-remediation for {incident.id[:8]}"
        body = f"""## Nexus Autonomous Fix

**Incident:** {incident.id}
**Type:** {incident.type.value}
**Severity:** {incident.severity.value}
**Root cause:** {incident.root_cause}
**Confidence:** {incident.confidence:.2f}

**Generated fix:**
```
{action.summary}
```

**Risk:** {action.risk.value}
**Autonomy level:** see policy gate

---
*I generated this PR automatically via Nexus control plane.*
"""
        fix_path = self._fix_path(action, incident.id)
        pr = self.gh.create_pr(
            branch,
            title,
            body,
            fix_path=fix_path,
            fix_content=action.diff or "",
        )
        # I update action
        action.pr_url = pr["pr_url"]
        action.status = ActionStatus.proposed
        return pr

    def _fix_path(self, action: Action, incident_id: str) -> str:
        short_id = incident_id[:8]
        kind = action.kind.value
        if kind == "kubernetes":
            return f"nexus-fix-{short_id}.yaml"
        if kind == "opentofu":
            return f"nexus-fix-{short_id}.tf"
        if kind == "helm":
            return f"nexus-fix-{short_id}-values.yaml"
        return f"nexus-fix-{short_id}.txt"
