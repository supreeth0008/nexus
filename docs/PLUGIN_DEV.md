# Plugin Development

I designed Nexus to be pluggable first.

## Probe

```python
from nexus.observe.probes.base import Probe, get_probe
class MyProbe(Probe):
    name = "mycloud"
    def observe(self, target):
        # I return ObserveResult
        ...
```

Register automatically via get_probe mapping.

## Analyzer

```python
from nexus.analyzer.base import Analyzer
from nexus.analyzer.registry import register
@register("myanalyzer")
class MyAnalyzer(Analyzer):
    def analyze(self, result):
        # I return List[Incident]
        ...
```

## Remediator

```python
from nexus.remediator.base import Remediator
from nexus.remediator.registry import register
@register("myfix")
class MyRemediator(Remediator):
    def can_remediate(self, incident): ...
    def generate(self, incident): ...
```

I discover all via the registries at import time.
