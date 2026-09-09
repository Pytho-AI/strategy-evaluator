# Backend — Strategy Option Evaluation workbench (P3)

HTTP API over the frozen `strategy-evaluation-dataset-pytho` dataset in `dataset/`. P0
covered loading, identity, contracts and error states. P1 added the evaluation services:
decision overview, strategy comparison, evidence and claim trace, risk, collection, and the
batch-to-batch diff. P3 adds the product's own state: new-report ingestion, claim review,
the collection workflow, and tracked planning objects — all in a versioned workspace beside
the dataset, never inside it.

## Run

From the repository root, with the project venv:

```bash
make app-run      # uvicorn on http://127.0.0.1:8765
make app-test     # .venv/bin/python -m pytest -q app/tests
```

`make app-run` is `.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8765`.
Set `STRATEGY_DATASET_DIR` to serve a dataset directory other than `dataset/`.

Dependencies: `app/requirements-app.txt` plus the repo's `requirements.txt`.

## Endpoints

| Endpoint | Returns |
|---|---|
| `GET /api/health` | `ok`, dataset identity, `load_ms` for batch 0 |
| `GET /api/meta` | product name, dataset name, marking, identity, batches 0..3 with `as_of` and per-table row counts, world counts |
| `GET /api/injects` | the three inject manifests: `batch`, `as_of`, `docs`, `change_events`, `expected_effects` |
| `GET /api/injects/{batch}/diff` | what batch *n* changed, computed from the batch *n-1* and *n* snapshots: `evidence` (claims added / superseded / contradicted), `assumptions_changed`, `validity_changed`, `strategies_restated`, `ranking_before`/`ranking_after`, `risk_assessments_changed` (with `cascade_paths`), `problem_sets_moved`, `requirements_closed`, `jipcl_changed` |
| `GET /api/snapshot?batch=0..3` | `decision_overview` plus the batch's `strategies`, `rankings`, `assumptions`, `problem_set_assessments`, `collection_requirements` |
| `GET /api/strategies?batch=0..3` | `caution`, `ranking`, and the three Blue options in full: validity, value, `adversary_range`, robustness, objectives with `expected_contribution`, assumptions, resources, theory of victory, constraints/restraints, harmful events, decision points, opponent model |
| `GET /api/strategies/{id}?batch=0..3` | the same `StrategyDetailView` for one option |
| `GET /api/claims?batch=&entity=&source=&status=&min_confidence=&relationship=&assumption=&harmful_event=&limit=&offset=` | `total`, `limit`, `offset`, and claims with full provenance, exact span text and flags |
| `GET /api/claims/{id}?batch=0..3` | one claim plus its `trace` |
| `GET /api/risks?batch=0..3` | `problem_sets` (risk context + per-horizon level), `harmful_events` (per-horizon assessment, drivers, cascade, sources of risk), `escalation_edges` |
| `GET /api/collection?batch=0..3` | requirements ranked by `jipcl_rank`, each with PIR context, `priority_basis`, `closure_basis`, linked assumption, affected options, candidate assets and routing authority |
| `POST /api/reports` | ingest a text/markdown/CSV/PDF report: stores the original and its sha256, returns proposed claims with exact spans |
| `GET /api/reports` / `GET /api/reports/{id}` | what this workspace has ingested; the detail carries the stored text and every proposed claim |
| `POST /api/claims/proposed/{id}/decision` | accept or reject one proposed claim; answers with everything the acceptance changed |
| `POST /api/collection/drafts` | draft a requirement from a strategy question or PIR plus a linked assumption or gap |
| `POST /api/collection/{req_id}/route` | assign a product requirement to an internal queue (JIOC / JCMB / `<unit> J-2`) |
| `POST /api/collection/{req_id}/status` | set a product requirement's open status (`research`, `validation`, `submission`) |
| `GET /api/planning?batch=&workspace=` | tracked assumptions, constraints and restraints, with `flags` for the objects the latest accepted evidence touches |
| `POST /api/planning/{object_id}/review` | record a review status, source links and validity on a tracked object |
| `GET /api/workspace` | the workspace's counters and its full audit log |
| `POST /api/workspace/reset` | clear one workspace; the dataset and other workspaces are untouched |

Every batch-scoped endpoint also takes `workspace=` (default `demo`).

Batch-scoped endpoints default to `batch=0` and return the same envelope: `batch`,
`as_of`, `marking`, `load_ms`, `response_ms`. An id the loaded batch does not contain
returns 404 `{"error": {"code": "unknown_id", ...}}`; a `batch` outside 0..3 returns 422
`invalid_request`. Response models are pydantic models in `contracts.py`; the OpenAPI
schema is at `/docs` and `/openapi.json`.

## Contract decisions

1. **Scope.** Operator views are the Meridian game (`game_id == "meridian"`). The three
   Blue options (`actor_id == "ent_blue"`) are the options; the Varenia strategies appear
   only as adversary COAs inside `opponent_model.coas`, carrying their
   `adversary_coa_label` (`most_likely` / `most_dangerous` / `alternative`). The RPS game
   is a dataset test fixture and never appears: `/api/strategies/str_rps_p1_uniform` is a
   404. The diff is scoped the same way, and a test asserts no non-Meridian strategy value
   or status ever moves between adjacent batches, so the scoping cannot hide a change.
2. **`adversary_range`.** The dataset's `value_ci` is served as `adversary_range` and
   described as the min/max expected value across the adversary COAs. It is never called a
   confidence interval, and never a casualty estimate.
3. **Every number is computed.** Values, statuses, rankings, sensitivities, EVPI, risk
   levels, ratings and JIPCL ranks come from `dataset.load(...)` (which runs
   `eval.engine.recompute`) or from calling a function in `dataset/eval`:
   `eval.validity.worst_case_cost` for expected resource use, `eval.value.value` with a
   one-hot weight vector for each objective's `expected_contribution`,
   `eval.engine.ranking` for the ranking, `eval.claimset.ClaimSet` /
   `eval.claimset.satisfies` / `eval.claimset.horizon_window` for evidence selection, and
   `eval.style_check.CAUTION` for the App. F caution. No formula is copied and no outcome
   is typed in.
4. **`closure_basis`.** A requirement carries `closure_basis = "manifest_replay"` when its
   status was set by `loader.py` from a batch manifest's `expected_effects` — detected as a
   closed status (`satisfaction` / `closed`) with an `answered_by_source_id`, which nothing
   else in the frozen truth sets. Otherwise it is `null`. P3 adds `"reviewed_evidence"` for
   requirements the product itself closes from accepted evidence.
5. **Forced choice.** Forced-choice rows are read from the loaded frame, never from the
   manifest. `app/tests/backend/test_risks.py` compares every assessment against a direct
   `eval.engine.recompute` call on the same tables.
6. **Marking.** `MARKING = "UNCLASSIFIED — SYNTHETIC"` and `PRODUCT_NAME` live in
   `branding.py` and are the single branding source; `/api/meta` serves both.
7. **Routers.** `create_app` includes the routers in `routes/`; the joins live in
   `views.py` and the indexed batch view in `derive.py`, so no file carries everything.

## decision_overview

`GET /api/snapshot` answers the first screen's three questions from the data:

- **Which valid strategy ranks first?** `recommended` is `ranking[0]`, where `ranking` is
  `eval.engine.ranking(meridian, ent_blue)` — valid strategies only, best value first. An
  invalid strategy cannot appear, so it cannot be recommended. `recommended` carries value,
  `adversary_range`, robustness and the risk functional.
- **Why?** `why.winning_criteria` are the recommended option's objectives (weight, App. F
  `rating_1_to_3`, `contribution` = E[u_k]) where its contribution is at least the
  runner-up's, heaviest weight first; `why.validity_evidence` is the five JP 5-0 tests with
  the evidence string the evaluator wrote. `why.tradeoff` names the runner-up, the
  `value_gap`, and `objectives_favouring_runner_up` — the objectives where the runner-up's
  E[u_k] is higher, ordered by weight × gap. Both lists are empty when the option leads on
  every criterion, which is what the shipped payoffs give at every batch.
- **What could change it?** `highest_sensitivity_assumptions` is the recommended option's
  three assumptions with the largest |sensitivity|, with status, `p_holds` and EVPI.
  `top_collection_requirement` is the open requirement with `jipcl_rank == 1`, carrying
  `priority_basis` (`evpi` with the assumption id, or `fallback` with the current claim's
  confidence and its degree in the dependency graph). `highest_risks` is the five
  harmful-event/horizon rows with the worst JRAM level (ties by `p_raw`), and
  `problem_sets_at_highest_level` the problem-set rows at that same level.

`as_of`, `batch`, `marking` and `caution` (imported from `eval.style_check`) ride along.

## The claim trace

`GET /api/claims/{id}` returns `trace.paths`, each one
`source span → claim → assumption or harmful event → strategy`. Every edge states its
`basis`:

- `dependency_edge` — an edge in the frozen `dependencies` table.
- `current_evidence` — a link derived the way the evaluator selects evidence at this
  batch's `as_of`: an assumption is grounded by the approved claim on its
  (subject, predicate) that is valid at `as_of` (the selection
  `eval.claimset.ClaimSet.current` makes), and a risk driver is driven by the approved
  claims that satisfy its `(op, value)` inside a horizon window (what
  `eval.engine.assess_risk` does).

The frozen dependency edges name T0 claim ids, so inject evidence has no edge there: without
the derived links, `clm_0844`, `clm_0850` and `clm_0856` — the claims that actually move
k0, k2 and k4 — would trace to nothing. `docs/reviews/P1-trace-probes.py` checks every
Blue assumption's selected claim reaches it, at every batch.

`trace.claim_node.status` is `superseded` when a later claim supersedes this one, so a
superseded T0 claim reads as superseded even when it has no outgoing edges.

## Product state

Everything the product itself owns lives in a **workspace**, a SQLite file at
`app/workspace/<workspace_id>/workspace.db` (gitignored; `STRATEGY_WORKSPACE_DIR` moves the
root, which is what the tests do). The default workspace is `demo`. The dataset is never
written to and never read from for product state.

One workspace holds: reports (original text, sha256, format, uploaded_at, actor, the
product source id), proposed claims (with the exact span into the stored text, asserted and
valid times, entity resolution result and review flags), review decisions (actor, time,
decision, reason, revision), accepted claims (versioned), collection requirements
(`preq_0001`..) with their status history, tracked planning object reviews, and an audit log.

Two counters:

- **`graph_version`** increments on every accepted change to the claim set. It is what the
  overlay and its cache are keyed on, and what `/api/workspace` and every overlaid response
  report.
- **`state_version`** increments on every workspace write at all. It is in the cache key too,
  so a new draft requirement or a planning review shows up without waiting for a claim.

`POST /api/workspace/reset` deletes and recreates one workspace directory; it refuses any
path that is not a direct child of the workspace root. State survives a process restart:
`create_app()` reads the same file.

### The overlay rule

Read endpoints (`/api/snapshot`, `/api/strategies`, `/api/claims`, `/api/claims/{id}`,
`/api/risks`, `/api/collection`, `/api/planning`) take `workspace=`. When that workspace has
accepted claims or product requirements, the backend merges them into the batch's tables and
runs the same `eval.engine.recompute(tables, as_of, world_version, claims=merged)` the replay
path runs. Nothing is recomputed by hand.

**`as_of` is the batch's own date, or the latest `asserted_at` among the accepted product
claims when that is later.** The evaluator only selects claims it already knows about
(`ClaimSet.all(known_at=as_of)`), so a report dated after the batch would otherwise be
invisible. Moving the evaluation date forward is what makes new reporting count — and it
moves the JRAM horizon windows with it, so risk numbers can change from the date alone. The
batch's own date is still served, as `batch_as_of`.

An overlaid response carries `overlay_applied: true`, `workspace`, `graph_version`,
`product_claim_ids` and `batch_as_of`; `as_of` is the date the evaluation ran at. **With an
empty workspace none of those keys are present and the body is exactly the replay body** —
`app/tests/backend/test_workspace.py::test_an_empty_workspace_leaves_every_read_response_unchanged`
compares every read endpoint before and after a full ingest/review/reset cycle.

Overlays are cached on `(dataset identity, batch, workspace, graph_version, state_version)`.

## Ingestion

`POST /api/reports?batch=&workspace=` — two body shapes:

```jsonc
// JSON (text, markdown, CSV as `text`; PDF as base64)
{"filename": "cmac_201430Z.md", "actor": "analyst", "text": "FROM: ...", "content_base64": null}
```

```text
// raw upload: POST the file bytes with its own Content-Type and ?filename=
POST /api/reports?filename=brief.pdf   Content-Type: application/pdf   X-Actor: analyst
```

Supported formats: `text` (`.txt`), `markdown` (`.md`), `csv` (`.csv`), `pdf` (`.pdf`, parsed
with pymupdf). Anything else is **415** `unsupported_format` naming what is supported.
`multipart/form-data` is *not* accepted: `python-multipart` is not installed in this venv and
the venv has no pip, so the JSON and raw-body shapes are the two supported paths.

The response states which extractor ran:

```jsonc
{
  "workspace": "demo",
  "report": {"report_id": "rpt_0001", "sha256": "...", "format": "markdown",
             "source_id": "psrc_0001", "report_date": "2026-11-20", "extractor": "local_rules",
             "text_length": 400, "uploaded_at": "...", "actor": "analyst", "filename": "..."},
  "duplicate": false,
  "extractor": "local_rules",
  "proposed_claims": [{"claim_id": "pclm_0001", "status": "proposed",
                       "subject_id": "sys_dorne_asm", "predicate": "range_km", "value": 360,
                       "unit": "km", "valid_from": "2026-11-18", "asserted_at": "2026-11-20",
                       "estimative": false, "likelihood_icd203": null,
                       "confidence_icd203": "moderate", "confidence": 0.8995,
                       "span_start": 114, "span_end": 205, "span_text": "The Dorne-3 ...",
                       "flags": [], "notes": ["..."]}],
  "instruction_like_spans": [{"span_start": 417, "span_end": 487, "text": "Ignore all ..."}],
  "response_ms": 19.0
}
```

**Deduplication.** Re-ingesting the same bytes returns the existing report with
`duplicate: true` and creates no new claims and no new requirements.

**What the extractor does** (`product/extract.py`, pure functions, opens no file):

1. splits sentences and records `[start, end)` offsets into the stored text;
2. resolves entities by canonical name and alias, longest match, case-insensitive, on word
   boundaries. A surface form that resolves to more than one entity leaves `subject_id` null
   and flags `entity_unresolved`. A reporting role (`the theater J-2`) is never chosen as a
   subject while another mention is available — it is the author of the sentence;
3. matches predicates from `gen.vocab.PREDICATES`: number+unit patterns (km and nautical
   miles — the conversion at 1 nm = 1.852 km is stated in `notes`; percent readiness as a
   fraction; transits per day; days of supply; megawatts; brigades; days to mobilize;
   displaced persons; outage hours; counts), the status / alignment / posture / intent /
   cyber-capacity / basing-access vocabularies, and the relational phrases *located at*,
   *operates from*, *operated by*, *subordinate to*, *hosts*, *supplies*, *controls*;
4. reads `asserted_at` from a `DDHHMMZ MON YY` date-time group, else from the report's stated
   date; reads `valid_from` from an `as of DD Month YYYY` cue in the same sentence, else
   assumes the asserted date and flags `valid_from_assumed`; reads `valid_to` from a
   `valid until DD Month YYYY` cue;
5. reads ICD 203 likelihood terms (`gen.vocab.ICD203_TERMS`) and, separately, a confidence
   sentence (`Confidence in this judgment is moderate`). The two are never merged: a sentence
   carrying both is flagged `mixed_likelihood_and_confidence` and its confidence is not read
   (ICD 203 1A.6, dataset invariant 12). A claim with no confidence stated anywhere keeps
   `confidence_icd203: null` and the flag `confidence_missing`;
6. treats instruction-like sentences as data. They are returned in `instruction_like_spans`
   and produce no claim.

Nothing is invented to satisfy the schema. Every field the report does not state stays null
and is named in `flags`, and such a claim cannot be accepted without a reviewer `revision`.

`INGEST_MODEL=<name>` selects a model-backed extractor. This build does not implement one and
answers **501** `extractor_unavailable` rather than silently running the rules extractor under
another name. The offline path imports no model SDK and needs no credentials.

### Measured extraction accuracy

On the four fictional reports in `app/tests/backend/reports_fixture.py`, scored against the
claims they were written to state (`(subject_id, predicate, value)` triples, hand-written in
that file, never read from `dataset/truth`):

```text
tp=9  fp=1  fn=2   precision 0.90   recall 0.82
```

The misses are all in the deliberately loose fourth report: a spelled-out number ("three
hundred and twenty kilometres") is not matched, a non-ICD hedge ("probably") makes the whole
sentence unusable, and the adjectival form "Varenian" does not resolve to `ent_varenia`, so
that sentence's subject came out as the wrong entity — the one false positive. This is an
extraction measurement on four authored documents. **It is not a benchmark, and it is
separate from deterministic scoring parity**, which is exact: every evaluated number in
`test_review.py` is compared against a direct `eval.engine.recompute` call on the same tables.

## Review

`POST /api/claims/proposed/{claim_id}/decision?batch=&workspace=`

```jsonc
{"decision": "accept", "actor": "reviewer", "reason": "corroborated by imagery",
 "revision": {"confidence_icd203": "moderate"}}
```

`revision` is the reviewer's own corrections, applied before acceptance and recorded with the
decision. Only claim fields are accepted: `subject_id`, `predicate`, `object_id`, `value`,
`valid_from`, `valid_to`, `asserted_at`, `estimative`, `likelihood_icd203`,
`confidence_icd203`.

Accepting bumps `graph_version`, re-evaluates, reconciles the collection requirements, and
returns what changed:

```jsonc
{
  "workspace": "demo", "batch": 3, "as_of": "2026-11-20", "graph_version": 1,
  "claim": { ... the accepted claim, status "approved" ... },
  "decision": {"decision_id": "dec_0001", "decision": "accept", "actor": "reviewer",
               "decided_at": "...", "reason": "...", "revision": {}},
  "changes": {"evidence": {"claims_added": [], "claims_superseded": [], "claims_contradicted": []},
              "assumptions_changed": [{"assumption_id": "asm_blue_1_k0", "from": "violated",
                                       "to": "holds", "p_holds_before": 0.1005,
                                       "p_holds_after": 0.8995, "statement": "..."}],
              "validity_changed": [], "strategies_restated": [],
              "ranking_before": ["str_blue_1", "..."], "ranking_after": ["..."],
              "risk_assessments_changed": [], "problem_sets_moved": [],
              "requirements_closed": ["preq_0001"], "jipcl_changed": []},
  "contradicts": ["clm_0844"],
  "contradiction_reason": "accepted claim pclm_0001 reports range_km = 360 ... both remain visible ...",
  "chosen_claim_id": "pclm_0001",
  "requirements_changed": [ ... full RequirementView rows ... ],
  "planning_flags": [{"object_id": "asm_blue_1_k0", "kind": "assumption", "text": "...",
                      "review_status": "unreviewed", "reason": "... grounds this assumption",
                      "claim_ids": ["pclm_0001"], "dependent_options": ["str_blue_1"]}]
}
```

`changes` is computed by the same `views.diff` the inject timeline uses, over the evaluation
before the decision and the evaluation after it.

**Contradictions never overwrite.** When the accepted claim disagrees with an approved
dataset claim over an overlapping valid-time window, both stay `approved` and both stay in
`/api/claims`; each carries the other in `flags.contradicts_claim_ids`; the reason is
recorded on the product claim; and `chosen_claim_id` names the one the evaluator's as-of
selection rule actually made current (latest `asserted_at` whose window contains `as_of`).

Rejecting records the decision and changes no evaluation. A second decision on the same claim
is **409** `already_decided` — decisions are kept, not overwritten. An unknown claim id is
**404**.

## Collection workflow

Dataset requirements `req_01`..`req_07` stay read-only replay rows. Product requirements are
`preq_0001`.. and appear as extra rows in the same `/api/collection` list, ranked by the same
JIPCL rule (they are put through `eval.engine.recompute` with the dataset ones, so their
`priority` and `jipcl_rank` are computed, not assigned). A product row carries
`owner: "product"` and a `product` block; **dataset rows carry neither key**, which is what
keeps the replay response byte-identical.

`POST /api/collection/drafts?batch=&workspace=`

```jsonc
{"actor": "collection manager",
 "strategy_question": "Can str_blue_1 stage from Halden?",   // or "pir_id": "pir_01"
 "assumption_id": "asm_blue_1_k2",                            // or subject_id + predicate
 "gap_type": "missing",                                       // missing|stale|low_confidence|contradiction
 "required_evidence": "a reported grant or refusal of basing access at Halden",
 "gap_reason": "the option's basing assumption has no claim valid at the as-of date",
 "proposed_owner": "the theater JIOC",
 "ltiov": "2026-12-01",
 "sir": "", "indicators": []}
```

A draft needs an explicit strategy question **or** a PIR, plus a linked assumption **or** a
(subject, predicate) gap; missing either is **422** naming the missing fields. `created_at` is
the batch's as-of date, so the requirement is ranked in the batch it was raised against.

**Deduplication.** A draft for a (subject, predicate, gap_type) that is already open returns
the existing requirement with `duplicate_of` set and records a review decision
`duplicate_of` against it. No second row is created.

`POST /api/collection/{req_id}/route` — `{"queue": "JIOC", "actor": "...", "reason": "..."}`.
`queue` is `JIOC`, `JCMB` or `"<unit> J-2"`; anything else is 422. Routing sets the status to
`submission` and records the authority tier that approves a `requirement_submit` from the
`authority` extension (`tier_3`, J-2/J-5 director). **This is an internal queue assignment;
nothing is sent to an external recipient.**

`POST /api/collection/{req_id}/status` — `{"status": "validation", "actor": "...", "reason": "..."}`.
Only the open statuses `research`, `validation`, `submission` can be set by hand. Setting
`satisfaction` or `closed` is **422**: closure comes from evidence, not from a button.

### The satisfaction rule

A product requirement closes (`status: "satisfaction"`, `closure_basis: "reviewed_evidence"`)
only when an **accepted** claim on its (subject, predicate) meets its gap, and is valid at the
evaluation's as-of date:

| `gap_type` | closes when the accepted claim … |
|---|---|
| `missing` | exists and is valid at `as_of` |
| `stale` | is valid at `as_of` |
| `low_confidence` | is valid at `as_of` **and** its `confidence_icd203` is `moderate` or `high` |
| `contradiction` | is valid at `as_of` **and** either the as-of rule makes it current (it supersedes the contradicted value) or its value equals the current approved value (it corroborates) |

A document arriving never closes anything: ingestion produces *proposed* claims, and the
reconciliation only ever looks at accepted ones. The closing claim is recorded as
`product.satisfied_by_claim_id`, its report as `answered_by_source`, and the basis in the
status history.

### Reopening

After every review decision, each satisfied product requirement is re-checked and **reopens**
— back to the status it held before closure, with the reason in its status history — when:

- the satisfying claim expired: its `valid_to` is before the current `as_of` (which a later
  report moves forward), or
- a later accepted claim on the same (subject, predicate) states a different value.

## Tracked planning objects

`GET /api/planning?batch=&workspace=` returns `objects` and `flags` in the usual envelope.

**Assumptions** are seeded from the dataset with their real grounding: `source_links` is the
claim the evaluator selects at `as_of` with its `claim_id`, `source_id`, `span_start`,
`span_end` and exact `span_text`; `validity` is that claim's window; `confidence` is its
`confidence_icd203` and derived numeric confidence; `status` is the assumption state.
`provenance` is `"dataset"`.

**Constraints and restraints** exist in the frozen schema only as strings on `strategies`, so
they get product-owned sidecar records with stable ids (`pcon_<strategy_id>_<n>`,
`pres_<strategy_id>_<n>`), `source_links: []`, `validity: null`, `confidence: null`,
`review_status: "unreviewed"`, and a `provenance` string that says the schema carries no span,
window or confidence for them. **Their provenance is stated as absent, not invented.**

`POST /api/planning/{object_id}/review`

```jsonc
{"review_status": "reviewed",           // unreviewed|reviewed|needs_review|invalidated
 "actor": "the theater J-5", "reason": "confirmed against the OPORD",
 "source_links": [{"claim_id": "clm_0844"}],
 "validity": {"valid_from": "2026-09-08", "valid_to": null}}
```

The review is stored with actor and time, appended to the object's `review.history`, and also
written to the workspace's decision log and audit log.

`flags` lists the objects the latest accepted evidence touches: an assumption whose
(subject, predicate) the accepted claim reports, and any constraint or restraint a reviewer
has linked to that claim. Each flag names its `dependent_options`. An unreviewed sidecar has
no source links, so it is never flagged on a guess.


## For the UI

- Every batch-scoped response has the same envelope: `batch`, `as_of`, `marking`,
  `load_ms`, `response_ms`. Show `marking` (`UNCLASSIFIED — SYNTHETIC`) on every screen and
  in exports.
- Show `caution` (`/api/strategies`, `decision_overview.caution`) under any comparison
  table: it is JP 5-0 App. F's own sentence, invariant 17 of the dataset.
- `adversary_range` is `[min, max]` across adversary COAs — label it "adversary range" or
  "range across adversary COAs", never a confidence interval, probability of success, or
  casualty figure. `value`, `robustness`, `p_holds`, `sensitivity`, `evpi`, `priority` and
  `jipcl_rank` are scenario-relative decision-support outputs, not predictions.
- Keep likelihood and confidence apart: a claim carries `likelihood_icd203` (with the
  surface term as written, `likelihood_surface_term`), `confidence_icd203`, and the derived
  numeric `confidence` whose `confidence_basis` string states what it is. Do not merge
  them into one probability.
- Invalid options are served, ranked nowhere, and name their gate: `status`,
  `gate_failed` (a single test name, e.g. `acceptable`) and `gates_failed`.
- `decision_overview.recommended` is always `ranking[0]` and always valid; `ranking` is the
  same list as the `meridian`/`ent_blue` entry of `snapshot.rankings`.
- Ids are stable dataset ids; display names are resolved for you
  (`subject_name`, `problem_set_name`, `from_name`/`to_name`, `task_org_names`,
  `posture_subject_names`, `thing_of_value_names`, `actor_name`). Do not render raw ids.
- `/api/claims` defaults to `limit=50` (max 1000) and reports `total`; filters are
  `entity`, `source`, `status`, `min_confidence`, `relationship`, `assumption`,
  `harmful_event`. Rows come back ordered by `claim_id`, so paging is stable.
- `claim.span_text` is the exact `[span_start, span_end)` slice of `source.path` — show it
  verbatim with the source title, reliability (A–F), credibility (1–6) and both dates
  (`asserted_at` vs `valid_from`/`valid_to`).
- `claim.flags` gives `proposed`, `contradiction` + `contradicts_claim_ids`, `stale`
  (valid_to before `as_of`), `superseded` + `superseded_by_claim_id`. A contradiction is
  flagged on both claims; the approved one stays `approved`.
- Risk horizons are always ordered `near`, `mid`, `long`. `forced_choice_applied` rows
  always carry `posture_rationale` — show it wherever the JRAM level is shown.
- Collection requirements arrive in `jipcl_rank` order with closed ones (rank `null`) last.
  `affected_strategies` includes every option whose assumption shares the requirement's
  `index_k`, because those rows share the grounding claim.
- The diff endpoint's field names match the manifest's `expected_effects`, plus display
  extras (`name`, `statement`, `cascade_paths`, `new`, `trend_before`, `evidence`).
  `assumptions_changed` uses the manifest's `from` / `to` keys.
- Timings on this laptop: any endpoint cold ≤ ~220 ms; the warm
  snapshot+strategies+claims+risks+collection set ≈ 12 ms.

### The product endpoints

- Pass `workspace=` on every call once the operator starts a product flow, and keep passing
  the same one. `demo` is the default. With an empty workspace the read responses are
  identical to the replay responses, so it is safe to pass it always.
- The overlay keys (`overlay_applied`, `workspace`, `graph_version`, `product_claim_ids`,
  `batch_as_of`) are **absent** when no overlay was applied. Test with
  `"overlay_applied" in body`, not `body.overlay_applied === false`. When they are present,
  show both dates: `as_of` is what the evaluation ran at, `batch_as_of` is the inject batch's
  own date, and the gap between them is the newly reported evidence.
- Ingest with JSON `{filename, actor, text}` for text/markdown/CSV, or `{filename, actor,
  content_base64}` for a PDF; or POST the raw bytes with the file's Content-Type and
  `?filename=`. There is no multipart endpoint. 415 means the format is not supported and
  `error.detail.supported` lists what is.
- Show a proposed claim's `span_text` verbatim next to `span_start`/`span_end` — it is the
  exact slice of the stored report, and `GET /api/reports/{id}` returns that text so the UI
  can highlight in place. Show `flags` and `notes`: they are why the claim still needs a
  reviewer, in the extractor's own words.
- `instruction_like_spans` are sentences that read as instructions. Render them as quoted
  document content, never as an action.
- Accepting a claim with a `confidence_missing` (or any other missing-field) flag returns 422
  with `error.detail.missing`. Prompt the reviewer for exactly those fields and resend them in
  `revision`; do not default them.
- After a decision, `changes` has the same field names as the inject diff, so the same panel
  renders both. `planning_flags[].dependent_options` are strategy ids for the options to
  re-highlight.
- A contradiction is not an error: show both claims, both marked, and say which one
  `chosen_claim_id` names as current.
- Collection: a row with `owner === "product"` has a `product` block (strategy question, gap
  reason, proposed owner, required evidence, authority tier, satisfying claim, status
  history); a row without it is a dataset replay row and its route/status endpoints return
  404. `closure_basis` is `"reviewed_evidence"` for a product closure and `"manifest_replay"`
  for a dataset one.
- Nothing in this API sends a collection request anywhere. Label the route action as an
  internal queue assignment.

## Where numbers come from

`adapter.py` calls `dataset.load(base=True, extensions=[...], through_batch=batch)`, which
runs `dataset/eval/engine.py::recompute` on every call, and converts the returned
DataFrames to plain dicts. `derive.Index` indexes one loaded batch and holds the bridges
into `dataset/eval`; `views.py` turns that into the typed contracts.

The rules this backend keeps:

- No computed column is read from `dataset/truth/*.jsonl`. Values, statuses, rankings,
  sensitivities, EVPI, risk levels, App. F ratings and JIPCL ranks are computed, not
  stored — reading the truth files directly gives the T0 world only. The forced-choice risk
  flag, for instance, is false everywhere in the truth file and true on six rows after
  batch 3.
- No eval formula is copied into the backend or the frontend.
- No expected outcome is typed into product code. The manifests are read by the tests as
  the oracle, never by the app to produce an answer.
- Nothing writes to `dataset/`. `app/tests/backend/test_no_source_writes.py` hashes every
  file under `dataset/` before and after the run.

## Extensions

`snapshot()` loads the `collection_assets` and `authority` extension layers when the
checkout has them, and skips them when it does not, so a dataset without `extensions/`
still serves every endpoint (with `candidate_assets`, `disciplines` and
`routing_authority` empty). `collection_assets` supplies each requirement's candidate
assets and disciplines through `asset_coverage` on (subject, predicate); `authority`
supplies the tier that approves a `requirement_submit`.

## Cache ownership

The cache owns its tables; callers own what they are handed. `BatchSnapshot.tables`,
`.table()`, `.find()` and `.rows_where()` all return deep copies, so a caller that mutates
a response cannot change a later one. `BatchSnapshot.raw` is the uncopied table set: the
adapter's own read-only paths and `derive.Index` read it and never mutate it, which is what
keeps the warm views at a few milliseconds. `app/tests/backend/test_adapter.py` mutates a
returned table and asserts the next read still equals a fresh load; `test_api.py` asserts
the batch-1 response body is unchanged by a mutation attempt.

## Cache key

Batch snapshots — and the `derive.Index` built over them — are cached under
`(dataset identity, batch)`, where dataset identity is

```text
<SHA-256 of dataset/strategy-evaluation-dataset-pytho.zip>:<git HEAD of the dataset checkout>
```

with `no-archive` / `no-git` standing in when either is unavailable. Changing the archive or
the checkout produces a different key, so a stale batch cannot be served. A cold load of
batch 3 takes about 40 ms against a 2 s budget, so caching is a convenience, not a
requirement.

## Error states

Preflight runs before any load and never falls back to mocked data.

| Condition | Status | `error.code` |
|---|---|---|
| `dataset/` missing, or missing `truth/`, `schema/`, `injects/`, or an inject manifest | 503 | `dataset_missing` |
| a schema file is gone, unparseable, has lost a column the API reads, changed its `x-primary-key`, or changed the type/enum/nesting of a field the API reads; or a required table loads empty | 500 | `schema_incompatible` |
| `batch` outside 0..3, or not an integer | 422 | `invalid_request` |
| a strategy, claim or diff id the loaded batch does not contain | 404 | `unknown_id` |
| an unknown report, proposed claim, product requirement or planning object | 404 | `unknown_id` |
| an unsupported report format, or a body with neither `text` nor `content_base64` | 415 | `unsupported_format` |
| a draft with no strategy question/PIR or no gap; an invalid queue, status or gap type; a claim that cannot be accepted as it stands | 422 | `invalid_request` |
| a second decision on an already-decided claim | 409 | `already_decided` |
| `INGEST_MODEL` is set | 501 | `extractor_unavailable` |

Error bodies are `{"error": {"code": ..., "message": ..., "detail": {...}}}`. The 503
message names the directory it looked in and the `STRATEGY_DATASET_DIR` override; the 500
message names the table and the column, key, type or enum that changed; the 404 message
names the id that was asked for.

### Schema preflight

`REQUIRED_SHAPES` in `adapter.py` is the whole contract: per table, the properties the API
reads, the exact set of JSON types each may take once `$ref` and `anyOf` are flattened, the
exact enum value set where the product branches on it, and nested properties where it reads
into a structure. Preflight compares it against `dataset/schema/*.json` and rejects, per
property, a changed type, an added, removed or renamed enum value, and a changed or missing
nested field. P1 declares the tables the new services read — `problem_sets`,
`harmful_events`, `risk_assessments`, `risk_drivers`, `risk_sources`, `escalation_edges`,
`pirs`, `dependencies`, `entities`, `objectives`, `actions`, `resources`,
`strategy_resources`, `policy_rules`, `decision_points`, `opponent_models`, `games` — and
the columns P1 added to `strategies`, `assumptions`, `claims`, `sources`,
`strategy_objectives` and `collection_requirements`. Enums are pinned where the product
branches: strategy/assumption/claim/requirement status, `dependencies.kind` and node types,
`risk_assessments.risk_level` and `jsps_horizon`, `harmful_events.risk_type`,
`assumptions.origin`.

## Files

```text
app/backend/adapter.py         dataset loading, identity, preflight, batch and index cache
app/backend/derive.py          Index: one loaded batch, indexed, with the eval bridges
app/backend/views.py           builders: Index in, typed contracts out
app/backend/branding.py        PRODUCT_NAME and the classification marking
app/backend/contracts.py       typed pydantic responses
app/backend/errors.py          DatasetMissing / SchemaIncompatible / UnknownId
app/backend/main.py            create_app(): error envelope and router wiring
app/backend/routes/            one router per resource, plus the shared batch/workspace parameters
app/backend/product/store.py   the workspace: SQLite, ids, versions, audit log
app/backend/product/extract.py the local rules extractor (pure functions, opens no file)
app/backend/product/ingest.py  format decoding, hashing, deduplication
app/backend/product/overlay.py merged claims -> eval.engine.recompute -> a cached Index
app/backend/product/review.py  accept/reject, contradiction detection, what changed
app/backend/product/collection.py  drafts, routing, status, satisfaction, reopening
app/backend/product/planning.py    seeded planning objects, reviews, affected flags
```

## Tests

`app/tests/backend/`: `test_api.py` (P0 contracts), `test_adapter.py`,
`test_dataset_errors.py`, `test_manifest_beats.py`, `test_no_source_writes.py`,
`test_performance.py`, and the P1 files `test_diff.py`, `test_strategies.py`,
`test_overview.py`, `test_claims.py`, `test_risks.py`, `test_collection.py`.
and the P3 files `test_ingest.py`, `test_review.py`, `test_workflow.py`,
`test_planning.py`, `test_workspace.py`, with the authored fixture reports in
`reports_fixture.py`. `conftest.py` primes `sys.path` through `adapter.eval_module` so a test
can import the reference evaluator directly and use it as an oracle; it also points
`STRATEGY_WORKSPACE_DIR` at a throwaway directory for the run and gives each test its own
workspace, so the tests never touch `app/workspace/`.

Backend suite: 277 tests, ~6 s.

Known limitations, stated plainly:

- The extractor takes at most one claim per sentence, and it matches surface patterns. It has
  no spelled-out numbers, no adjectival entity forms ("Varenian" does not reach `ent_varenia`),
  and no non-ICD hedges. Measured precision 0.90 / recall 0.82 on four authored reports.
- `multipart/form-data` uploads are not supported (no `python-multipart` in this venv, and the
  venv has no pip). JSON and raw-body uploads cover the same ground.
- A model-backed extractor exists only as an interface: `INGEST_MODEL` returns 501.
- A product requirement is only ever satisfied by an accepted *product* claim. Dataset claims
  arriving in a later inject batch close dataset requirements through the manifest replay
  path, which is labelled `manifest_replay` and is not this rule.
- Reopening on contradiction fires on the acceptance that introduces the contradicting claim;
  the requirement can be satisfied again by the next reconciliation if that newer claim also
  meets the gap. That is deliberate — the operator sees the reopen and its reason.
