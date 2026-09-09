# STATE — strategy-evaluation-workbench

Living state file for the Strategy Option Evaluation product build. Updated after every phase
with completed work, exact checks, remaining work, blockers, and current ETA.

- Repository: `/Users/akshay/Dev/pytho/strategy-evaluation-workbench` (renamed 2026-09-09 from
  `claimgraph-dataset`; same git history, branch `dataset`, HEAD `f7cc914`).
- Precheck reports referenced below: `/tmp/precheck/A_dataset_and_repos.md`,
  `/tmp/precheck/ui/B_ui_artifact.md`, `/tmp/precheck/C_existing_apps.md`,
  `/tmp/precheck/D_capability_matrix.md`. Paths inside those reports say `claimgraph-dataset`
  because they were written before the rename; read them as this repository.
- Last updated: 2026-09-09, end of P0 documentation.

---

## 1. Validation precheck

```text
VALIDATION PRECHECK
[PASS] Local instructions read
       11 instruction/guardrail files read across 4 repos plus ~/.claude/CLAUDE.md; no AGENTS.md exists in scope.
[PASS] Existing work recorded and protected
       Every modified/untracked path listed in §4: vite 1 modified + 1 untracked + 3 stashes; coa-engine 2 modified + 1 unpushed commit; arena clean; this repo 1 untracked (HANDOFF_CODEX.md).
[PASS] Dataset commit and archive checksum
       HEAD f7cc9149088200bc655601410cc0de4e793e4457 on branch `dataset`; zip SHA-256 fc5c9d311fd1392d0af367f4522842afa807b29ad60ba41cda446cbbeac54418 — exact match to the expected value.
[PASS] Archive integrity
       `unzip -t dataset/strategy-evaluation-dataset-pytho.zip` exit 0, 288 entries, "No errors detected in compressed data".
[PASS] Dataset checks and tests
       `make check` exit 0, 28/28 gates PASS (schema + invariants 01-20 + repro + denylist + 6 extension gates); `make test` exit 0, 35 passed, 5 warnings in 7.63s.
[PASS] Loader and batch-manifest smoke test — with one recorded exception
       57 assertions ran; 56 passed. All 28 base tables are nonempty at batches 0–3, every adjacent-batch manifest comparison and all 14 demo-beat assertions pass. The one failing assertion was the smoke script's own "every extension table is nonempty" check, which two intentionally empty workflow tables fail (§3.7). The prompt's requirement is that the *required* tables are present and nonempty; those two tables are write logs the dataset ships empty by design, so the gate is recorded PASS with this exception stated, not as an unqualified pass.
[PASS] Supplied UI integrity, resource inventory, and browser baseline
       `Stratistics Wargaming System.html` SHA-256 0d8e9e477aaac8213d0987f52c82468fa2753fa2b377c6aa743e5dd51c1aebed unchanged before and after; all 38 resources decoded as data with per-file hashes; the original rendered in Chrome with all 9 nav entries exercised, zero page-origin console errors, zero outbound requests.
[PASS] Existing UI handlers mapped to the integration contract
       All 10 named handlers located in the decoded logic file and mapped to the four use cases and to the exact numbers they fabricate: buildCoas l.181, compute l.196, ranked l.225, runSim l.185, COA_LIB l.154, PROBLEM_SETS l.121, sendWeakToCollection l.383, cycle l.416, loadDocs l.76, ingest l.411.
[PASS] Selected implementation baseline recorded
       Target repo selected with a green baseline executed in this session (`make check` 28/28, `make test` 35 passed); the three candidate app repos were run and scored, and their pre-existing failures are recorded and excluded (§2.4).
[PASS] Submitted capability matrix and source gaps recorded
       docs/CAPABILITY_MATRIX.md carries all twelve rows with non-empty missing work, the submitted claim text with its Slack source paths, the UI citation audit, and the explicit finding that no Army-published adversary model is identified anywhere.
Target repository: /Users/akshay/Dev/pytho/strategy-evaluation-workbench
Reason: the computed results are a Python package in this repository (dataset.load + dataset/eval), so a service here reaches them by import; no other repository is a clean fit — pytho-vite fails its own typecheck gate and is the wrong language, coa-engine is live production for pytho-vite and pytho-app, pytho-arena is under an explicit user HOLD.
Baseline test commands: make check; make test; (new) app/backend pytest
Baseline result: make check exit 0, 28/28 gates PASS; make test exit 0, 35 passed, 5 warnings in 7.63s; app/backend pytest not yet established (P0).
Estimated completion: 12-18 working hours from the precheck, i.e. P1-P5 complete 2026-09-10 to 2026-09-11, assuming the new-report ingestion flow (P3) is the long pole.
```

---

## 2. Architecture decision

### 2.1 Decision

Build a standalone product in this repository. The repository holds both the frozen dataset and
the product:

| Path | Contents | Owner |
|---|---|---|
| `dataset/` | The frozen `strategy-evaluation-dataset-pytho` release: schemas, truth, corpus, injects, eval, extensions, generator, archive | Frozen contract — read only |
| `app/backend` | FastAPI + uvicorn + pydantic v2 on Python 3.12, importing `dataset.load` and `dataset/eval` directly | Product |
| `app/ui` | The recovered Stratistics UI, served as static files | Product |
| `docs/` | This file, the capability matrix, the demo script | Product |

Stack: Python 3.12, FastAPI, uvicorn, pydantic v2, pandas (already present for the dataset).
The UI is static — dc-runtime compiles its template at load, so there is no frontend build step.
No LLM, no AWS, no containers, no network for the base demo.

### 2.2 Boundary

- The backend owns loading, filtering, recomputation, joins and trace construction. It calls
  `dataset.load(...)` and the functions in `dataset/eval/` and never re-implements a formula.
- The frontend renders typed API responses. No dataset formula is copied into JavaScript.
- `dataset/schema/*.json` are the API contracts. Stable dataset IDs are the identifiers.
- Product-owned state (review decisions, ingested reports, sidecar records for constraints and
  restraints) is stored outside `dataset/`. Nothing in `dataset/` is written by the product.

### 2.3 Why standalone — the user's decision, with the evidence

The user decided this is a standalone hackathon effort. Report C's independent audit reaches the
same conclusion, and its evidence is recorded here so the decision is auditable:

| Candidate | Verdict | Evidence |
|---|---|---|
| `pytho-vite` | Excluded | `npm run typecheck` fails with 9 NEW TypeScript errors above a tolerated ratchet of 726; `npm run test` 1 failed / 335 passed (`src/data/personas.test.ts:32`). It is TypeScript on SST/Lambda, so it cannot host the Python evaluators without adding the very service this repo would be. It also has no guardrails kit and a documented `.env.dev` deploy hazard. |
| `coa-engine` | Excluded as a host | Baseline green (1516 passed, 11 skipped in 83.30s), but `http_server.py` is live production: pytho-vite's planning pages call its `/api/runs/*` and pytho-app attaches to its `coa-engine_default` docker network. Recorded as a standing user decision in `pytho-arena/docs/STATE.md` (2026-09-03): the planning product "is LIVE for pytho-vite and pytho-app and must not be touched". |
| `pytho-arena` | Excluded as a host | `docs/STATE.md` records `HOLD ACTIVE`, "NOTHING STARTS WITHOUT A NEW USER INSTRUCTION", 61 queued work items W01-W61 not started. It also carries a pre-existing failing test (`test_golden_rollout.py::test_scripted_rollout_reproduces_golden_fixture_exactly`, sha256 mismatch, fails on origin/main too) and an open unauthenticated-replay finding (W04). Its `server/app.py` is the right structural pattern and is read as a reference only. |
| `pytho-app` | Not applicable | COA storage and workflow CRUD only (`app/app/routers/api/seminars.py:224-244`). Nothing computes, scores, ranks or wargames. |

### 2.4 What is excluded and why

- **The four other repositories are not modified and not reused.** Their simulators are recorded
  as **not used**: `pytho-arena`'s `BatchedScenarioEnv` (a real tick-based tensor simulator, but
  its scenario schema is tactical counter-UAS geometry — metre-scale world, platform speeds,
  sensor ranges, detection probabilities — none of which the dataset contains; mapping Meridian
  Sea onto it means inventing parameters) and `coa-engine`'s `WargameMCTS` /
  `WargameEnvironment` (a real LLM-in-the-loop wargame at the right altitude, but its
  transitions come from a model, it needs Bedrock or Ollama credentials, and its own code
  comment at `agent.py:314-315` states OPFOR doctrine is not encoded).
- **No simulation-derived metric ships.** Per the prompt, unsupported metrics are rendered
  explicitly unavailable rather than filled from the UI's placeholder math.
- **Pre-existing failures in the excluded repositories are not repair work for this product.**
  They are listed in §4 so nobody starts them by accident.

### 2.5 Branding and naming

- The product placeholder name lives in **one** value so it renames without touching logic. The
  string `Stratistics` appears nowhere inside the UI artifact — it exists only in the download
  filename. The single in-app brand string is `【Pytho】`, hard-coded once in the nav markup; the
  product title rendered on every screen is `Strategy Adjudicator`. Both are placeholders.
- `Pytho` is the team name.
- The dataset archive keeps its existing name, `strategy-evaluation-dataset-pytho`.
- The UI ships a different fictional universe (Olvana / Khorathidin / Operation ENDURING
  PHOENIX). **Meridian Sea is added as a distinct, dataset-backed scenario.** The two scenario
  identities are never merged and the UI's numeric outputs are never relabelled as dataset
  results.

---

## 3. Dataset facts the product relies on

### 3.1 Identity

| Fact | Value |
|---|---|
| Branch / HEAD | `dataset` / `f7cc9149088200bc655601410cc0de4e793e4457` |
| Archive | `dataset/strategy-evaluation-dataset-pytho.zip` |
| Archive SHA-256 | `fc5c9d311fd1392d0af367f4522842afa807b29ad60ba41cda446cbbeac54418` |
| Archive integrity | `unzip -t` exit 0, 288 entries |
| Generation seed | `20260908`; regeneration is byte-identical (`repro` gate) |
| License | CC BY 4.0 |

### 3.2 Size

92 documents, 864 claims, 122 entities, 9 strategies. Counts include the three inject batches.
All four verified by `len(load(through_batch=3)[table])`.

### 3.3 Worlds — 64 Blue, and what the "66" figure means

The Meridian game gives Blue **64 worlds**: a world is a θ-assignment over the K = 6 Blue
assumption bits, labelled as a 6-bit string, `000000` … `111111`. That is the number the product
displays for Meridian Sea.

The DATA_CARD's **66** is the count of *distinct* `payoffs.world` label strings across the whole
600-row payoff table, not a per-actor world count:

| game | actor | K | distinct world labels |
|---|---|---:|---:|
| meridian | ent_blue | 6 | 64 |
| meridian | ent_varenia | 1 | 2 |
| rps | ent_rps_p1 | 1 | 2 |
| rps | ent_rps_p2 | 1 | 2 |

The union is 64 + {`0`,`1`} = 66, because the three K = 1 actors share the same two labels.
Summing per-actor world sets instead gives 70. The figure 66 is correct as written in the
DATA_CARD, and the product must not render it as "66 distinct scenario states across all
actors".

### 3.4 Extensions

Six ship and all six gates pass: `rag_qa`, `target_systems`, `capability`, `authority`,
`collection_assets`, `events`. 18 extension tables load on top of the 28 base tables.

### 3.5 Performance

`load(base=True, extensions=<all 6>, through_batch=3)` measured at **0.034-0.048 s**, worst case
0.040 s on the repeat runs, against the two-second budget — a 50x margin. The recompute is inside
`load`: `loader.py:87` calls `eval.engine.recompute` on every base load, so that figure already
includes recomputation of every computed column.

### 3.6 The three demo beats — all verified against the manifests

| Batch | as_of | Verified effects |
|---|---|---|
| 1 | 2026-09-28 | `str_blue_1` valid → invalid, cause is the **acceptable** test failing (`V = 0.3700 below aspiration w·τ = 0.5000`; suitable, feasible, distinguishable, complete all still pass), value 0.657667272 → 0.369958724; valid ranking becomes `str_blue_2`, `str_blue_3`; the chokepoint problem set becomes Significant on all three horizons |
| 2 | 2026-10-23 | `req_01` closes (research, rank 1 → satisfaction, rank null); assumption k2 unknown → holds (`asm_blue_1_k2`, `asm_blue_3_k2`); `str_blue_1` valid again (0.369958724 → 0.647275499); ranking becomes `str_blue_1`, `str_blue_2`, `str_blue_3` |
| 3 | 2026-11-17 | assumption k4 holds → violated (`asm_blue_2_k4`); `he_05` becomes Significant on all three horizons; cyber and energy problem sets become Significant; `req_07` becomes the first collection priority (rank 1, priority 0.24, `gap_type=contradiction`, `predicate=throughput_per_day`, `subject=inf_kestrel_lane`, `created_at=2026-11-15`) |

Adjacent-batch comparison covered strategy value (1e-9) and status, valid-strategy ranking,
per-test validity flags, assumption status, risk level / `p_raw` (1e-6) / trend, problem-set
`max_risk_level`, and requirement status and `jipcl_rank`, plus assertions that no *unlisted*
assumption or problem-set changed. All passed.

### 3.7 Findings the product must build around

**Forced choice is reachable only through `load()`.** The ICD 203 roughly-even-chance
forced-choice rule fires on 6 of 27 `risk_assessments` rows at `through_batch=3` — `he_05` and
`he_06` on near/mid/long — each with a non-null `posture_rationale`. `he_05`'s rationale reads:
"Roughly even chance intelligence estimate; plotted Likely because friendly posture factors are
Blue logistics network: lacks rehearsed mitigations; Meridian Cyber Protection Team: lacks
rehearsed mitigations." But `dataset/truth/risk_assessments.jsonl` holds only `world_version 0`
rows and carries **zero** forced-choice rows, so invariant 19 ("0 forced-choice assessments all
carry posture_rationale") is vacuous, and `ExpectedEffects.RiskAssessmentChanged` has no field to
express the post-batch state. **A product that reads the truth JSONL directly will silently show
`forced_choice_applied = false` everywhere.** Always go through `load()`.

**`loader.py` closes fixture requirements from the manifest answer key.**
`_apply_closed_requirements` (`loader.py:33-52`) reads each batch manifest's
`expected_effects["requirements_closed"]` and, for each listed `req_id`, sets
`status = "satisfaction"` and fills `answered_by_source_id` from the first approved claim in that
batch matching the requirement's `(subject_id, predicate)`. The manifest supplies the *decision*;
the claim search supplies only the *citation*, and if no matching claim exists the requirement is
left open with no error. There is no requirement-satisfaction detector in `loader.py` or
`eval/engine.py`. This is valid labelled replay. It is **not** evidence that the product can
decide whether an independently ingested report satisfies a requirement — that has to be built,
and the ingestion path must be provably unable to read manifests, answer keys or gold claims.

**Requirements are date-filtered** by `created_at <= as_of`, so `req_07` does not exist in the
batch-2 frame at all. That is why its manifest `rank_before` is `null`.

**`recompute` re-derives every computed column on every `load()` call.** Values, statuses,
rankings, risk levels, EVPI priorities and JIPCL ranks in the returned frames are computed, not
read. Copying a formula into the frontend would fork the contract.

**Two extension tables are intentionally empty:** `extensions/authority/truth/decision_log.jsonl`
and `extensions/collection_assets/truth/tasking_plan.jsonl` are 0-byte files at every batch. This is
by design, not a content gap: the dataset specification (v1 §11) defines `decision_log` as a "schema
(empty at ship)" for the Mission Authority Broker and `tasking_plan` as an empty schema for Dynamic
Collection Resource Optimization — workflow logs that a consuming product fills, with example rows
supplied separately (`example_decisions.jsonl`, 24 rows; `greedy_plan.jsonl`, 12 rows). The
extension gates check schema validity, starter query and eval, which these files satisfy.

Product behavior: the two tables are **write-side workflow logs**, distinct from the read-model
tables. The backend never treats them as required-populated tables (they are excluded from the
adapter's required-table preflight), and the product records its own authority decisions and
tasking assignments in product-owned sidecar state (P3), never by writing into `dataset/`.

---

## 4. Protected user work outside this repository

Recorded so nobody touches it. These paths belong to the user. Do not overwrite, delete, stage,
reformat, revert, push or include them in any commit.

| Repository | Protected work |
|---|---|
| `/Users/akshay/Dev/pytho/pytho-vite` | Modified `sst-env.d.ts`; untracked `CLAUDE.md.pre-migration-20260710-0858`; **3 stashes**: `stash@{0}` "On main: round5: sst-env.d.ts", `stash@{1}` "On planningprocess: SST-regenerated env types (production deploy)", `stash@{2}` "On feat/planning-ma-editor: undo claude numbering edits" |
| `/Users/akshay/Dev/pytho/coa-engine` | Modified `docs/STATE.md` (+4) and `docs/baselines/projection-bandwidth.json` (13 lines); **1 unpushed local commit** `13b6a9e`, ahead of `origin/main` by 1 — do not push or rewrite it |
| `/Users/akshay/Dev/pytho/pytho-arena` | Working tree clean, in sync with origin/main, and under an explicit **HOLD**: "NOTHING STARTS WITHOUT A NEW USER INSTRUCTION"; no work item W01-W61 may begin |
| `/Users/akshay/Dev/pytho/pytho-app` | Untracked `CLAUDE.local.md` and `docs/guardrails/` |
| This repository | Untracked `HANDOFF_CODEX.md` at the repo root |

Standing rules that also apply: never `git amend` or force-push on branch `dataset` — the user
commits to it from other sessions. Never `git reset --hard`, `git clean`, or a checkout that
discards work.

Pre-existing failures in the excluded repositories, recorded so they are not mistaken for
regressions caused by this work: `pytho-vite` typecheck (9 new errors over a 726 ratchet) and
`src/data/personas.test.ts:32`; `pytho-arena`
`tests/test_golden_rollout.py::test_scripted_rollout_reproduces_golden_fixture_exactly` (fails on
origin/main too; must not be regenerated or loosened).

The original UI artifact at `/Users/akshay/Downloads/Stratistics Wargaming System.html` is
preserved byte-identical (SHA-256 `0d8e9e47…1c1aebed`). The product copies a recovered tree into
`app/ui`; it never edits the Downloads file.

---

## 5. Phase table

| Phase | Status | Acceptance test | ETA |
|---|---|---|---|
| **P0** — foundation and contracts | **In progress** (this documentation set is the first half) | `docs/STATE.md` records the precheck and the architecture decision; a read-only dataset adapter and typed response contracts exist; tests prove batch 0-3 loading, rejection of invalid batch/ID inputs, clear failure when the dataset is missing, and that no source file under `dataset/` is written | 2026-09-09 |
| **P1** — evaluation service | Planned | Contract tests prove every key manifest effect for batches 1-3 (the beats in §3.6) and at least one full provenance chain from source span to strategy validity, all through `dataset.load` + `dataset/eval` | 2026-09-09 → 2026-09-10 |
| **P2** — connect the existing operator workbench | Planned | Frontend tests prove an invalid strategy is never recommended and that changing the selected batch updates the decision overview, timeline and comparison panels consistently; no placeholder value from `COA_LIB` / `compute()` remains on a connected screen | 2026-09-10 |
| **P3** — evidence, risk and collection analysis | Planned | Tests cover contradiction, supersession, exact span display, filters, forced-choice rationale, `req_01` closure and `req_07` creation; and the new-report → proposed claim → review → accepted evidence → recomputation flow with a report authored after the fixture, its value and date varied in a test, proven unable to read gold claims, answer keys or manifest `expected_effects` | 2026-09-10 → 2026-09-11 |
| **P4** — demo hardening | Planned | Reset, loading, empty, error and incompatible-schema states exist; one documented offline command launches the demo; browser acceptance passes at 1440x900, 1280x800 and a narrow mobile width with no console errors, no failed API calls, no clipped or overflowing content; `docs/DEMO.md` is verified step by step | 2026-09-11 |
| **P5** — final validation | Planned | All repo unit, contract, type, lint and build checks pass; the browser acceptance flow passes against a production build; `make check` and `make test` pass again; the archive SHA-256 is unchanged; `git diff --check` and `git status --short` are clean in every touched repository; the T0 → 1 → 2 → 3 → T0 flow works without a restart | 2026-09-11 |

Every step marked "to be verified in P4" in `docs/DEMO.md` is part of P4's acceptance, not P0's.

---

## 6. Blockers and risks

**Blockers — none.** Every precheck gate passes and the dataset baseline is green.

**Risks, in order of how much they can cost:**

1. **New-report ingestion is the long pole and nothing exists to start from.** No component in
   any repository processes an unseen document: `eval/baseline.py` reads gold claims and gold
   spans to build its predictions, `run_llm_baseline.py` was never run, the UI's `ingest`
   handler discards the report body and assigns a PIR by `1 + (intel.length % 3)`, and
   `loader.py` closes requirements from the manifest. If P3 does not finish, **the demo is
   partial and must say so** in the final report.
2. **Two submitted claims are not supported and cannot be closed by building.** "Grounded in
   Army-published adversary models" — no Army publication is named anywhere, in the submitted
   text, the UI, the dataset or `doctrine/`. "Monte Carlo wargaming, thousands of iterations" —
   the dataset is a finite Bayesian game with no transition dynamics, and the UI's `runSim()` is
   a `setInterval` progress bar in front of Gaussian noise around hand-written constants. The
   team must correct the claims or accept a scope change; the product must not present fictional
   Red COAs or the payoff tensor as proof of source grounding.
3. **Every UI number on a connected screen is currently fabricated.** `P(SUCCESS)`, the `80% CI`,
   `CASUALTIES P90`, `P(ESCALATION)`, the hop counts and the ARC table all come from local
   placeholder math. Each must either get a supported dataset source under its real name or be
   rendered explicitly unavailable. Dataset utility is not probability of success, and `value_ci`
   is an adversary-scenario range, not a confidence interval.
4. **Six UI behaviours key off array position** (`p.assumption`, `c.deps`,
   `PROBLEM_SETS[failIdx]`, `pir: 1 + (len % 3)`, the `'A' + (i+1)` labels, `planSel`). Stable
   IDs are a prerequisite for every other change. Doing them late means redoing the work.
5. **The UI's collection `cycle` handler fabricates evidence.** One click sets the linked
   assumption to Valid and `conf: Math.max(a.conf, 85)` with no report, no claim, no review and
   no provenance. This is the single most misleading behaviour in the artifact and must be
   replaced by the reviewed-evidence satisfaction rule before any demo.
6. **Constraints and restraints have no provenance in the frozen schema.** They are plain
   `list[str]` on `strategies` with no IDs, spans, windows, confidence, review state or change
   links. The submitted claim that they are tracked objects "each with a source, a validity
   window, and a confidence score" is not true as shipped. Product-owned sidecar records keyed to
   stable IDs are the only allowed fix; the dataset is not edited and provenance is not invented.
7. **A known 404 will appear in server logs after integration.** The JIPOE `<iframe
   src="{{ mapSrc }}">` is parsed by `DOMParser` before dc-runtime binds it, so the browser
   fires one request for the literal `{{ mapSrc }}` string. Switching to a relative
   `./assets/jipoe-map/index.html?threat=…` URL removes it.
8. **One offline break in the recovered UI:** `docreader.js` fetches
   `https://cdn.jsdelivr.net/npm/pdf-parse@2.4.5/…` when a user uploads a PDF. Everything else
   is fully offline. Either vendor the parser or state that PDF upload is unavailable offline.
9. **Two unreconciled edition dates in the dataset's own doctrinal basis.** `DATA_CARD.md` dates
   CJCSM 3105.01C to 14 February 2025 while `doctrine/README.md` and `EXTRACTS.md` say 10 July
   2026; JP 2-01 is 5 July 2017 versus 5 January 2012. The extracts were verified against the
   PDFs in hand, so `EXTRACTS.md` is the version the code reads. Resolve before repeating either
   date externally. Not a blocker for the build.
10. **A concurrent session shares `/tmp/precheck/`.** Files this build did not write live there.
    Leave them alone.

---

## 7. Constraints

Standing rules for this build. Any user "don't / only / keep / stop" instruction is appended here
verbatim.

- The dataset is a frozen contract. Do not modify `dataset/`, the archive, or any schema to make
  the product easier to build. If a check, checksum or manifest stops matching, stop and report
  the exact mismatch.
- Use `dataset.load(...)` and `dataset/eval/` for every computed result. No formula is copied into
  the frontend; no score, ranking or risk level is hand-entered anywhere in product code.
- Keep likelihood and confidence distinct. Never display them as one probability.
- Label `value_ci` as an adversary-scenario range, never a statistical confidence interval.
- Do not imply the finite payoff model predicts real combat outcomes. Values are
  scenario-relative decision-support outputs.
- All scenario content is UNCLASSIFIED and synthetic. Keep that marking visible in the
  application and in every export.
- No network service and no LLM in the deterministic evaluation path. No cloud credentials for
  the base demo.
- Do not add live external feeds in this handoff. Record them as follow-up candidates.
- Do not silently fall back to mocked or hard-coded results. Fail clearly instead.
- Edits stay inside this repository, and inside `app/**`, `docs/**` and the root `README.md`.
- Commit only after a phase gate is green; never include pre-existing user changes in a commit.

---

## Appendix — archived dataset-build state

The dataset build session that produced this repository recorded its own state here. Kept for
history; it is not the product's state.

> **Goal.** Finish all work in `CLAUDE_CODE_PROMPT_dataset_and_schemas_v2.md` and its referenced
> v1 prompt.
>
> **Phases.** P0 schemas, extracts, style guides, RPS → P1 scenario, scaffold, facts, guidance,
> PIRs → P2 strategies, payoff tensors, grounding graph, validity → P3 risk inputs and cascade →
> P4 intelligence and doctrinal product rendering → P5 inject manifests and loader → P6
> extraction/effects scorers and measured baseline → P7 data card, review samples,
> reproducibility, zip → P8 extension layers and final package. All gates passed; final commit
> `f7cc914`.
>
> **Constraints in force during that session.** No web scraping; no external datasets beyond
> `doctrine/`. That session did not build the application. Every schema is a contract, frozen
> once its acceptance tests pass. Never fabricate a fact about a real entity, and never attribute
> a fictional fact to a real organization. Write the test before the code; do not advance on a
> failing gate; never commit a failing gate.
>
> **Decisions.** Continue on branch `dataset`. Deterministic template rendering; document any
> unavailable LLM baseline honestly. Inclusive `valid_to`; half-open claim span offsets. The
> deliverable and archive are named `strategy-evaluation-dataset-pytho`.
>
> **Open items at handoff.** An unestablished LLM rendering/baseline capability — no model
> baseline result may be fabricated. Six further items are recorded in the untracked
> `HANDOFF_CODEX.md`; the precheck refuted its first item (the forced-choice rule does fire, see
> §3.7) and confirmed the rest.
