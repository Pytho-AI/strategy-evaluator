# authority

Intended use case: Mission Authority Broker.
Four role-named tiers route actions and recommendations by reversibility and risk.
The decision log ships empty; 24 inject-derived examples are provided separately.

Base tables referenced: claims, harmful_events, risk_assessments, actions.

```python
from dataset import load
data = load(extensions=["authority"])
rows = data["authority_tiers"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
