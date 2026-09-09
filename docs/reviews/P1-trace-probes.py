"""Read-only current-claim trace check. Run from repository root."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.backend.adapter import DatasetAdapter
from app.backend.views import claim_trace

adapter = DatasetAdapter()
for batch in range(4):
    index = adapter.index(batch)
    missing = []
    for assumption in index.rows("assumptions"):
        if not assumption["strategy_id"].startswith("str_blue_"):
            continue
        claim = index.current_claim(assumption["subject_id"], assumption["predicate"])
        if claim is None:
            continue
        trace = claim_trace(index, claim)
        linked = any(
            node.id == assumption["assumption_id"]
            for path in trace.paths
            for node in path.nodes
        )
        if not linked:
            missing.append({
                "assumption": assumption["assumption_id"],
                "claim": claim["claim_id"],
                "paths": len(trace.paths),
            })
    print("batch", batch, "selected-claim trace missing assumption", missing)

# The three inject claims the review named, with the path each now takes.
for batch, claim_id, assumption_id in ((1, "clm_0844", "asm_blue_1_k0"),
                                       (2, "clm_0850", "asm_blue_1_k2"),
                                       (3, "clm_0856", "asm_blue_2_k4")):
    index = adapter.index(batch)
    trace = claim_trace(index, index.claims[claim_id])
    for path in trace.paths:
        if any(node.id == assumption_id for node in path.nodes):
            print(
                f"batch {batch} {claim_id} -> {assumption_id}:",
                " -> ".join(f"{n.type}:{n.id}" for n in path.nodes),
                [e.basis for e in path.edges],
            )
