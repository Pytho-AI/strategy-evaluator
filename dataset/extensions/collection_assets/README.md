# collection_assets

Intended use case: Dynamic Collection Resource Optimization.
Eight fictional assets offer overlapping multi-discipline coverage with capacity and cost limits.
The greedy baseline maximizes requirement priority times success probability subject to asset capacity.

Base tables referenced: collection_requirements, pirs, entities, assumptions.

```python
from dataset import load
data = load(extensions=["collection_assets"])
rows = data["assets"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
