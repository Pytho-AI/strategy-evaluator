# PROGRESS.md — phase log

Seed 20260908. T0 = 08 September 2026. Every gate is logged here with its test output summary.
Format: `P<n> <status> <timestamp>` followed by the gate table and decisions.

## Doctrine conflicts and resolutions (doctrine wins; v2 §preamble)

| # | Prompt text | Doctrine | Resolution |
|---|---|---|---|
| D1 | v2 §1A.14 / §3.14: collection plans use columns "PIR, EEI, indicators, SIR, assets to task / resources to request, LTIOV, reporting instructions" | JP 2-01 Fig. III-8 (p. III-20) column headers are "Priority or Other Intelligence Requirements; Indications; Specific Information Sought; Assets to Be Tasked/Resources to Be Required; Place and Time to Report; Remarks" with a "Period Covered: From/To" line; §13.b(2) lists the prompt's content items | Rendered collection plans use the Fig. III-8 headers verbatim; PIR/EEI/requirement id go in the first column, indicators under Indications, SIR under Specific Information Sought, routing under Assets, LTIOV and recipient under Place and Time to Report, gap type/RFI disposition/JIPCL rank under Remarks. Extract I09. |
| D2 | v2 §2.8: probability bins "Fig. 6 bands" | JP 5-0 Fig. III-8 (2020) names its levels very likely / probable / improbable / highly unlikely; CJCSM 3105.01C Fig. 6 (2026) names them Very Likely / Likely / Unlikely / Very Unlikely with ~81-99 / ~51-80 / ~21-50 / ~01-20 percent | The newer JRAM scale governs every risk product and enum (`PLevel`); JP 5-0's older terms are not used. Extract E15, J11. |
| D3 | v2 §3.14 `status` enum includes `closed` | JP 2-01 §13.a tracks "research, validation, submission, and satisfaction" only | `closed` kept as a DATASET terminal state (LTIOV passed or requirement withdrawn) and labelled non-doctrinal in SCHEMA.md and vocab.SOURCE. Extract I05. |
| D4 | v1 §5 "message traffic is all-caps" | v2 §1A.4 acronym rule cannot be checked on all-capital text; DTG, SITREP, NEO, NLT, ORBAT, HA/DR do not appear in any of the five glossaries | Message traffic uses upper-case only on the marking lines; header labels are words ("Date-time group:", "From:", "To:", "Subject:"); products write "situation report", "noncombatant evacuation", "not later than" in words. Style guide `message_traffic.md`, `cjcs_directive.md`. |
| D5 | v2 §2.8: "risk contour (Fig. 8)" as a 4×4 lookup | Fig. 8 is a drawn contour with dashed boundaries, not a table | Encoded as the team's reading of cell centres (`eval/jram.py::CONTOUR`), constrained by the manual's worked examples (E18b–d, Fig. 11 example); four near-boundary cells carry their alternative reading in `CONTOUR_BOUNDARY_CELLS`. Stated in SCHEMA.md §1 and DATA_CARD Fidelity statement. |
| D6 | v2 §3.13 `harmful_events.fig28_row` and "for MR use Fig. 26 and the row of Fig. 28" | Fig. 28's rows have four graduated cells; the consequence level is the cell the assessor lands in, chosen by judgment (Encl. C §6.b(4)) | Added `fig28_cell` (the authored cell) so the MR consequence lookup is as mechanical as the MSR Fig. 23 lookup; the authored input is the judgment, the level is computed from it. Extract E45b. |
| D7 | v2 §2.4 dependency kinds list only claim→claim `supports` | Theory-of-victory chains must reach objectives (v2 §2.2) and JP 5-0 Fig. IV-9 nests effect → objective → end state | `supports` also allowed claim→objective and objective→objective (typed edges validated in `gen/models.py::Dependency`). |
| D8 | v1 §7 "harness scores truth-vs-truth at 1.0" for RPS at P0 | P0 gate text only requires RPS to validate incl. validity tests | `python -m gen check` runs schema load, invariants 1–20 and reproducibility now; the score_extraction truth-vs-truth gate is added to `check` at P6. |

## Decisions not specified by the prompt (with the alternative rejected)

- Repository root is `~/Dev/pytho/claimgraph-dataset/` with `doctrine/` (PDFs, not committed) and `dataset/`; `dataset/doctrine/` holds `EXTRACTS.md`, `README.md` and `SOURCES.sha256` rather than 80 MB of copied PDFs. Rejected: copying PDFs into `dataset/doctrine/` (the JP 5-0 release alone is 65 MB).
- Rendering backend defaults to deterministic templates (`gen/render.py`, no network) because no `ANTHROPIC_API_KEY` is present in this environment and the 20 style invariants are far easier to guarantee mechanically; an LLM backend is kept behind `--llm` with the required (seed, doc_id, prompt_hash) cache. The model used is recorded in DATA_CARD.md.
- `entities.description`, `facts.supersedes_fact_id`, `facts.first_asserted_batch`, `claims.likelihood_surface_term`, `guidance.issuing_role`, `objectives.parent_objective_id`, `objectives.statement`, `actions.mechanism`, `strategies.{main_effort, sequencing, task_org, reserve_policy, mitigates_he_ids, aspiration, adversary_coa_label}`, `policy_rules.periods`, `decision_points.{pir_id, latest_period}`, `harmful_events.{thing_of_value_id, fig28_cell, posture_subject_ids, beneficial_statement, key_actions}`, `risk_drivers.{driver_id, horizons, label}`, `risk_assessments.{forced_choice_applied, dominant_driver_id, active_driver_ids}`, `problem_set_assessments` (table), `pirs.decision_point_ids`, `collection_requirements.{assumption_id, created_at}` were added so that every computed quantity has the inputs it needs in the data rather than in code. Each is documented in SCHEMA.md.
- Payoff utility vectors are ordered by the actor's `objective`-kind objectives sorted by id (stated in SCHEMA.md §1) rather than by `strategy_objectives` row order, so every strategy of an actor shares one basis.
- RPS includes a second Player 1 strategy ("always paper") beside the spec's mixed-uniform policy so that sensitivity and EVPI are exercised (EVPI = 0.009 > 0) and the acceptable test has a failing example (V = −0.0395 < aspiration 0). Player 2's payoffs are zero in both worlds.
- The suitable test considers only the guidance objectives that belong to the strategy's actor (a shared guidance row can state objectives for several actors).

## P0 — schemas, models, extracts, style guides, RPS — PASSED 2026-09-08

Outputs: `schema/*.json` (28 tables + inject manifest), `schema/SCHEMA.md` (generated from the models),
`gen/models.py`, `gen/vocab.py` (every enum with its doctrinal source), `doctrine/EXTRACTS.md`
(168 extracts, 176 quotations verified verbatim against the PDF text layers by
`gen/check_extracts.py`, 13 transcribed from figure images), `gen/styles/*.md` (13 guides),
`gen/styles/acronyms.yml` (529 acronyms from the five glossaries + ICD 203), `eval/{jram,value,
validity,engine,style_check}.py`, `gen/validate.py` (invariants 1–20), RPS in `truth/`.

Gate: `python -m gen check --seed 20260908`

```
schema  PASS  all rows of 28 tables validate
01–20   PASS  (see REVIEW.md for the full table)
repro   PASS  regeneration with seed 20260908 is byte-identical
```

`pytest tests/test_p0.py`: 2 passed (schemas export and load as JSON Schema 2020-12; RPS validates
end-to-end: uniform strategy V = 0, all five validity tests pass, assumption holds with p = 0.97,
EVPI on the 'always paper' strategy = 0.009 > 0, sensitivity −0.35).

## P1 — scenario, scaffold, facts, guidance, PIRs — PASSED 2026-09-08

Outputs: `gen/scenario.md` (theater design: geography graph, actors/units/systems, timeline, guidance
chain, ends, game form, three Blue and three Red COAs, the 3×6 assumption matrix, four problem
sets with risk context paragraphs, nine harmful events with sources/drivers/consequence basis,
the six-edge escalation DAG, PIRs and T0 requirements, inject design with JRAM effects, document
plan), `gen/scenario_data.py` (the same design as data), `gen/scaffold.py`, `gen/facts.py`,
`gen/denylist.txt` + `gen/denylist.py` (now a `gen check` gate).

Gate (`pytest tests/test_p1.py`, 4 passed): denylist grep clean over entity names/aliases/descriptions,
`scenario.md` and rendered documents; every non-role scenario entity has ≥ 2 facts (as subject or
object; organization roles and the two RPS players are structural); change events land in three
clusters (batch 1: 6 at days +14..+18; batch 2: 5 at +38..+42; batch 3: 5 at +60..+64) and every
change pairs adjoining valid-time intervals; scenario.md anchors match the data.

Counts: 122 entities (2 actors, 3 polities, 12 locations, 10 infrastructure, 20 units, 47 sub-units,
12 systems, 9 roles, 4 problem-set entities, 2 RPS players), 448 facts of which 421 are valid at T0,
4 backstory change events, 2 future projections, 16 inject change events, 7 guidance rows, 20
objectives, 5 resources, 28 actions, 4 PIRs.

Contract amendment (pattern only): `entities.entity_id` accepts the typed readable prefixes
`ent_`, `loc_`, `inf_`, `unit_`, `sys_`, `role_` instead of `ent_` alone; schema re-exported.

Full `gen check` at P1: invariant 03 (every fact instantiated by a claim) FAILS as expected until the
corpus is rendered (P2 renders the intelligence documents; P4 the products); every other gate passes.

Ordering decision for P2–P4: theory-of-victory, grounding and driver edges reference claim ids, and
claims come from rendered documents. The pipeline therefore renders the intelligence-bearing
documents (reference entries, situation reports, news, message traffic, tabular, intelligence
assessments) before strategies and risk are built, and renders the products (risk context, risk
assessments, collection plans, COA statements, guidance) after them. Stage order: scaffold, facts,
plan_docs, render_intel, strategies, graph, risk, collection, render_products, rps, injects.

## P2–P7 — base release — PASSED 2026-09-08

| Phase | Focused gate | Result |
|---|---|---|
| P2 | strategies, payoffs, graph, validity | `pytest tests/test_p2.py`: 2 passed |
| P3 | risk inputs, cascade, JRAM statements | `pytest tests/test_p3.py`: 2 passed |
| P4 | corpus, products, perturbations, spans | `pytest tests/test_p4.py`: 2 passed |
| P5 | three inject batches and computed effects | `pytest tests/test_p5.py`: 1 passed |
| P6 | extraction/effects scoring and measured baseline | `pytest tests/test_p6.py`: 1 passed |
| P7 | loader, data card, review pack, deterministic zip | `pytest tests/test_p7.py`: 1 passed |

P7 full gate: `make check` passed schema validation, invariants 01–20, byte-identical regeneration,
and the denylist. Base counts are 92 documents, 864 claims, 442 facts, 122 entities, 9 strategies,
600 payoff rows, 9 harmful events, and 3 inject manifests. The measured baseline is the offline
literal-surface proxy. The live LLM baseline was not run because `ANTHROPIC_API_KEY` was unset.

Temporal fix at the P7 gate: every rendered claim now preserves its fact's `valid_to`. Two redundant
multi-valued relationship facts were removed because the frozen invariant permits one approved value
per `(subject, predicate, valid-time)`; unit `located_at` facts preserve those graph connections.

## P8 — extension layers — PASSED 2026-09-08

Shipped all five required layers plus the optional sixth: 210 RAG questions, 4 target systems,
12 capability areas with four world-version scores each, 4 authority tiers and 24 example decisions,
8 collection assets with a greedy baseline, and 600 multi-INT events with 40 percent of observed
entity IDs withheld. Every extension includes schemas, truth, a licensed README and starter query,
and an eval result where applicable.

Gate: `pytest tests/test_p8.py` (2 passed). Final `make check` passed the 20 base invariants,
byte-identical regeneration of truth, corpus, injects, extensions, review samples, and archive,
the denylist, and all six extension gates.
