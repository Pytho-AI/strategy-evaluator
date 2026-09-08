# events

Intended use case: Multi-INT Fusion.
Six hundred AIS-like, RF-like, and social-like events reference the fictional base entities.
Observed entity IDs are withheld on 40 percent of rows; truth IDs support resolution scoring.

Base tables referenced: entities, facts, claims.

```python
from dataset import load
data = load(extensions=["events"])
rows = data["events"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
