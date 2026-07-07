#!/usr/bin/env bash
# teardown.sh - remove the local Nexus development environment.

set -euo pipefail

CLUSTER_NAME="nexus-dev"

echo "[teardown] Deleting Kind cluster '${CLUSTER_NAME}' (if it exists)..."
kind delete cluster --name "${CLUSTER_NAME}" 2>/dev/null || true

echo "[teardown] Removing build artifacts..."
rm -f "$(dirname "$0")/../nexus" "$(dirname "$0")/../coverage.out"

echo "[teardown] Done."
