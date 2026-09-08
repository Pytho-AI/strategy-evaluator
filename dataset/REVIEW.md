# REVIEW.md — how to check this work without reading code

Updated at every gate. A second Claude Code session or a colleague can open this repository and run
one command.

## One command

    make check          # or: cd dataset && python -m gen check --seed 20260908

Prints a single table `gate → PASS/FAIL`: schema load, invariants 01–20, reproducibility diff
against a fresh regeneration. Nothing else on success. `make test` runs the pytest gates per phase.

## Current phase: P7 (base release package)

Files to open and the question to answer while reading:

1. `dataset/DATA_CARD.md` — does it state the contents, limits, model use, fiction notice, license,
   doctrine, and computable extensions without making an unsupported claim?
2. `dataset/review/samples/coa_statement_src_0060.md` — could a J-5 planner brief the course of action
   as written, and do the claim spans below it support the source text?
3. Open three `dataset/review/samples/risk_context_*.md` products and read their risk statements
   against JRAM Figure 11. Does each slot map to the figure?
4. `dataset/injects/batch_2/manifest.json` — does the evidence support closing `req_01`, and are every
   listed strategy, risk, and collection effect caused by this batch?

Gate: `pytest tests/test_p7.py` (1 passed), followed by `make check` (all gates passed).

## Previous phase: P0 (schemas and contract)

Files to open and the question to answer while reading:

1. `dataset/schema/SCHEMA.md` — does every enum cite a document/enclosure/figure, and is every
   computed column defined by a formula you could re-implement?
2. `dataset/doctrine/EXTRACTS.md` — pick five extracts at random and check them against the PDFs
   (`python -m gen.check_extracts` does this mechanically for the text layer); do the figure
   transcriptions (E15, E17, E30, E37, E43, E45c) match the rendered figures?
3. `dataset/eval/jram.py` — read `CONTOUR` against JRAM Fig. 8 (p. B-9): do you agree with the
   reading of the four boundary cells listed in `CONTOUR_BOUNDARY_CELLS`?
4. `dataset/truth/strategies.jsonl` (three RPS rows) — do the `validity.evidence` strings read like
   a planner's justification for each JP 5-0 test?

Decisions made that the prompt did not specify are listed in `PROGRESS.md` with the rejected
alternative.

## Gate output at P0

```
schema  PASS  all rows of 28 tables validate
01      PASS  referential integrity and PK uniqueness
02      PASS  2 spans inside their source text and mention subject/value
03      PASS  every fact instantiated by >= 1 claim; every intelligence-bearing document yields >= 1 claim
04      PASS  no conflicting approved claims overlap in valid time; supersession acyclic
05      PASS  3 (strategy, condition) groups sum to 1
06      PASS  weights and opponent distributions sum to 1
07      PASS  payoffs cover all 6 (strategy, opponent, world) triples exactly once
08      PASS  escalation edges (0) form a DAG
09      PASS  every assumption's (subject, predicate) has >= 1 fact
10      PASS  every computed column reproduces from truth to 1e-9
11      PASS  all 1 products carry the markings and no other marking string
12      PASS  no sentence mixes a likelihood term with a confidence term
13      PASS  no product mixes ICD 203 and JRAM vocabularies
14      PASS  all 0 risk statements match the Fig. 11 slot order and are <= 90 words
15      PASS  every assumption is in the decision matrix; every COA statement lists its assumptions
16      PASS  every strategy carries the five validity entries and a status
17      PASS  every comparison table is followed by the App. F caution sentence
18      PASS  MSR rows carry strategic_value/damage_degree; MR rows carry risk_subset/fig28_row
19      PASS  0 forced-choice assessments all carry posture_rationale
20      PASS  acronyms glossary-only, spelled out at first use, listed at the end
repro   PASS  regeneration with seed 20260908 is byte-identical
```
