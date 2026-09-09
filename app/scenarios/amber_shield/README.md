# AMBER SHIELD — scenario core

UNCLASSIFIED — SYNTHETIC. For exercise and demonstration use only. Not a real plan. Doctrine,
product types and organizational roles are real and cited; every unit disposition, assumption,
course of action, number and assessment is fictional.

A computed scenario model for the operation the shipped v3 UI already talks about (USEUCOM
Operation AMBER SHIELD, Baltic Region). It emits the same table shapes the frozen dataset uses, so
`eval/engine.py::recompute` runs on it unchanged and the API is served by the same code path.

```python
from app.scenarios.amber_shield import SCENARIO, load

rows = load()                 # {table_name: [row dict, ...]}, every computed column filled
rows["strategies"][0]["value"]
```

```
python -m app.scenarios.amber_shield.build     # rebuild truth/*.jsonl and print row counts
python -m pytest -q app/tests/scenarios        # 59 tests
```

## Modules

| file | what it holds |
| --- | --- |
| `scenario.py` | the authored model: entities, guidance chain, objectives, game form, resources, actions, the eight assumptions, the five COAs and three Russian COAs, policy rules, decision points, budgets |
| `payoffs.py` | the finite Bayesian game `u(σ, σ', θ)`; structured, no RNG |
| `placeholders.py` | every row three other agents own, marked `PLACEHOLDER` |
| `build.py` | assembles, validates against the dataset's pydantic models, runs `recompute`, writes `truth/` |
| `_dataset.py` | the one supported way to import `eval/` and `gen/` from the frozen dataset |

## Id scheme

Typed, readable prefixes, following `dataset/schema/SCHEMA.md` conventions:

```
ent_   actor, polity, JRAM problem-set entity     loc_   location
inf_   infrastructure                             unit_  unit
sys_   weapon or sensor system                    role_  organization role
obj_   objective, end state, effect               str_   strategy (COA)
asm_   assumption      act_  action               res_   resource
rule_  policy rule     dp_   decision point       om_    opponent model
gd_    guidance        dep_  dependency edge      clm_ / fct_  claim / fact
```

The Blue actor is `ent_useucom`, Red is `ent_rus`, and the game is `amber_shield`. Blue COAs are
`str_coa_1` … `str_coa_5`, in the UI's `COA_LIB` order. Assumptions are `asm_a1_coa_1` …
`asm_a8_coa_5`: `index_k = n - 1` for A*n*, so a COA's `COA_LIB` `deps` entry `d` is `index_k = d - 1`.

## Where the numbers come from

The five UI comparison criteria are the five `objective` rows for `ent_useucom`. Each is mapped
onto one of `COA_LIB`'s authored constants, read straight off `app.logic.js::compute()`:

| objective | UI risk row | `COA_LIB` field | sense |
| --- | --- | --- | --- |
| `obj_mission` | `rm` risk to mission | `s` | higher is better |
| `obj_personnel` | `rp` risk to personnel | `cas` | lower is better |
| `obj_escalation` | `re` risk of escalation | `esc` | lower is better |
| `obj_time` | `rt` risk to time | `days` | lower is better |
| `obj_resources` | `rr` risk to resources | `res` | lower is better |

Each constant is mapped linearly onto `[0.15, 0.85]` across the range the five COAs span, sense
flipped where lower is better. That preserves the UI's per-criterion ordering exactly while making
the criteria commensurate, so the weight vector `{mission 4, personnel 3, escalation 4, time 2,
resources 1}` (normalized) means something.

`u(σ, σ', θ)[o] = floor(σ)[o] + Σ_k θ_k · δ_k(σ)[o] + resilience(σ) · shift(σ')[o]`, with `δ_k(σ)`
nonzero exactly when `k ∈ deps(σ)` and `floor(σ) = authored(σ) − Σ_k δ_k(σ)` — so the
all-assumptions-hold payoff is exactly the authored table, and each failing assumption subtracts a
documented amount. K = 8, 2^8 = 256 worlds; `recompute` takes about 90 ms.

## Hooks for the other three agents

Everything below is in `placeholders.py`. Replace the block, keep the shape; nothing outside that
module needs to change. Rerun `python -m app.scenarios.amber_shield.build` afterwards, then
`python -m pytest -q app/tests/scenarios`.

### Claims / corpus agent — `claims`, `sources`

| symbol | contract |
| --- | --- |
| `SOURCES` | one stand-in `assessment` row. Replace with the rendered corpus. `path` is relative to `ROOT`; `text_sha256` must be the SHA-256 of the rendered text |
| `GROUNDING_EVIDENCE` | one `(index_k, value, estimative, likelihood_icd203, confidence_icd203)` tuple per assumption. The `(subject_id, predicate)` pair and the tolerance are fixed by `scenario.ASSUMPTIONS` — do not move them. `assumptions.p_holds` is the derived confidence of the claim you supply, so the evidence sets the world probabilities |
| `RED_GROUNDING_EVIDENCE` | the same, for the single Red assumption |
| `TOV_CLAIMS` | the seven theory-of-victory waypoint claims. `build.py::_dependencies` wires `action -enables-> clm_ph_tov_<key> -supports-> <objective>`; keep the keys in `TOV_OBJECTIVE` or update both |
| `facts()` / `claims()` | one claim per fact, `truth_claim_id` set. Invariant 3 needs every fact instantiated; invariant 4 needs each `(subject, predicate)` pair to appear once among approved claims |

Entity and assumption ids to import: `scenario.entities()`, `scenario.ASSUMPTIONS` (ids are
`asm_a1` … `asm_a8` plus a `_coa_n` suffix per strategy row).

Invariant 02 (spans point into real text and mention the subject or the value) is **not** run
today because there is no corpus. Add it to `SCENARIO_INVARIANTS` in
`app/tests/scenarios/test_schema.py` once the corpus lands, together with 11–13, 15–17 and 20.

### Risk agent — `problem_sets`, `harmful_events`, `risk_drivers`, `risk_sources`, `escalation_edges`

| symbol | contract |
| --- | --- |
| `PROBLEM_SETS_SPEC` | eight rows, one per assumption cluster in the UI's `PROBLEM_SETS` map, each already bound to an `ent_ps_*` entity. `thing_of_value_ids` must be objectives |
| `HARMFUL_EVENTS_SPEC` | `thing_of_value_id` must be one of the five criteria objectives. MSR rows carry `strategic_value` + `damage_degree`; MR rows carry `risk_subset` + `fig28_row` + `fig28_cell` (invariant 18) |
| `RISK_DRIVERS_SPEC` | `(claim_subject_id, claim_predicate)` must resolve against claims that exist. A driver whose dominant satisfying claim carries `roughly_even_chance` triggers the JRAM forced-choice rule, which needs `posture_subject_ids` and `posture_state` claims on those entities |
| `ESCALATION_EDGES_SPEC` | must stay a DAG (invariant 8) |

**The one thing that changes behaviour outside this module.** `build.py::tables()` currently sets
`strategies.mitigates_he_ids = every placeholder harmful event`, and the placeholders are pitched
so no MR event is assessed `high`. The JP 5-0 acceptable test fails for any COA that does not
mitigate a `high` MR event, and such a COA also drops out of the EVPI candidate set. When you
publish real ids, replace that line with a per-COA map — which COA actually mitigates which event
is your call, and it is the intended way to make `acceptable` bite.

### Collection agent — `pirs`, `collection_requirements`

| symbol | contract |
| --- | --- |
| `PIRS_SPEC` | the seven OPORD PIRs, `pir_01` … `pir_07`. The decision points reference these ids, so keep them: `scenario.COMMON_DPS` uses `pir_01`, `pir_04`, `pir_05` and `scenario.COA_DPS` uses `pir_01`, `pir_02`, `pir_03`, `pir_07`. `decision_point_ids` is filled by `build.py` from the decision-point table — leave it empty here |
| `COLLECTION_REQUIREMENTS_SPEC` | `assumption_id` is given as an `index_k`; `build.py` binds it to a real assumption row. A requirement with an assumption gets `priority = EVPI_k`, so `jipcl_rank` is driven by the payoff structure. `routing` must match `^(JIOC\|JCMB\|.+ J-2)$` |

## What the tests prove

`app/tests/scenarios`:

* every row validates against `dataset/gen/models.py`, before and after recompute;
* the twelve `dataset/gen/validate.py` invariants that apply to a scenario's tables pass
  (01, 03–10, 14, 18, 19) — imported, not reimplemented;
* `recompute` produces a value, five validity tests and a status for all five COAs, in under 300 ms;
* information about at least two assumptions (A3 and A6) changes which COA is best, so EVPI is not
  an artefact of the payoff shape; EVPI is positive exactly where the argmax flips;
* no COA dominates on every objective, and the weighted ranking under the UI's default weights is
  not degenerate;
* the feasible test is not vacuous (halving one budget makes that COA infeasible) and the
  acceptable test separates the COAs (three valid, two below aspiration);
* COA names, approaches, concepts, `deps` and authored constants are verbatim from
  `app/ui/src/app.logic.js`, and the eight assumption statements are verbatim from the OPORD;
* two builds are byte-identical and the checked-in `truth/` is what the build produces.
