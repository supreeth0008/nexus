# Nexus Makefile
# Standard targets for building, testing, and linting the project.

BINARY    := nexus
MODULE    := github.com/supreeth0008/nexus
VERSION   ?= v0.1.0-dev
COMMIT    := $(shell git rev-parse --short HEAD 2>/dev/null || echo none)
DATE      := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
LDFLAGS   := -s -w \
	-X '$(MODULE)/internal/utils.version=$(VERSION)' \
	-X '$(MODULE)/internal/utils.commit=$(COMMIT)' \
	-X '$(MODULE)/internal/utils.date=$(DATE)'

.PHONY: all build test lint fmt vet clean tidy help

all: build

## build: Compile the nexus binary
build:
	go build -ldflags "$(LDFLAGS)" -o $(BINARY) .

## test: Run all tests with race detection
test:
	go test -race -count=1 ./...

## cover: Run tests with coverage report
cover:
	go test -race -count=1 -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out | tail -1

## lint: Run golangci-lint (falls back to go vet if not installed)
lint:
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run ./...; \
	else \
		echo "golangci-lint not installed, running go vet"; \
		go vet ./...; \
	fi

## fmt: Format all Go source files
fmt:
	gofmt -s -w .

## vet: Run go vet
vet:
	go vet ./...

## tidy: Tidy module dependencies
tidy:
	go mod tidy

## clean: Remove build artifacts
clean:
	rm -f $(BINARY) coverage.out

## help: Show this help
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
