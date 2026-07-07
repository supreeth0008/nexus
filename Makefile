.PHONY: build install test lint run status observe clean

PY=python3
PIP=pip

install:
	$(PIP) install -e .[dev]

build:
	$(PY) -m build || echo "build skipped - install build tool if needed"

test:
	pytest -q

lint:
	ruff check nexus tests

run:
	nexus --help

status:
	nexus status

observe:
	nexus observe

migrate:
	nexus migrate

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache

version:
	nexus version
