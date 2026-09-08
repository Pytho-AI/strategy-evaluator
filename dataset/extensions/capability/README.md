# capability

Intended use case: Capability Assessment Visualization.
Six areas per actor combine numeric readiness, count, range, and sustainment claims.
Scores are normalized to 0–1 and recomputed for each inject world version.

Base tables referenced: entities, claims, sources.

```python
from dataset import load
data = load(extensions=["capability"])
rows = data["capability_areas"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
