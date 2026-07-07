# Contributing to Nexus

I welcome contributions – I built Nexus to be pluggable first.

## Dev quick start

I use Python 3.11+:

```bash
git clone https://github.com/supreeth0008/nexus
cd nexus
pip install -e .[dev]
pytest -q
nexus version
```

I run lint before every commit:
```bash
ruff check nexus tests
```

## Code style I enforce

- I write first-person comments: `# I do X` – never “we”
- I keep functions small, typed with Pydantic
- I never swallow exceptions silently – I log to cycle.errors
- I redact secrets – use `from nexus.security import redact`
- I add a test for every state machine transition

## PR process I follow

1. I fork, I branch `feat/<name>`
2. I run `make test && make lint`
3. I open PR – I fill the template with incident scenario if applicable
4. CI must be green – I use GitHub Actions

Thank you – I built Nexus because I believe clouds should heal themselves.
– Supreeth
