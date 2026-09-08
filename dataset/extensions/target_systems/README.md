# target_systems

Intended use case: Target System Object Development.
Four fictional systems connect base infrastructure, units, systems, and locations.
Criticality is a computable edge-betweenness proxy; JP 3-60 target system analysis uses analyst judgment.

Base tables referenced: entities, claims, facts.

```python
from dataset import load
data = load(extensions=["target_systems"])
rows = data["systems"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
