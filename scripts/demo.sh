#!/usr/bin/env bash
set -euo pipefail

# Nexus capability demo: init → status → observe → detect → fix generate → run --autonomy 2

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

# Prefer the local virtual environment if it exists.
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

DEMO_DIR="$(mktemp -d)"
trap 'rm -rf "$DEMO_DIR"' EXIT

echo "=== Nexus capability demo ==="
cd "$DEMO_DIR"
"$PYTHON" -m nexus init --name demo-project
"$PYTHON" -m nexus status
"$PYTHON" -m nexus observe --target demo-k8s
"$PYTHON" -m nexus detect --target demo-k8s
"$PYTHON" -m nexus fix generate demo --kind opentofu
"$PYTHON" -m nexus run --autonomy 2 --trigger manual
echo "=== Demo complete ==="
