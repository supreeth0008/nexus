#!/usr/bin/env bash
# setup-dev.sh - one-command development environment setup for Nexus.
# I check each prerequisite, install what can be installed safely, and
# give clear instructions for anything that needs a manual step.

set -euo pipefail

GO_MIN="1.24"

info()  { echo "[setup] $*"; }
fail()  { echo "[setup] ERROR: $*" >&2; exit 1; }

info "Checking prerequisites..."

# Go
if ! command -v go >/dev/null 2>&1; then
    fail "Go ${GO_MIN}+ is required. Install from https://go.dev/dl/"
fi
info "Go found: $(go version)"

# Docker
if ! command -v docker >/dev/null 2>&1; then
    fail "Docker is required. Install Docker Desktop or Docker Engine: https://docs.docker.com/get-docker/"
fi
info "Docker found: $(docker --version)"

# kubectl
if ! command -v kubectl >/dev/null 2>&1; then
    info "Installing kubectl..."
    KVER=$(curl -L -s https://dl.k8s.io/release/stable.txt)
    OS=$(uname | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m); [ "$ARCH" = "x86_64" ] && ARCH=amd64; [ "$ARCH" = "aarch64" ] && ARCH=arm64
    curl -sSLo /tmp/kubectl "https://dl.k8s.io/release/${KVER}/bin/${OS}/${ARCH}/kubectl"
    chmod +x /tmp/kubectl
    sudo mv /tmp/kubectl /usr/local/bin/kubectl 2>/dev/null || mv /tmp/kubectl "$HOME/go/bin/kubectl"
fi
info "kubectl found: $(kubectl version --client --output=yaml 2>/dev/null | head -3 | tail -1 || true)"

# Kind
if ! command -v kind >/dev/null 2>&1; then
    info "Installing Kind..."
    go install sigs.k8s.io/kind@latest
fi
info "Kind found: $(kind version 2>/dev/null || echo 'installed to GOPATH/bin')"

# Helm
if ! command -v helm >/dev/null 2>&1; then
    info "Installing Helm..."
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi
info "Helm found: $(helm version --short 2>/dev/null || true)"

# golangci-lint
if ! command -v golangci-lint >/dev/null 2>&1; then
    info "Installing golangci-lint..."
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
fi

# OpenTofu (needed from Phase 3 onward; warn only)
if ! command -v tofu >/dev/null 2>&1; then
    info "NOTE: OpenTofu not found. It is needed from Phase 3 onward."
    info "      Install guide: https://opentofu.org/docs/intro/install/"
fi

# Go dependencies
info "Downloading Go module dependencies..."
go mod download

info "Development environment ready."
info "Next: ./scripts/setup-kind.sh to create the local cluster, then 'make build'."
