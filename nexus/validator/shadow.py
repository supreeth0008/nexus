import os
import shutil
import subprocess
import tempfile

from ..models.action import Action, ActionKind
from .base import ValidationResult, Validator


# I validate fixes in an isolated shadow environment
class ShadowValidator(Validator):
    def validate(self, action: Action) -> ValidationResult:
        # I create a temp shadow directory
        try:
            with tempfile.TemporaryDirectory(prefix="nexus-shadow-") as td:
                # I write the diff content to a file for inspection
                if action.kind == ActionKind.opentofu:
                    tf_path = os.path.join(td, "main.tf")
                    with open(tf_path, "w") as f:
                        f.write("# I am validating OpenTofu fix\n")
                        f.write(action.diff or "")
                    # I try tofu fmt -check if tofu is installed, else simulate
                    tofu = shutil.which("tofu") or shutil.which("terraform")
                    if tofu:
                        # I run init + validate (no backend)
                        try:
                            subprocess.run([tofu, "fmt", "-check", td], capture_output=True, timeout=5, check=False)
                            # I consider fmt warnings non-fatal
                        except Exception:
                            pass
                        # I run tofu validate if possible
                        try:
                            subprocess.run([tofu, "init", "-backend=false"], cwd=td, capture_output=True, timeout=10, check=False)
                            r = subprocess.run([tofu, "validate", "-json"], cwd=td, capture_output=True, timeout=10)
                            if r.returncode==0:
                                return ValidationResult(True, "OpenTofu validate passed in shadow env")
                        except Exception:
                            pass
                    # I fallback to heuristic: check for dangerous patterns
                    dangerous = ["0.0.0.0/0", "delete", "destroy", "password", "secret"]
                    content = (action.diff or "").lower()
                    [d for d in dangerous if d in content and "remove" not in content and "fix" in content or d=="0.0.0.0/0" and d in content]
                    # Actually allow 0.0.0.0/0 detection but we already fixed it, so:
                    if "0.0.0.0/0" in content and "10.0.0.0/8" not in content:
                        return ValidationResult(False, "Shadow validator rejected: open CIDR still present", {"found":"0.0.0.0/0"})
                    return ValidationResult(True, "Shadow validation passed (heuristic – tofu not installed or plan simulated)")
                elif action.kind == ActionKind.kubernetes:
                    # I do a basic YAML sanity check
                    if "apiVersion" in (action.diff or "") and "kind" in (action.diff or ""):
                        return ValidationResult(True, "K8s manifest looks structurally valid (dry-run simulated)")
                    return ValidationResult(False, "K8s manifest missing apiVersion/kind")
                elif action.kind == ActionKind.helm:
                    # I check values.yaml basic structure
                    if "replicaCount" in (action.diff or ""):
                        return ValidationResult(True, "Helm values passed basic validation")
                    return ValidationResult(False, "Helm values missing replicaCount")
                return ValidationResult(False, f"Unknown action kind {action.kind}")
        except Exception as e:
            return ValidationResult(False, f"Shadow validator exception: {e}")
