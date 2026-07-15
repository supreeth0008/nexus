# I create real GitHub PRs for Nexus fixes
import base64
import os
from typing import Any

import httpx


class GitHubClient:
    def __init__(self, token: str = "", repo: str = ""):
        self.token = token or os.getenv("NEXUS_GITHUB_TOKEN", "")
        self.repo = repo or os.getenv("NEXUS_GITHUB_REPO", "supreeth0008/nexus")
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _create_blob(self, content: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/repos/{self.repo}/git/blobs",
            {
                "content": base64.b64encode(content.encode()).decode(),
                "encoding": "base64",
            },
        )

    def _request(self, method: str, path: str, json_data: dict | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=30.0) as client:
            resp = client.request(method, url, headers=self._headers(), json=json_data)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"GitHub API {method} {path} failed: {exc.response.status_code} {exc.response.text}"
            ) from exc
        data: dict[str, Any] = resp.json()
        return data

    def create_pr(
        self,
        branch: str,
        title: str,
        body: str,
        fix_path: str,
        fix_content: str,
        base: str = "main",
    ) -> dict[str, Any]:
        if not self.token:
            raise RuntimeError("NEXUS_GITHUB_TOKEN not configured; cannot create real PR")

        # 1. Get base branch reference
        ref_data = self._request("GET", f"/repos/{self.repo}/git/ref/heads/{base}")
        base_sha = ref_data["object"]["sha"]

        # 2. Create blobs for the real fix file and the human-readable summary
        fix_blob = self._create_blob(fix_content)
        summary_blob = self._create_blob(body)

        # 3. Get current tree
        base_commit = self._request("GET", f"/repos/{self.repo}/git/commits/{base_sha}")
        base_tree_sha = base_commit["tree"]["sha"]

        # 4. Create tree with both files
        summary_path = f"nexus-auto-fix-{branch.replace('/', '-')}.md"
        tree_data = self._request(
            "POST",
            f"/repos/{self.repo}/git/trees",
            {
                "base_tree": base_tree_sha,
                "tree": [
                    {
                        "path": fix_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": fix_blob["sha"],
                    },
                    {
                        "path": summary_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": summary_blob["sha"],
                    },
                ],
            },
        )

        # 5. Create commit
        commit_data = self._request(
            "POST",
            f"/repos/{self.repo}/git/commits",
            {
                "message": title,
                "tree": tree_data["sha"],
                "parents": [base_sha],
            },
        )

        # 6. Create branch ref
        try:
            self._request(
                "POST",
                f"/repos/{self.repo}/git/refs",
                {"ref": f"refs/heads/{branch}", "sha": commit_data["sha"]},
            )
        except RuntimeError as exc:
            if "422" in str(exc):
                # Branch may already exist; update it
                self._request(
                    "PATCH",
                    f"/repos/{self.repo}/git/refs/heads/{branch}",
                    {"sha": commit_data["sha"], "force": True},
                )
            else:
                raise

        # 7. Create PR
        pr_data = self._request(
            "POST",
            f"/repos/{self.repo}/pulls",
            {"title": title, "body": body, "head": branch, "base": base},
        )

        return {
            "pr_url": pr_data["html_url"],
            "pr_number": pr_data["number"],
            "branch": branch,
            "title": title,
            "state": pr_data["state"],
            "created_at": pr_data["created_at"],
            "simulated": False,
        }

    def add_label(self, pr_number: int, labels: list) -> bool:
        if not self.token:
            return False
        self._request(
            "POST",
            f"/repos/{self.repo}/issues/{pr_number}/labels",
            {"labels": labels},
        )
        return True


# I manage git branches locally
class BranchManager:
    def create_fix_branch(self, incident_id: str, incident_type: str) -> str:
        safe_type = incident_type.replace("_", "-")
        short_id = incident_id[:8]
        return f"nexus/fix/{short_id}-{safe_type}"
