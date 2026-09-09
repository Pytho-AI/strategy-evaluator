# Capability matrix — submitted claims against what exists

Every submitted claim, what actually implements it, the test that proves it, the work still
missing, and what the demo will show. Twelve rows. **All twelve carry non-empty missing work.**
No row is closed.

Source: `/tmp/precheck/D_capability_matrix.md` (Phase -1 part D), with the UI evidence from
`/tmp/precheck/ui/B_ui_artifact.md` and the repository audit from `/tmp/precheck/C_existing_apps.md`.

---

## 1. Submitted materials found

No standalone project plan, pitch deck or portal-submission file exists on disk. `~/Downloads`
and `~/Dev/pytho` were scanned to depth 3 for `.md .txt .pdf .pptx .docx .html`, newest first,
plus a content grep of every `.pptx`/`.docx` modified in the last 30 days for `Stratistics` and
`Strategy Option Evaluation` — zero hits. The most recent Pytho deck,
`/Users/akshay/Downloads/diana/Pytho_DIANA_Deck.pptx` (2026-09-07), is an unrelated NATO DIANA
deck and contains neither string.

The submitted claims exist as text in the team's Slack archive, plus the UI artifact.

### 1.1 Sponsor use-case text

`/Users/akshay/Downloads/slack-archive/slack/intel/2026-09.md` — posted 2026-09-03 by Mike Mearn
("Use cases for the J2 Hackathon in DC next week"). The team selected Use Case 9 on 2026-09-04
(Will Coffin: "Yes, I say we go with Use Case 9: Strategy Option Evaluation Support."). Verbatim:

> **Use Case 9 — Strategy Option Evaluation Support.**
> *Description*: A capability to compare alternative strategies by organizing assumptions,
> evaluating options, and assessing likely outcomes.
> *Requirement*: Seeking a decision-support environment with scenario development, assumption
> tracking, option comparison, sensitivity analysis, and explainable recommendations.

> **Use Case 4 — Automated Foundational Data Ingestion.**
> *Description*: A capability to support creation, update, and maintenance of foundational
> intelligence content by integrating data from multiple sources, identifying changes, and
> assisting analysts in producing standardized reference products.
> *Requirement*: Industry is requested to provide a solution that supports data fusion, entity
> resolution, change detection, structured knowledge management, AI-assisted drafting, and
> quality control for foundational intelligence production. The capability should emphasize
> provenance, update tracking, and interoperability with authoritative data stores.

> **Use Case 6 — Predictive Interconnected Risk Engine.**
> *Description*: AI-driven analytical capability that leverages open and classified sources to
> generate trend analysis, enabling predictive assessments of crisis escalation likelihood,
> employing modeling techniques to identify problem set interrelationships and demonstrate
> horizontal escalation pathways and cascading effects between interconnected crises. The
> platform must provide interactive multi-tier visualization with collaborative multi-user
> editing capabilities, maintain standardized data structures, and integrate into existing tool
> architectures through standard APIs or modular components.
> *Requirement*: Industry is requested to provide a scalable warning and monitoring solution with
> multi-source ingestion, anomaly detection, rule-based and AI-assisted alerting, confidence
> scoring, visualization, and collaborative case management. The capability must support source
> traceability, configurable thresholds, and human validation before dissemination.

> **Use Case 7 — Collection Management Workflow Automation Agent.**
> *Description*: A workflow assistant that reduces manual burden on collection managers by
> automating routine tasks such as requirement intake, tagging, routing, status tracking, and
> preparation of drafts or summaries.
> *Requirement*: Industry is requested to provide an agent-assisted workflow capability that
> supports task orchestration, document and message triage, metadata extraction, recommendation
> of routing actions, status monitoring, and user-approved drafting.

### 1.2 Product summary — the source of the contested claims

`/Users/akshay/Downloads/slack-archive/slack/dm-will-coffin/2026-09.md`, 2026-09-08 14:21 PDT,
Will Coffin. The name `stratistics` was proposed by Akshay Mittal at 13:15 in the same thread.
Verbatim, in full:

> Stratistics gives Joint Staff and Combatant Command planners a single hub to wargame a strategy
> against adversary courses of action, the operational environment, and risk. It is grounded in
> JP 5-0 and Army-published adversary models. Following the Joint Planning Process, Stratistics
> organizes a planning cell's assumptions, constraints, and restraints as tracked objects, each
> with a source, a validity window, and a confidence score. Assumptions stop being a slide in the
> mission analysis brief and become living inputs that expire, update, and flag themselves when
> the strategic guidance or the intelligence estimate changes.
>
> Every course of action then runs through Monte Carlo wargaming, thousands of iterations varying
> each assumption within its confidence bounds, against most-likely and most-dangerous adversary
> COAs. The interconnected risk engine evaluates the three governing risks (to mission, to force,
> and of escalation) and shows how they propagate across the joint operating environment: which
> assumption, if wrong, moves which risk, at which phase, and by how much. It proposes
> mitigations and scores them the same way. Where the plan rests on weak or stale evidence,
> Stratistics identifies the gap, drafts it as a CCIR-aligned collection requirement, and routes
> it to the J2, so the planning cell and the collection management board are working from the
> same picture.
>
> The output is a weighted COA comparison, a sensitivity analysis showing how robust the
> recommendation is to shifting priorities and adversary behavior, and an explainable
> recommendation the Commander can defend to the Secretary and the Chairman. Every option is
> ranked, with exactly why it ranks where it does.

### 1.3 UI artifact

`/Users/akshay/Downloads/Stratistics Wargaming System.html`, SHA-256
`0d8e9e477aaac8213d0987f52c82468fa2753fa2b377c6aa743e5dd51c1aebed`, 1,118,147 bytes. Decoded
read-only: 38 resources (a nested `jipoeMap` HTML page, `docreader.js`, React 18.3.1 + ReactDOM
UMD, a 69 KB dc-runtime bundle, a 300-byte design-system no-op, 31 WOFF2 fonts, d3, topojson, a
world-atlas TopoJSON), plus a 190,759-byte `__bundler/template`.

### 1.4 Not found

No pitch deck, no portal submission export, no written project plan, no API contract document,
no UI source repository.

---

## 2. Citations found in the UI

All publication-like strings live in one `doctrine: [...]` array rendered on the Doctrine screen.
Each carries a `used:` field naming what the artifact claims it backs.

| # | `ref` verbatim | `title` | `used` — the artifact's own claim | Real or fictional |
|---|---|---|---|---|
| 1 | `CJCSI 3100.01F · 29 Jan 2024` | Joint Strategic Planning System | Plan type selector, CCMD selection, GFM inputs | Real |
| 2 | `JP 5-0 · Joint Planning` | Joint Planning Process | Five-step lifecycle, COA screening tags | Real |
| 3 | `CJCSM 3105.01 · JRAM` | Joint Risk Analysis Methodology | Risk scale, decision matrix | Real |
| 4 | `JP 2-01.3 · JIPOE` | Intelligence Preparation of the Operational Environment | JIPOE panel, red-cell reactions in the ARC table | Real |
| 5 | `USEUCOM OPORD 26-002 · 25 MAR 2026` | Operation ENDURING PHOENIX | Strategy under adjudication, assumptions, constraints, force posture | **Fictional** |
| 6 | `JP 2-0 · Joint Intelligence` | Collection management | Collection Management, RFI routing | Real |

Elsewhere in the artifact: `JSCP (CJCSI 3110.01)`, `2022 National Defense Strategy`,
`2022 National Military Strategy`, `Contingency Planning Guidance` (all real, as guidance-set
labels); `UNSCR 2781 (2026)` / `UNSCR 2781 (S/2026/041)`, `CJCS WARNORD 26-001` with paragraph
citations `para 3.B.5` / `4.B`, and `USEUCOM OPORD 26-002 — OPERATION ENDURING PHOENIX.docx` with
paragraph citations `OPORD 1.g.2` … `1.g.7` (**all fictional**). One code comment in
`docreader.js` reads `// Lightweight structure extraction from plan text (JP 5-0 paragraph
headings).` above `extractPlan()`.

### 2.1 No Army adversary publication is cited anywhere

Searched the raw HTML and every decoded resource — template, `jipoeMap`, `docreader`, page bundle
— for `TC 7-100`, `ATP 7-100`, `7-100`, `FM `, `ADP`, `ADRP`, `ATP `, `TC `, `AR `, `OPFOR`,
`threat tactics`, `DATE`, `Decisive Action Training Environment`, `TRADOC`, `ODIN`,
`Worldwide Equipment Guide`, `WEG`, `SMARTbook`.

**Zero hits.** (`WEG` and `ODIN` matched only as case-insensitive substrings inside base64
payloads, not text.) `OPFOR` appears once and not as a citation: it is the fictional adversary's
own name inside a PIR string, "Will the OPA launch a renewed offensive into southern Khorathidin
before D-Day (MDCOA)?".

The same search across `coa-engine`, `pytho-arena`, `pytho-vite` and this repository returns zero
hits for `7-100` in any form, and exactly three `OPFOR` hits, all labels rather than models:
`coa-engine/agent.py:315` (a comment stating OPFOR doctrine is **not** encoded),
`coa-engine/tests/test_side_assignment.py:65` (a force name in a fixture), and
`coa-engine/tests/test_agent_doctrinal_integration.py:108` (a test asserting the adversary player
*skips* doctrinal branching). The nearest thing in the UI is the free-text phrase
`"DIA-model adversary"` inside `THREATS.OLV.desc` — an unsourced assertion, and DIA is not the
Army.

### 2.2 Citation quality gaps

- Entries 2, 3, 4 and 6 carry **no edition, date, page or section**. Only entry 1 is dated. Entry
  3 omits the revision letter (`CJCSM 3105.01`, not `…01C`).
- Entry 5 is fictional scenario content presented in the same list, and the same visual register,
  as the joint publications, with paragraph-level citations. Nothing in the artifact marks it as
  fictional. Real and fictional sources need visibly different treatment before any demo.
- The UI's citations back UI-local content in a different fictional theater (Olvana /
  Khorathidin / Sungzon / North Torbia / Operation ENDURING PHOENIX). They do not back dataset
  results, and Meridian Sea appears nowhere in the artifact.

---

## 3. Capability matrix

| submitted claim | existing implementation | evidence/test | missing work | demo scope |
|---|---|---|---|---|
| **Strategy Option Evaluation** — "compare alternative strategies by organizing assumptions, evaluating options, and assessing likely outcomes"; "scenario development, assumption tracking, option comparison, sensitivity analysis, and explainable recommendations" | Dataset: 3 Blue COAs (`str_blue_1..3`) with the five JP 5-0 validity tests, expected value `V(σ)` under `expected`/`cvar`/`minimax`, `value_ci` (min/max over Red COAs), `robustness = min_θ E_σ'`, per-assumption `sensitivity` and `evpi`, objective weights and App. F 1-3 ratings — all recomputed by `eval/engine.py::recompute` + `eval/validity.py` + `eval/value.py`. UI: the Strategy Option Evaluation screen with COA cards, weighted comparison and a stability sweep — but every number comes from `COA_LIB` constants, not the dataset. | `tests/test_p2.py::test_theater_strategy_gate` (3 valid Blue COAs at T0, T0 ranking `str_blue_1`, ≥2 assumptions with EVPI > 0.001, exactly one `jp50_realistic = false`, 64 worlds); `tests/test_p2.py::test_batch_one_changes_value_ranking_and_acceptability`; `tests/test_evaluator.py::test_objective_ratings_preserve_ties`, `::test_infeasible_strategy_cannot_create_evpi` | Nothing connects the two halves — the UI computes its own numbers. Build the read API and bind the COA screens to `dataset.load()` + `eval/`. The UI's `pSuccess`, casualty p90 and `ci` must **not** be relabelled as dataset `value` / `value_ci`. The explainability trace (claim → assumption → validity/value) exists in neither half. Add the JP 5-0 App. F caution (extract J14b) to the comparison screen. | In scope: full T0 + batches 1-3 comparison, ranking, sensitivity, EVPI, with links to source spans. |
| **Collection Management** — requirement intake, tagging, routing, status tracking, drafting (UC7); "identifies the gap, drafts it as a CCIR-aligned collection requirement, and routes it to the J2" | Dataset: 6 T0 requirements; `priority` = EVPI of the linked assumption, else `(1 − confidence) × dependency degree`; `jipcl_rank`, PIR/EEI context, LTIOV, gap type, status lifecycle, and `req_07` opening on the batch-3 throughput contradiction. UI: Collection Management Agent and RFI screens with `sendWeakToCollection` (drafts from weak assumptions by array position) and a `cycle` handler that increments status. | `tests/test_p4.py::test_collection_and_product_gate` (exactly 6 T0 requirements, top of JIPCL = `req_01`); `tests/test_p5.py::test_inject_manifests_and_demo_beats` (`req_01` in batch-2 `requirements_closed`; `req_07` present); `tests/test_p3.py::test_cyber_forced_choice_moves_energy_without_local_changes` | Draft creation from an explicit strategy question or PIR with stable IDs — an array index is not an identifier. Record required evidence, linked assumption/option, gap reason, proposed owner. Routing as an internal queue assignment. Deduplication of repeat gaps with a recorded review decision. **Satisfaction driven by reviewed accepted evidence rather than by the manifest** (see the new-report row). Reopening on expiry or contradiction. Replace the UI `cycle` handler's "raise confidence to ≥85 on return" rule. | In scope: ranked JIPCL, visible `req_01` closure and `req_07` creation across the three batches. New-report-driven satisfaction is the second flow and is currently unbuilt. |
| **Interconnected / Predictive Risk** — "predictive assessments of crisis escalation likelihood… problem set interrelationships… horizontal escalation pathways and cascading effects"; "which assumption, if wrong, moves which risk, at which phase, and by how much" | Dataset: JRAM problem sets, harmful events, drivers, `risk_assessments` over near/mid/long horizons with `P_raw` from active drivers, noisy-OR cascade over 6 `escalation_edges`, Fig. 6 probability bins, Fig. 23/28 consequence, the Fig. 8 contour, least-squares trend, the ICD 203 roughly-even-chance forced-choice rule with `posture_rationale`, and Fig. 11/5 statement templates (`eval/jram.py`, `eval/engine.py::assess_risk`). UI: the Predictive Risk Engine screen driven by the hard-coded `PROBLEM_SETS` label/hop table and a `compute(..., failIdx)` re-run. | `tests/test_p3.py::test_risk_gate`; `tests/test_p3.py::test_cyber_forced_choice_moves_energy_without_local_changes` (the batch-3 beat: `he_05` forced choice → Significant, the energy problem set moved by a cascade edge alone); `tests/test_evaluator.py::test_high_risk_does_not_cross_game_or_actor` | Replace `PROBLEM_SETS`'s predetermined labels and hop positions with real traversal of `escalation_edges` and recomputed effects. Build the cascade-path explanation. Surface the forced-choice rationale and the four boundary cells in `eval/jram.py::CONTOUR_BOUNDARY_CELLS`. The forced-choice flag is reachable **only** through `load()` — the shipped truth JSONL is `world_version 0` and carries none. The phase-level attribution the summary promises ("at which phase") is not in the dataset: horizons are near/mid/long, not plan phases. | In scope: risk view with problem sets, JRAM levels, trend, drivers, cascade edges and forced-choice rationale for T0 + 3 batches. "At which phase" is out of scope unless rescoped to horizons. |
| **Foundational Data Ingestion — fixture replay** — "provenance, update tracking… change detection" over the shipped corpus | 92 template-rendered documents, 864 claims with exact `span_start`/`span_end`, separate asserted and valid time, reliability A-F, credibility 1-6, ICD 203 likelihood, derived confidence, supersession, proposed-versus-approved status, and 122 resolved entities. `dataset/loader.py` filters sources, claims and facts by batch and recomputes. | `tests/test_p4.py::test_collection_and_product_gate` (invariants `inv02_spans`, `inv03_coverage`, `inv04_valid_time`, `inv11_markings`, `inv12_likelihood_confidence`, `inv13_mixed_scale`); `tests/test_p1.py::test_every_entity_has_two_facts`, `::test_change_events_in_three_clusters`; `tests/test_p7.py::test_loader_and_package`; `tests/test_evaluator.py::test_transaction_time_blocks_future_assertions`, `::test_external_claims_get_derived_confidence` | Expose spans, dates, reliability, credibility, confidence and status through the API and a usable evidence view; keep likelihood and confidence separate on screen. Corpus prose is template-rendered, so extraction difficulty here does not generalize. | In scope and the strongest part of the demo. Label it replay of a fixture, not ingestion. |
| **Foundational Data Ingestion — new-report processing** — "data fusion, entity resolution, change detection… AI-assisted drafting, quality control"; "Assumptions… expire, update, and flag themselves when the strategic guidance or the intelligence estimate changes" | **Nothing that processes an unseen document.** `eval/baseline.py` loops over gold claims and slices the text with the gold `span_start`/`span_end` — it reads ground truth to produce its predictions and cannot be pointed at a new document. `eval/run_llm_baseline.py` was never run (`ANTHROPIC_API_KEY` unavailable). The UI's `docreader` (`readDocument`, `signalIndex`, `extractPlan`) parses uploads into local state and regex-greps JP 5-0 headings, with no character offsets and no persistence; the manual `ingest:` handler stores title and type, assigns a PIR by `1 + (s.intel.length % 3)`, and discards the report body. `loader.py::_apply_closed_requirements` closes requirements from the manifest answer key. | No test proves any of this. `tests/test_p6.py::test_scoring_truth_and_baseline` proves only that scoring truth against itself is 1.0 and that the surface proxy is far lower (extraction F1 0.008210, style compliance 0.000000) — a scorer test, not an extractor test. | **The largest gap.** Build: preserve original text and its hash; extract proposed claims with exact spans and separate asserted/valid times; resolve entities; show missing or uncertain fields for review; accept or reject into a product-owned versioned graph stored outside the frozen dataset; recompute with the same reference functions; no duplicate claims on re-ingest; audit history preserved across refresh. The path must be provably unable to read gold claims, answer keys or manifest `expected_effects`. Acceptance requires a report authored after the fixture with its value and date varied in a test. State which parser or model actually ran and keep it out of the offline path. | **Out of scope for the base offline demo unless built.** If it is not finished, the demo is *partial* and must say so. |
| **Tracked assumptions** — "tracked objects, each with a source, a validity window, and a confidence score"; "expire, update, and flag themselves" | Real and computed. `assumptions` carries `statement`, `subject_id`, `predicate`, `tolerance`, `role`, `origin`, `index_k`, `in_decision_matrix`, the three JP 5-0 tests `jp50_logical` / `jp50_realistic` / `jp50_essential`, and computed `p_holds`, `status` (holds / violated / stale / unknown), `sensitivity`, `evpi`. Source, validity window and confidence are **inherited from the grounding claim** via `eval/value.py::assumption_state`; `stale` fires when the window has expired or the claim's confidence is low. | `tests/test_p2.py::test_theater_strategy_gate` (one `jp50_realistic = false`, EVPI spread); `tests/test_p5.py::test_inject_manifests_and_demo_beats` (k2 unknown → holds at batch 2); `tests/test_evaluator.py::test_shared_assumption_index_requires_identical_proposition`; `tests/test_p4.py` invariant `inv15_decision_matrix` | Surface the source span, valid window and confidence **on the assumption**, and keep the assumption visibly distinct from its grounding claim — an assumption is a planning predicate over claims, not a claim. Add product-owned review state (proposed/approved/rejected, reviewer, time, reason) and change links: the frozen schema has no `source_id`, `review_status`, `reviewed_by` or `change_link` column on the assumption itself. Wire the "flags itself when guidance changes" behaviour — guidance changes are not currently linked to assumptions. | In scope: assumption status, sensitivity, EVPI and expiry across the three batches, each traced to its claim and span. |
| **Tracked constraints** — "organizes a planning cell's… constraints… as tracked objects, each with a source, a validity window, and a confidence score" | `strategies.constraints` is a plain `list[str]` per COA (e.g. `["Maintain combined patrols with Ilmara", "Keep Lantern Battery at Port Auberon"]`), cited to JP 5-0 Ch. III §(7)(a). Not computed, not versioned, not linked to any claim. The UI displays constraint text from its own scenario data. | None. No test asserts anything about constraints beyond schema load. The doctrinal definition is verified verbatim (`EXTRACTS.md` J07a, JP 5-0 Ch. III §(7)(a), p. III-18) by `tests/test_p0.py::test_extracts_verbatim`. | **The "source, validity window, confidence score" claim is false as shipped.** Add product-owned sidecar records keyed to stable IDs (`strategy_id` + ordinal, or a new constraint ID) carrying source id and exact span, `valid_from`/`valid_to`, confidence where supported, review status and change links. Do not modify the published dataset and do not invent provenance for the existing strings. Show them on the strategy comparison screen with honest empty-provenance states. | In scope only as sidecar records with visible empty provenance for the shipped strings. |
| **Tracked restraints** — same claim | `strategies.restraints` is a plain `list[str]` (e.g. `["No strikes on Varenian territory before strait closure", "No forces into Sondria"]`), cited to JP 5-0 Ch. III §(7)(b). Same limits as constraints. | None, beyond `tests/test_p0.py::test_extracts_verbatim` for the definition (`EXTRACTS.md` J07b, p. III-18). | The same sidecar work as constraints, kept as a **separate planning object** ("cannot do" versus "must do"), never merged into one list. | Same as constraints. |
| **Adversary COAs** — "against most-likely and most-dangerous adversary COAs" | Dataset: three fictional Red COAs — `str_red_ml` "Coercive pressure" (most likely, 0.55), `str_red_md` "Strait seizure" (most dangerous, 0.25), `str_red_alt` "Energy coercion" (alternative, 0.20) — as a fixed mixture in `opponent_models.om_blue`, with full payoff coverage against every Blue COA. `value_ci` is the min/max of expected value across them. UI: a separate `SCENARIOS` triple (MLCOA / MDCOA / opportunistic) with an `ag` aggression scalar, and a JIPOE map overlay drawing "solid axis = most likely COA · dashed = most dangerous". | `tests/test_p2.py::test_theater_strategy_gate` via `validate.inv07_payoff_coverage` (all 600 (strategy, opponent, world) triples covered exactly once); `tests/test_evaluator.py::test_opponent_distribution_cannot_repeat_a_strategy`; `EXTRACTS.md` J22 (JP 5-0 Ch. III §(2)(a), p. III-32) verified verbatim | The Red COAs are **team-authored fiction with no external provenance**. Label them that way everywhere. Label `value_ci` as an adversary-scenario range, never a confidence interval. Do not merge the UI's OPA/Khorathidin adversary with the dataset's Varenia — add Meridian Sea as a distinct scenario. Red does not react to Blue: the mixture is fixed at 0.55/0.25/0.20 and does not update between batches. | In scope: the three Red COAs shown as a labelled fixed mixture with the adversary-scenario range. Adaptive Red is out of scope. |
| **Dynamic wargaming against adversary COAs and the operational environment** — "wargame a strategy against adversary courses of action, the operational environment, and risk"; "Monte Carlo wargaming, thousands of iterations varying each assumption within its confidence bounds" | **Not implemented as wargaming.** Dataset: a finite Bayesian game — 64 enumerated Blue worlds (2^6 assumption bits) × 3 Red COAs, evaluated in closed form, no turns, no state transitions, no adjudication (`DATA_CARD.md`: "does not simulate transition dynamics beyond the payoff tensor"). UI: `runSim()` animates a 120 ms `setInterval` progress bar with four canned status strings ("Initializing red cell from JIPOE…", "Sampling adversary reactions…", …) and then calls `compute()`, which draws N Gaussian samples around per-COA authored constants `s`/`cas`/`esc` from `COA_LIB` with a seeded PRNG, a single scalar `ag`, and a `failIdx` knock-down of −0.14 success. That is noise around hand-set numbers. Other repositories: `pytho-arena`'s `BatchedScenarioEnv` is a real tick-based simulator but its scenario schema is tactical counter-UAS geometry (metres, platform speeds, sensor ranges, detection probabilities) that the dataset does not contain; `coa-engine`'s `WargameMCTS` is a real wargame but its transitions come from an LLM and it needs Bedrock or Ollama credentials. **Neither is used.** | `tests/test_p2.py::test_theater_strategy_gate` proves the **finite** world enumeration (all 64 six-bit worlds present) — which is evidence *against* the dynamic-wargaming reading. No test anywhere proves transition simulation. | Either (a) drop "Monte Carlo wargaming, thousands of iterations" and "wargame" from the submitted summary and the deck and describe the finite Bayesian evaluation accurately, or (b) connect a real simulator, which needs a documented scenario mapping, opponent-model provenance, run configuration and test evidence — a scope change, not a wiring change. Do not substitute dataset playback for simulation, and do not present the UI's animated `runSim()` progress bar as a simulation run. | **Out of scope.** The demo shows finite-world decision support. This claim must be corrected or recorded as an explicit unresolved gap; the demo is partial while it stands. |
| **Grounding in JP 5-0** | Implemented and cited. `dataset/doctrine/EXTRACTS.md` §D holds 23 verbatim JP 5-0 extracts with chapter, paragraph and page: J02 logical/realistic/essential (Ch. III §(6)(b), p. III-17) → the three `assumptions.jp50_*` columns; J07a/J07b constraint and restraint (Ch. III §(7)(a)/(b), p. III-18) → `strategies.constraints`/`.restraints`; J13a-e the five validity tests (Ch. III §(q)1-5, pp. III-41-42) → `eval/validity.py` and `strategies.status`; J14a-c App. F (§1, §2.b, p. F-1) → the 1-3 `rating_1_to_3` rule and the required caution; J08, J17, J19a-c, J22. `SCHEMA.md` §1 states each formula. UI: a bare `JP 5-0 · Joint Planning` card backing "Five-step lifecycle, COA screening tags". | `tests/test_p0.py::test_extracts_verbatim` (every quotation checked against the PDF text layer via `gen/check_extracts.py`); `tests/test_p0.py::test_every_enum_cites_a_source_and_appears_in_schema_md`; `tests/test_p4.py` invariants `inv16_validity_entries` and `inv17_caution`; `dataset/doctrine/SOURCES.sha256` pins the PDF digests | Show the five validity tests, the exact failing gate for an invalid COA, and the App. F caution in the product UI. Add the edition and page to the UI's bare `JP 5-0 · Joint Planning` citation. Note the logged conflict: JP 5-0 Fig. III-8's likelihood wording is superseded by the JRAM scale for this dataset (`EXTRACTS.md` note at J11). | In scope. This is the claim with the best evidence — lead with it. |
| **Army-published adversary models** | **None.** No Army publication is named in the submitted text, the UI (§2.1: zero hits for `TC 7-100`, `ATP 7-100`, `FM`, `ADP`, `ADRP`, `OPFOR` as a citation, `DATE`, `TRADOC`, `ODIN`, SMARTbook), the dataset's `DATA_CARD.md` "Doctrinal basis", `dataset/doctrine/README.md`, `EXTRACTS.md`, `SOURCES.sha256`, or the repository-root `doctrine/` directory. All five doctrine PDFs in hand are joint publications: `18-F-1152_JP_5-0.pdf`, `CJCSI_3100_01F.pdf`, `CJCSM_3105_01C.pdf`, `JP2_01.pdf`, `JP_3-60.pdf`. The three Red COAs and their 0.55/0.25/0.20 mixture are team-authored fiction. | None exists. `tests/test_p0.py::test_extracts_verbatim` covers only the five joint documents in `SOURCES.sha256`. | **Unresolved source gap.** Per publication: publication *not identified*, edition *not identified*, page or section *not identified*, implemented rule or parameter *none*. Either name a specific publication, edition and section and point at the parameter it sets, or remove the claim from the summary, the deck and the portal text. Do not present fictional Red COAs or the payoff tensor as evidence of this grounding. | **Out of scope and must be stated as an unresolved gap in the final report.** |

### 3.1 Per-publication resolution for the Army-model claim

The claim under test: *"It is grounded in JP 5-0 and Army-published adversary models."*

| Publication claimed | Edition | Page / section | Implemented rule or parameter |
|---|---|---|---|
| **not identified** | not identified | not identified | **none** |

Adjacent Army references exist in the team's *other* work — `ATP 7-100.3` in the pytho-vite RAG
chat logs, `TC 7-100.2` and OPFOR SMARTbook task graphs discussed in
`slack/marine-corps-warfighting-lab/2026-04.md` and `slack/ndu/2026-07.md`. None of it is wired
into this dataset, this UI, or this product. Do not cite it here.

### 3.2 Rows with no missing work

None.

---

## 4. Modeling limits

These bound every number the product can honestly show.

1. **Finite worlds.** The Meridian game is 2^6 = 64 enumerated Blue worlds over six assumption
   bits, times three Red COAs, times six periods of authored payoff. Values, sensitivities, EVPI
   and robustness are exact sums over that finite set — not estimates from sampling and not
   predictions of real outcomes. Label them scenario-relative decision-support outputs.
   `value_ci` is the min/max across the three Red COAs (an adversary-scenario range), never a
   statistical confidence interval, and dataset utility is not probability of success.

2. **No transition simulation.** There is no state-transition model, no turn adjudication, no
   reactive Red. `DATA_CARD.md` says so directly. The Red mixture is fixed at 0.55/0.25/0.20 and
   does not change across batches. The UI's `runSim()` timer plus `compute()` Gaussian draws
   around `COA_LIB` constants is not a simulation and must not be displayed as one.

3. **Template prose.** All 92 documents were rendered by deterministic templates with seed
   20260908 and no language model, and every span was placed by the generator. Extraction
   difficulty on this corpus does not generalize. The only measured baseline is a literal-surface
   proxy that reads gold spans (extraction F1 0.008210, style compliance 0.000000), and no live
   LLM baseline has been established. Report measured extraction accuracy separately from
   deterministic scoring parity.

4. **Fixture-closing of requirements.** `loader.py::_apply_closed_requirements` closes exactly
   the `req_id`s named in each manifest's `expected_effects.requirements_closed`, and fills
   `answered_by_source_id` from the first approved claim in that batch matching the requirement's
   `(subject_id, predicate)` — if none exists, the requirement is left open with no error. This
   is correct for labelled replay and is *not* evidence that the product can decide whether an
   independently ingested report satisfies a requirement. The new-report path must be blocked
   from reading manifests, answer keys and gold claims, and must be proven so by a test.

5. **Sidecar records are required for constraint and restraint provenance.** The frozen schema
   stores them as bare strings with no IDs, spans, windows, confidence, review state or change
   links. Product-owned sidecar records keyed to stable IDs are the only allowed fix; the
   published dataset is not edited and provenance is not invented. Assumptions are better off —
   source, window and confidence come through the grounding claim — but they still lack review
   state and change links, which also belong in sidecars.

6. **The forced-choice flag is invisible in the truth files.** `truth/risk_assessments.jsonl`
   holds 27 rows at `world_version 0` with zero forced-choice rows, so invariant 19 ("0
   forced-choice assessments all carry posture_rationale") is vacuously satisfied, and
   `ExpectedEffects.RiskAssessmentChanged` has no field to express the post-inject state. The
   rule does fire — 6 of 27 rows at `through_batch=3`, `he_05` and `he_06` on all three horizons
   — but only in the recomputed state returned by `load()`. A product reading the JSONL directly
   would show `forced_choice_applied = false` everywhere.

7. **Two extension tables ship empty.** `extensions/authority/truth/decision_log.jsonl` and
   `extensions/collection_assets/truth/tasking_plan.jsonl` are 0-byte files that load as empty
   DataFrames at every batch, while `USE_CASE_MATRIX.md` marks both their use cases `shipped` and
   both extension gates print PASS. The gates do not require rows.

8. **Two unreconciled edition claims** in the dataset's own doctrinal basis. Recorded, not
   resolved — do not guess which is right:

   | Document | `DATA_CARD.md` says | `doctrine/README.md` + `EXTRACTS.md` say | PDF on disk |
   |---|---|---|---|
   | CJCSM 3105.01C (JRAM) | 14 February 2025 | 10 July 2026 | `CJCSM 3105.01C … (10JUL2026).pdf` |
   | JP 2-01 | 5 July 2017 | 5 January 2012 | `JP2_01_120105.pdf` |

   The extracts were verified against the PDFs in hand, so `EXTRACTS.md` is the version the code
   reads. Reconcile before either date is repeated in a deck or a submission.
