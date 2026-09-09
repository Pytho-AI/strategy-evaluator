# P1 integration notes — in-progress source

These observations concern a live worktree after P0 commit 9299540. P1 is not yet
claimed complete. Recheck at the completed-phase gate.

## Round 4 — current evidence is missing from static trace walks

Success check: a claim selected by the evaluator for an assumption should have a trace
that reaches that assumption and its affected option. Historical relationships may remain,
but must be distinguished from the evidence currently used for the calculation.

The new views.claim_trace calls Index.walk over the frozen dependencies table. Many
selected current claims have no outgoing edges there. The runtime selection is correct,
but its evidence cannot be followed through this trace builder.

Independent command:

```sh
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/P1-trace-probes.py
```

Observed missing assumption links by batch: 6 at T0, 7 at batch 1, 9 at batch 2,
9 at batch 3. Every reported missing case had zero trace paths.

Examples:

- Batch 1: clm_0844 is selected for asm_blue_1_k0, but its trace has zero paths.
- Batch 2: clm_0850 is selected for asm_blue_1_k2 and asm_blue_3_k2, but its trace
  has zero paths. This is the basing-access inject used in the decision-recovery demo.
- Batch 3: clm_0856 is selected for asm_blue_2_k4, but its trace has zero paths.

The assumption view now exposes subject_id and predicate, which supports a join, but
does not yet expose selected claim IDs. Derive current-evidence relationships from the
same approved, temporal selection used by evaluation. Do not edit frozen dependencies
or label all historical/proposed matches as current evidence. Check inject claims in the
acceptance test, not only an old claim that happens to have static dependency edges.

This was reproduced against the derivation/view builder, not the unfinished HTTP wiring
or an independently controlled browser. No product files were changed by the reviewer.
