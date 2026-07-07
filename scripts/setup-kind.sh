#!/usr/bin/env bash
# setup-kind.sh - create (or recreate) the local Kind cluster for Nexus.

set -euo pipefail

CLUSTER_NAME="nexus-dev"
CONFIG_FILE="$(dirname "$0")/../deploy/kind/kind-config.yaml"

info() { echo "[kind] $*"; }

if ! command -v kind >/dev/null 2>&1; then
    echo "[kind] ERROR: kind is not installed. Run ./scripts/setup-dev.sh first." >&2
    exit 1
fi

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
    info "Cluster '${CLUSTER_NAME}' already exists."
    read -r -p "[kind] Delete and recreate it? [y/N] " answer
    if [[ "${answer}" =~ ^[Yy]$ ]]; then
        kind delete cluster --name "${CLUSTER_NAME}"
    else
        info "Keeping existing cluster."
        kubectl cluster-info --context "kind-${CLUSTER_NAME}"
        exit 0
    fi
fi

info "Creating cluster '${CLUSTER_NAME}'..."
kind create cluster --config "${CONFIG_FILE}"

info "Waiting for the node to become Ready..."
kubectl wait --for=condition=Ready node --all --timeout=120s

info "Cluster ready:"
kubectl get nodes
