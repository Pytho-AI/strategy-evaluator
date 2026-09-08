# Generator

Run `python -m gen --seed 20260908` from `dataset/`. The ordered stages build scaffold data, bitemporal facts, document plans, rendered claims, strategies, payoff tensors, dependencies, risks, collection requirements, doctrinal products, injects, and package files.

Each assumption has an `index_k`. Payoff rows enumerate every Boolean assumption world. `eval/value.py` computes the change in expected utility for assumption `k` by holding all other assumption probabilities fixed and comparing `theta_k = 1` with `theta_k = 0`; this difference is `delta_k`. EVPI compares the best expected strategy before and after observing that bit.

To list claims carried by stale-echo sources:

```python
from dataset import load
d = load()
sources = d["sources"]
sources = sources[sources["perturbations"].apply(lambda values: "stale_echo" in values)]
print(d["claims"].merge(sources[["source_id", "path"]], on="source_id"))
```

IDs and output bytes are stable for seed 20260908. License: CC BY 4.0.
