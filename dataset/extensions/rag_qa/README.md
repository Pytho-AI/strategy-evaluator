# rag_qa

Intended use case: RAG Intelligence Service.
Questions test single-hop, joined, temporal, absent-answer, and doctrinal retrieval.
Gold answers cite base claim IDs or a doctrine location.

Base tables referenced: claims, facts, sources, entities.

```python
from dataset import load
data = load(extensions=["rag_qa"])
rows = data["questions"]
print(rows.head())
print(len(rows))
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
