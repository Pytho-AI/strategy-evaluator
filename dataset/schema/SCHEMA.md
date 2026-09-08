# SCHEMA.md — the schema contract

One JSON Schema per table lives beside this file (`<table>.json`, JSON Schema 2020-12, exported
from `gen/models.py`; `x-primary-key`, `x-foreign-keys`, `x-computed`, `x-truth-only` annotate each
schema). This document states, for every table: purpose, columns, primary key, foreign keys, the
doctrinal source of every enum and template, computed-column definitions, and the invariants. Once
the P0 acceptance tests pass the contract is frozen; later phases only add rows, never columns.

Conventions: ids are readable prefixed strings (`ent_0042`, `clm_0317`, `str_blue_2`, `he_04`), never
UUIDs. Dates are ISO 8601 in JSONL. `truth/` holds one JSONL file per table; an application's
output uses the same files minus the truth-only tables and columns. All content is fictional;
doctrine, organizations, processes and product formats are real and cited.

## 0. The formal model the tables encode

A **game form** `G = <N, S, {A_i}, T, {O_i}, H>` (tables `games`, `actions`, `entities`) is the
operational environment. A **strategy** `σ_i = <U, Π, M, Θ, Σ_-i, ρ>` is a JP 5-0 course of action
nested in the JSPS (`strategies`, `strategy_objectives` = U and w, `policy_rules` +
`decision_points` = Π, `strategy_resources` = M, `assumptions` = Θ, `opponent_models` = Σ_-i,
`strategies.risk_functional` = ρ). The **claim graph** (`claims`, `facts`, `dependencies`) is the
unifying primitive; assumptions, risk drivers and collection requirements are views over it.

## 1. Computed quantities (definitions; reference implementation in `eval/`)

All computed columns are recomputed from truth by `eval/engine.py::recompute` and checked by
invariant 10 to 1e-9. Nothing computed is typed by hand.

**Derived confidence** (`claims.confidence`, `facts.confidence`; v2 §2.6a; `eval/value.py::derived_confidence`):
`confidence = 0.5 + (1 − s) · (mid − 0.5)` where `mid` is the ICD 203 band midpoint of
`likelihood_icd203` for estimative claims (almost_no_chance 0.03, very_unlikely 0.125, unlikely
0.325, roughly_even_chance 0.50, likely 0.675, very_likely 0.875, almost_certain 0.97) and
`mid = 0.97` (the almost-certain midpoint) for factual claims; `s` is the confidence shrink factor
(high 0.0, moderate 0.15, low 0.35). Factual: high 0.97, moderate 0.8995, low 0.8055.

**Worlds and P(θ)** (`eval/value.py`): K assumptions per (game, actor) indexed by `index_k`;
θ ∈ {0,1}^K; `P(θ) = Π_k p_k^θ_k (1 − p_k)^(1 − θ_k)`; `p_k = assumptions.p_holds` of any
assumption row with that `index_k` (rows sharing `index_k` share the grounding claim).

**Assumption state** (`assumptions.p_holds`, `status`; v2 §2.4; `eval/value.py::assumption_state`):
the current approved claim is the one for (subject, predicate) whose valid window contains `as_of`
(latest `asserted_at` wins). `unknown`: no approved claim ever valid → p = 0.5. Otherwise `sat` =
tolerance predicate holds on the claim value; `p = confidence` if `sat` else `1 − confidence`;
status `stale` if no claim is valid at `as_of` (window expired) or the claim's
`confidence_icd203 = low`; else `holds` / `violated`.

**Value** `V(σ) = ρ over (θ ~ P, σ' ~ Σ_-i) of w·u(σ, σ', θ)` with `u` from `payoffs` (utility
vector ordered by the actor's `objectives` of kind `objective` sorted by `objective_id`; weights
from `strategy_objectives`, missing = 0). ρ: `expected` = mean; `cvar` = mean of the worst
`risk_alpha` probability mass; `minimax` = minimum over the support.
`value_ci = [min, max]` over σ' of `E_θ[w·u]` (the stated uncertainty across adversary COAs).
`robustness = min_θ E_σ'[w·u]`. `aspiration = Σ_k w_k τ_k` with τ_k = `objectives.aspiration` (0 if null).

**Sensitivity** `Sensitivity_k(σ) = V(σ | θ_k = 1) − V(σ | θ_k = 0)` (conditioning fixes bit k).
**EVPI** `EVPI_k = E_θk[max_σ V(σ|θ_k)] − max_σ E_θk[V(σ|θ_k)]` over the actor's strategies, each
under its own ρ; clipped at 0.

**Validity** (`strategies.validity`, `status`; JP 5-0 Ch. III §(q); `eval/validity.py`):
suitable = every objective of `guidance_source` belonging to the actor is reachable from the COA's
actions along the `theory_of_victory` edges; feasible = for every resource, Σ over periods of the
maximum cost among rules active in that period ≤ budget (worst-case trajectory); acceptable =
`V ≥ aspiration` and no `MR` harmful event assessed `high` (any horizon) that is absent from
`mitigates_he_ids`; distinguishable = differs from every other COA of the actor in ≥ 2 of
{main_effort, scheme (set of tactic classes used), sequencing, mechanism (set of action mechanisms),
task_org, reserves}; complete = five mission fields non-empty, an end state, ≥ 1 rule, every decision
point's branch rules exist. `status = infeasible` if feasible fails, `invalid` if any other test
fails, else `valid`. `stale` is the transient status an application assigns between a claim change
and recomputation; the reference engine never outputs it.

**Ratings** (`strategy_objectives.rating_1_to_3`, JP 5-0 App. F): for each objective k, rank the
actor's valid strategies by `E[u_k]`; rating = 1 + round(2 · rank / (n − 1)) (3 = best, 1 = worst;
3 when n = 1); invalid strategies get 1.

**Risk assessment** (`risk_assessments`; JRAM Encl. B–C; `eval/jram.py`, `eval/engine.py::assess_risk`):
for horizon h with window `[as_of + start_years, as_of + end_years]` (near 0–3, mid 2–7, long 5–15):
`P_raw = clip[0.01, 0.99]( base_p + Σ_{active drivers} delta )`, a driver being active when `h ∈
driver.horizons` and some approved claim for its (subject, predicate) whose valid window intersects
the horizon window satisfies `(op, value)`; then cascade by noisy-OR in topological order over
`escalation_edges`: `P_raw(j) = 1 − (1 − P_raw_pre(j)) · Π_{i→j} (1 − lift_ij · P_raw(i))`.
`p_level` = Fig. 6 bin (≤ 0.20 very_unlikely, ≤ 0.50 unlikely, ≤ 0.80 likely, else very_likely) —
unless the dominant active driver's latest satisfying claim carries `roughly_even_chance`, in which
case the forced-choice rule (JRAM Encl. C §4.d) sets `p_level` from the `posture_state` claims of
`harmful_events.posture_subject_ids` (`likely` if any is vulnerable / out_of_position / unmitigated
or none is documented; `unlikely` if all are hardened / postured_to_react / mitigated) and records
`posture_rationale`. `c_level` = Fig. 23[strategic_value][damage_degree] for MSR, or `fig28_cell` of
`fig28_row` for MR. `risk_level` = CONTOUR[c_level][p_level] (team's reading of Fig. 8, below).
`trend` = sign of the least-squares slope of P_raw over horizon midpoints (1.5, 4.5, 10 years),
threshold 0.002 per year. `statement_text` = Fig. 11 template. `problem_set_assessments.max_risk_level`
= max over the set's events; `aggregated_statement_text` = Fig. 5 template.

Risk contour (rows consequence, columns very_unlikely / unlikely / likely / very_likely):
minor → low, low, moderate, moderate; modest → low, moderate, moderate, moderate; major → moderate,
moderate, significant, significant; extreme → moderate, moderate, significant, high. This is the
team's reading of the drawn Fig. 8 (cell centre versus the dashed boundaries), constrained by the
manual's own examples (E18b–d, Fig. 11 example). Four cells lie within ~5% of a boundary and are
listed with their alternative reading in `eval/jram.py::CONTOUR_BOUNDARY_CELLS`.

**Collection priority** (`collection_requirements.priority`, `jipcl_rank`; v2 §2.7): `EVPI_k` of the
assumption in `assumption_id`; otherwise `(1 − confidence of the current claim) × degree of that
(subject, predicate)'s claims in the dependency graph` (degree ≥ 1; confidence 0 if no claim).
`jipcl_rank` = rank by descending priority (ties by `req_id`) among requirements whose status is not
`satisfaction` or `closed`; null otherwise.

## 2. Predicate vocabulary (`claims.predicate`, `facts.predicate`, `assumptions.predicate`, `risk_drivers.claim_predicate`)

DATASET vocabulary; `status` values follow JP 3-60 Ch. I §8.b(2), `posture_state` values follow JRAM Encl. C §4.d(2).

| predicate | value_type | unit | allowed values | meaning |
|---|---|---|---|---|
| `range_km` | number | km | — | maximum effective range of a system |
| `count` | number | each | — | number of systems or platforms held by a unit |
| `readiness` | number | fraction | — | readiness as a fraction 0..1 of full mission capability |
| `status` | string | — | operational, degraded, inoperative | functional status (JP 3-60 Ch. I §8.b(2)) |
| `throughput_per_day` | number | transits/day | — | chokepoint or port throughput per day |
| `alignment` | string | — | blue_aligned, neutral, red_aligned | polity alignment |
| `basing_access` | bool | — | — | whether the polity grants Blue basing access |
| `mobilization_days` | number | days | — | days for the actor to mobilize the stated brigade count |
| `mobilized_brigades` | number | brigades | — | brigades currently mobilized |
| `cyber_capacity` | string | — | limited, moderate, extensive | offensive cyber capacity against logistics networks |
| `munitions_stock_days` | number | days | — | days of supply of precision munitions |
| `posture_state` | string | — | hardened, postured_to_react, mitigated, vulnerable, out_of_position, unmitigated | friendly posture factor (JRAM Encl. C §4.d(2)) |
| `capacity_mw` | number | MW | — | generating capacity |
| `displaced_persons` | number | persons | — | internally displaced persons |
| `outage_hours` | number | hours | — | cumulative outage hours in the period |
| `intent` | string | — | coercive, defensive, opportunistic, benign | assessed intent of an actor |
| `mixing_bias` | number | fraction | — | rock-paper-scissors: deviation of a player's mix from uniform |
| `located_at` | entity | — | — | subject is located at object (location) |
| `operated_by` | entity | — | — | system is operated by unit/actor |
| `subordinate_to` | entity | — | — | unit is subordinate to unit/actor |
| `supplies` | entity | — | — | infrastructure supplies location/unit |
| `controls` | entity | — | — | actor controls location |
| `hosts` | entity | — | — | location hosts unit |

## 3. Enumerations and their doctrinal sources

| enum | values | doctrinal source | note |
|---|---|---|---|
| `DocType` | `reference_entry`, `sitrep`, `news`, `message_traffic`, `tabular`, `assessment`, `risk_context`, `collection_plan`, `coa_statement`, `guidance` | v2 §3.1; product formats: JRAM Fig. 3 (risk_context), JP 2-01 Fig. III-8 (collection_plan), JP 5-0 Ch. III/App. F (coa_statement), CJCSI 3100.01F Encl. A/C/D (guidance) | DATASET list of document kinds |
| `Reliability` | `A`, `B`, `C`, `D`, `E`, `F` | Source reliability A–F (Admiralty/NATO code); JP 2-01 Ch. III §13 does not reproduce the scale | DATASET usage; letter scale is the standard intelligence source-reliability rating |
| `Credibility` | `1`, `2`, `3`, `4`, `5`, `6` | Information credibility 1–6 (Admiralty/NATO code) | as above |
| `Perturbation` | `paraphrase`, `unit_drift`, `stale_echo`, `implicit`, `distractor`, `alias`, `typo`, `contradiction`, `hedge_drift`, `mixed_scale` | v1 §6, v2 §6 | DATASET realism perturbations |
| `EntityType` | `actor`, `unit`, `system`, `location`, `polity`, `infrastructure`, `problem_set`, `organization_role` | v2 §3.2 | DATASET |
| `ValueType` | `entity`, `number`, `string`, `bool`, `date` | v1 §3.3 | DATASET |
| `LikelihoodICD203` | `almost_no_chance`, `very_unlikely`, `unlikely`, `roughly_even_chance`, `likely`, `very_likely`, `almost_certain` | ICD 203 (12 Jun 2023) 7-level scale as reproduced in JRAM Fig. 19, p. C-4 | bands in ICD203_BANDS |
| `ConfidenceICD203` | `low`, `moderate`, `high` | JRAM Encl. C §4.c(1)-(3), p. C-5 | High / Moderate / Low |
| `ClaimStatus` | `proposed`, `approved`, `rejected`, `superseded` | v1 §3.3 | DATASET |
| `Predicate` | `range_km`, `count`, `readiness`, `status`, `throughput_per_day`, `alignment`, `basing_access`, `mobilization_days`, `mobilized_brigades`, `cyber_capacity`, `munitions_stock_days`, `posture_state`, `capacity_mw`, `displaced_persons`, `outage_hours`, `intent`, `mixing_bias`, `located_at`, `operated_by`, `subordinate_to`, `supplies`, `controls`, `hosts` | DATASET; `status` values follow JP 3-60 Ch. I §8.b(2); `posture_state` values follow JRAM Encl. C §4.d(2)(a)-(b) | controlled vocabulary |
| `PostureState` | `hardened`, `postured_to_react`, `mitigated`, `vulnerable`, `out_of_position`, `unmitigated` | JRAM Encl. C §4.d(2)(a)-(b), p. C-5 | forced-choice posture factors |
| `GuidanceProductType` | `NSS`, `NDS`, `NMS`, `JSCP`, `GCP`, `CCP`, `contingency_plan`, `OPORD` | CJCSI 3100.01F Encl. A §3.c(2)-(3) and Encl. C §1-2, Encl. D §3-6; JP 5-0 Glossary (contingency plan, OPORD) | NSS/NDS/NMS/JSCP/GCP/CCP + subordinate plans |
| `TimeHorizon` | `immediate`, `near`, `mid`, `long` | JRAM Encl. B §3.a(1)-(2), p. B-3; CJCSI 3100.01F Encl. A fn. 4 | near 0–3 / mid 2–7 / long 5–15 years; immediate = expedited process |
| `ObjectiveKind` | `end_state`, `objective`, `effect` | JP 5-0 Ch. IV Fig. IV-9, p. IV-27 | end state / objectives / effects |
| `Direction` | `max`, `min` | v1 §3.7 | DATASET |
| `TacticClass` | `posture`, `isr`, `strike`, `logistics`, `information`, `diplomatic`, `cyber`, `signal` | v1 §3.6 | DATASET |
| `Echelon` | `national`, `theater_strategic`, `operational`, `tactical` | JP 5-0 Fig. IV-9 levels (national strategic, theater strategic, operational, tactical) |  |
| `RiskFunctional` | `expected`, `cvar`, `minimax` | v1 §2.2 ρ ∈ {E, CVaR, minimax}; commander's risk tolerance per JRAM Encl. B §1.b | DATASET formalization |
| `StrategyStatus` | `valid`, `invalid`, `stale`, `infeasible` | v2 §3.7 | invalid = fails a JP 5-0 validity test (Ch. III §(q)) |
| `ValidityTest` | `suitable`, `feasible`, `acceptable`, `distinguishable`, `complete` | JP 5-0 Ch. III §(q) 1–5, pp. III-41–III-42 | suitable, feasible, acceptable, distinguishable, complete |
| `DistinguishDim` | `main_effort`, `scheme`, `sequencing`, `mechanism`, `task_org`, `reserves` | JP 5-0 Ch. III §(q)4 a–f, p. III-42 | main effort, scheme, sequential/simultaneous, mechanism, task organization, reserves |
| `Sequencing` | `sequential`, `simultaneous` | JP 5-0 Ch. III §(q)4.c | sequential versus simultaneous maneuvers |
| `AdversaryCoaLabel` | `most_likely`, `most_dangerous`, `alternative` | JP 5-0 Ch. III COA development inputs (Fig. III-13): enemy most likely / most dangerous COA | alternative = DATASET third support point |
| `AssumptionRole` | `state`, `transition`, `opponent`, `means` | v1 §3.13 | DATASET |
| `AssumptionOrigin` | `higher_hq`, `own` | JP 5-0 Ch. III §(6)(a) and (b)3, p. III-17 | higher headquarters assumptions are followed in framing but validated for execution |
| `AssumptionStatus` | `holds`, `violated`, `stale`, `unknown` | JP 5-0 Ch. III §(6)(b)1 validate/invalidate cycle; v2 §2.4 | holds / violated / stale / unknown |
| `CmpOp` | `==`, `!=`, `<`, `<=`, `>`, `>=`, `abs_le`, `in` | v1 §3.13 | DATASET |
| `DependencyKind` | `supports`, `contradicts`, `grounds`, `requires`, `enables`, `drives`, `escalates` | v2 §2.4 | DATASET typed graph |
| `NodeType` | `claim`, `assumption`, `strategy`, `action`, `objective`, `problem_set`, `harmful_event` | v2 §2.4 | DATASET |
| `RiskType` | `MSR`, `MR` | JRAM Encl. C §6.b(1)-(2), pp. C-8–C-10; Glossary Part II | MSR / MR |
| `RiskSubset` | `operational`, `projected_mission`, `force_management`, `institutional` | JRAM Encl. C §6.b(2)(a)1-2 and (b)1-2, pp. C-10–C-12; Fig. 27 | operational, projected mission, force management, institutional |
| `StrategicValue` | `homeland_vital`, `ally_global`, `partner_regional`, `other_local` | JRAM Fig. 23, p. C-10 | Homeland/Vital, Ally/Global, Partner/Regional, Other/Local |
| `DamageDegree` | `confined`, `considerable`, `catastrophic`, `existential` | JRAM Fig. 22 and Fig. 23, pp. C-9–C-10 | Confined, Considerable, Catastrophic, Existential |
| `HarmCondition` | `action`, `inaction`, `posture`, `plan` | JRAM Fig. 11, p. B-16 ([action/inaction/posture/plan] slot) |  |
| `SourceKind` | `threat`, `hazard` | JRAM Encl. B §3.b(2)(a)-(b), p. B-5 | threat / hazard |
| `DriverKind` | `frequency`, `vulnerability`, `resilience`, `criticality`, `accessibility`, `recognition`, `impact`, `resources`, `response`, `reliance` | JRAM Encl. B §3.b(3)(a)-(j), pp. B-5–B-6 | ten driver considerations |
| `DriverLocus` | `internal`, `external` | JRAM Fig. 4, p. B-6 | internal / external |
| `PLevel` | `very_unlikely`, `unlikely`, `likely`, `very_likely` | JRAM Fig. 6, p. B-8 | Very Unlikely ~01-20%, Unlikely ~21-50%, Likely ~51-80%, Very Likely ~81-99% |
| `CLevel` | `minor`, `modest`, `major`, `extreme` | JRAM Fig. 7, p. B-8 | Minor / Modest / Major / Extreme |
| `RiskLevel` | `low`, `moderate`, `significant`, `high` | JRAM Fig. 8, p. B-9; Glossary 'Risk Level' | Low / Moderate / Significant / High |
| `Trend` | `up`, `down`, `flat` | JRAM Encl. B §3.c(3), p. B-10 | trending up / trending down; flat = no modifier |
| `GapType` | `missing`, `stale`, `low_confidence`, `contradiction` | v1 §3.18 | DATASET |
| `RfiDisposition` | `answered_from_holdings`, `gap_confirmed` | JP 2-01 Ch. III §13.b(1), p. III-19 | RFI checks holdings; gap identified when information is not available |
| `ReqStatus` | `research`, `validation`, `submission`, `satisfaction`, `closed` | JP 2-01 Ch. III §13.a, p. III-19 (research, validation, submission, satisfaction) | `closed` is a DATASET terminal state, not a JP 2-01 tracking state |
| `Discipline` | `GEOINT`, `SIGINT`, `HUMINT`, `OSINT`, `MASINT` | JP 2-01 Ch. III §11.b(3) and Fig. III-9 (GEOINT, SIGINT, HUMINT, MASINT); OSINT per JP 2-01 glossary |  |
| `TargetCharacteristicType` | `physical`, `functional`, `cognitive_control_informational`, `environmental`, `temporal` | JP 3-60 Ch. I §8 a–e, pp. I-13–I-17 | physical; functional; cognitive, control, and informational; environmental; temporal |

## 4. Tables

### `sources`

L0 provenance: every rendered document/product with reliability, credibility, batch and perturbations.

- Primary key: `source_id`

| column | type | required | notes |
|---|---|---|---|
| `source_id` | str | yes |  |
| `doc_type` | enum `DocType` | yes |  |
| `title` | str | yes |  |
| `published_at` | date | yes |  |
| `author_org` | str | yes | fictional unit, or a real organizational role such as 'supported CCMD J-2' |
| `reliability` | enum `Reliability` | yes |  |
| `credibility` | enum `Credibility` | yes |  |
| `real_world` | bool | no |  |
| `public_reference` | str or null | no |  |
| `path` | str | yes | relative path under dataset/ (corpus/ or injects/batch_n/) |
| `batch` | int | yes |  |
| `text_sha256` | str | yes |  |
| `perturbations` | list[enum `Perturbation`] | no |  |

### `entities`

Named things claims are about.

- Primary key: `entity_id`
- Foreign keys: `parent_id` → `entities.entity_id`

| column | type | required | notes |
|---|---|---|---|
| `entity_id` | str | yes | typed readable prefix: ent_ actor/polity/problem set, loc_ location, inf_ infrastructure, unit_ unit, sys_ system, role_ organization role |
| `entity_type` | enum `EntityType` | yes |  |
| `canonical_name` | str | yes |  |
| `aliases` | list[str] | no |  |
| `parent_id` | str or null | no |  |
| `description` | str or null | no |  |

### `claims`

The world model (L3): sourced, bitemporal, ICD 203-typed assertions extracted from documents.

- Primary key: `claim_id`
- Foreign keys: `subject_id` → `entities.entity_id`; `object_id` → `entities.entity_id`; `source_id` → `sources.source_id`; `supersedes_claim_id` → `claims.claim_id`; `truth_claim_id` → `facts.fact_id`
- Computed columns: `confidence`

| column | type | required | notes |
|---|---|---|---|
| `subject_id` | str | yes |  |
| `predicate` | enum `Predicate` | yes |  |
| `object_id` | str or null | no |  |
| `value` | bool or int or float or str or null | no |  |
| `value_type` | enum `ValueType` | yes |  |
| `unit` | str or null | no |  |
| `valid_from` | date | yes |  |
| `valid_to` | date or null | no |  |
| `estimative` | bool | no |  |
| `likelihood_icd203` | enum `LikelihoodICD203` or null | no |  |
| `confidence_icd203` | enum `ConfidenceICD203` | yes |  |
| `confidence` | float | yes | DERIVED per SCHEMA.md §confidence |
| `claim_id` | str | yes |  |
| `source_id` | str | yes |  |
| `span_start` | int | yes |  |
| `span_end` | int | yes |  |
| `asserted_at` | date | yes | transaction time; = source.published_at unless the doc quotes an older report |
| `likelihood_surface_term` | str or null | no | the likelihood phrase as written in the span (may be a non-ICD synonym under hedge_drift) |
| `status` | enum `ClaimStatus` | yes |  |
| `supersedes_claim_id` | str or null | no |  |
| `truth_claim_id` | str or null | no | truth/ only: the fact this claim instantiates |

### `facts`

truth/ only: the canonical world documents are rendered from; change events are supersedes_fact_id pairs.

- Primary key: `fact_id`
- Foreign keys: `subject_id` → `entities.entity_id`; `object_id` → `entities.entity_id`; `supersedes_fact_id` → `facts.fact_id`
- Computed columns: `confidence`
- truth/ only.

| column | type | required | notes |
|---|---|---|---|
| `subject_id` | str | yes |  |
| `predicate` | enum `Predicate` | yes |  |
| `object_id` | str or null | no |  |
| `value` | bool or int or float or str or null | no |  |
| `value_type` | enum `ValueType` | yes |  |
| `unit` | str or null | no |  |
| `valid_from` | date | yes |  |
| `valid_to` | date or null | no |  |
| `estimative` | bool | no |  |
| `likelihood_icd203` | enum `LikelihoodICD203` or null | no |  |
| `confidence_icd203` | enum `ConfidenceICD203` | yes |  |
| `confidence` | float | yes | DERIVED per SCHEMA.md §confidence |
| `fact_id` | str | yes |  |
| `supersedes_fact_id` | str or null | no | the earlier fact on the same (subject, predicate) this one replaces: together they are a change event |
| `first_asserted_batch` | int | yes | 0 = asserted by a T0 document; n = first asserted by inject batch n |

### `guidance`

JSPS products (real product types, fictional content) and their nesting.

- Primary key: `guidance_id`
- Foreign keys: `parent_guidance_id` → `guidance.guidance_id`; `source_id` → `sources.source_id`

| column | type | required | notes |
|---|---|---|---|
| `guidance_id` | str | yes |  |
| `product_type` | enum `GuidanceProductType` | yes |  |
| `title` | str | yes |  |
| `issuing_role` | str | yes | real role that issues this product type: President (NSS), SecWar (NDS), CJCS (NMS, JSCP), SecWar-approved/CJCS-endorsed (GCP), CCDR (CCP) |
| `parent_guidance_id` | str or null | no |  |
| `objective_ids` | list[str] | no |  |
| `source_id` | str or null | no | the rendered guidance document (set once corpus is rendered) |

### `games`

Game form G = <N, S, A, T, O, H>: the operational environment, not the strategy.

- Primary key: `game_id`

| column | type | required | notes |
|---|---|---|---|
| `game_id` | str | yes |  |
| `name` | str | yes |  |
| `actor_ids` | list[str] | yes |  |
| `horizon` | int | yes |  |
| `horizon_map` | list[HorizonMapEntry] | yes |  |
| `state_variables` | list[StateVariable] | yes |  |
| `observables` | list[Observable] | yes |  |

### `actions`

Tactics A_i: named, costed, preconditioned.

- Primary key: `action_id`
- Foreign keys: `game_id` → `games.game_id`; `actor_id` → `entities.entity_id`

| column | type | required | notes |
|---|---|---|---|
| `action_id` | str | yes |  |
| `game_id` | str | yes |  |
| `actor_id` | str | yes |  |
| `name` | str | yes |  |
| `tactic_class` | enum `TacticClass` | yes |  |
| `line_of_effort` | str | yes |  |
| `mechanism` | str | yes | primary mechanism for mission accomplishment (JP 5-0 Ch. III §(q)4.d), e.g. deny, delay, deter_by_denial, defeat, influence, sustain |
| `cost` | dict[str → float] | no | resource_id -> cost c(a) |
| `preconditions` | bool or VarCmp or AllOf or AnyOf | no |  |
| `effects` | list[Effect] | no |  |

### `objectives`

Ends U: end states, objectives, effects (JP 5-0 Fig. IV-9).

- Primary key: `objective_id`
- Foreign keys: `game_id` → `games.game_id`; `actor_id` → `entities.entity_id`; `guidance_id` → `guidance.guidance_id`; `parent_objective_id` → `objectives.objective_id`

| column | type | required | notes |
|---|---|---|---|
| `objective_id` | str | yes |  |
| `game_id` | str | yes |  |
| `actor_id` | str | yes |  |
| `name` | str | yes |  |
| `kind` | enum `ObjectiveKind` | yes |  |
| `guidance_id` | str or null | no |  |
| `parent_objective_id` | str or null | no | effect -> objective -> end_state nesting (JP 5-0 Fig. IV-9) |
| `metric` | str | yes |  |
| `direction` | enum `Direction` | no |  |
| `aspiration` | float or null | no |  |
| `statement` | str or null | no | short active-voice phrase (JP 5-0 Ch. III §(11)(b)) |

### `resources`

Means M resource types.

- Primary key: `resource_id`
- Foreign keys: `game_id` → `games.game_id`

| column | type | required | notes |
|---|---|---|---|
| `resource_id` | str | yes |  |
| `game_id` | str | yes |  |
| `name` | str | yes |  |
| `unit` | str | yes |  |

### `strategies`

A strategy sigma = <U, Pi, M, Theta, Sigma_-i, rho>; a JP 5-0 COA nested in the JSPS.

- Primary key: `strategy_id`
- Foreign keys: `game_id` → `games.game_id`; `actor_id` → `entities.entity_id`; `guidance_source` → `guidance.guidance_id`; `end_state_objective_id` → `objectives.objective_id`; `opponent_model_id` → `opponent_models.opponent_model_id`
- Computed columns: `validity`, `status`, `aspiration`, `value`, `value_ci`, `robustness`, `world_version`

| column | type | required | notes |
|---|---|---|---|
| `strategy_id` | str | yes |  |
| `game_id` | str | yes |  |
| `actor_id` | str | yes |  |
| `name` | str | yes |  |
| `summary` | str | yes |  |
| `echelon` | enum `Echelon` | yes |  |
| `guidance_source` | str or null | no | FK guidance; the JSPS product this COA descends from |
| `adversary_coa_label` | enum `AdversaryCoaLabel` or null | no | set on opponent (Red) strategies only |
| `mission_who` | str | yes |  |
| `mission_what` | str | yes |  |
| `mission_when` | str | yes |  |
| `mission_where` | str | yes |  |
| `mission_why` | str | yes |  |
| `end_state_objective_id` | str | yes |  |
| `constraints` | list[str] | no | 'must do' (JP 5-0 Ch. III §(7)(a)) |
| `restraints` | list[str] | no | 'cannot do' (JP 5-0 Ch. III §(7)(b)) |
| `main_effort` | str | yes | line of effort that is the main effort (distinguishability dim main_effort) |
| `sequencing` | enum `Sequencing` | yes |  |
| `task_org` | list[str] | no | unit entity ids in the task organization |
| `reserve_policy` | str | yes | how reserves are used (distinguishability dim reserves) |
| `mitigates_he_ids` | list[str] | no | harmful events this COA mitigates (acceptable test) |
| `risk_functional` | enum `RiskFunctional` | yes |  |
| `risk_alpha` | float or null | no |  |
| `opponent_model_id` | str | yes |  |
| `theory_of_victory` | list[str] | no | ordered dependency edge ids: action -enables-> claim -supports-> objective ... end_state |
| `validity` | Validity or null | no |  |
| `status` | enum `StrategyStatus` or null | no |  |
| `aspiration` | float or null | no | COMPUTED w·τ over the strategy's objectives |
| `value` | float or null | no |  |
| `value_ci` | list[float] or null | no |  |
| `robustness` | float or null | no |  |
| `world_version` | int or null | no |  |

### `strategy_objectives`

Weight vector w = COA evaluation criteria weights (JP 5-0 App. F).

- Primary key: `strategy_id`, `objective_id`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `objective_id` → `objectives.objective_id`
- Computed columns: `rating_1_to_3`

| column | type | required | notes |
|---|---|---|---|
| `strategy_id` | str | yes |  |
| `objective_id` | str | yes |  |
| `weight` | float | yes |  |
| `rating_1_to_3` | int or null | no | COMPUTED rank of E[u_k] among valid strategies of the same actor (3 = best) |

### `strategy_resources`

Budget m.

- Primary key: `strategy_id`, `resource_id`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `resource_id` → `resources.resource_id`

| column | type | required | notes |
|---|---|---|---|
| `strategy_id` | str | yes |  |
| `resource_id` | str | yes |  |
| `budget` | float | yes |  |

### `policy_rules`

Policy Pi: ordered (condition, action, probability) rules; the condition is the information set.

- Primary key: `rule_id`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `action_id` → `actions.action_id`; `decision_point_id` → `decision_points.dp_id`

| column | type | required | notes |
|---|---|---|---|
| `rule_id` | str | yes |  |
| `strategy_id` | str | yes |  |
| `priority` | int | yes | lower fires first; equal priority + identical condition = one mixed distribution |
| `condition` | bool or VarCmp or AllOf or AnyOf | yes |  |
| `action_id` | str | yes |  |
| `probability` | float | yes |  |
| `periods` | list[int] or null | no | periods in which the rule is active; null = all periods (used by the feasible test) |
| `rationale_claim_ids` | list[str] | no |  |
| `decision_point_id` | str or null | no |  |

### `decision_points`

Decision points with their branch rules (JP 5-0 Ch. IV).

- Primary key: `dp_id`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `pir_id` → `pirs.pir_id`

| column | type | required | notes |
|---|---|---|---|
| `dp_id` | str | yes |  |
| `strategy_id` | str | yes |  |
| `name` | str | yes |  |
| `condition` | bool or VarCmp or AllOf or AnyOf | yes |  |
| `branch_rule_ids` | list[str] | yes |  |
| `pir_id` | str or null | no | PIR tied to this decision point (JP 5-0 Ch. IV §(b)3) |
| `latest_period` | int or null | no | latest period at which the decision can be made |

### `opponent_models`

Sigma_-i: distribution over the opponent's strategies.

- Primary key: `opponent_model_id`
- Foreign keys: `actor_id` → `entities.entity_id`

| column | type | required | notes |
|---|---|---|---|
| `opponent_model_id` | str | yes |  |
| `actor_id` | str | yes | the opponent whose strategies are mixed |
| `distribution` | list[OpponentMix] | yes |  |

### `payoffs`

truth/: the finite Bayesian game payoff tensor u(sigma_i, sigma_-i, theta).

- Primary key: `strategy_id`, `opponent_strategy_id`, `world`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `opponent_strategy_id` → `strategies.strategy_id`
- truth/ only.

| column | type | required | notes |
|---|---|---|---|
| `strategy_id` | str | yes |  |
| `opponent_strategy_id` | str | yes |  |
| `world` | str | yes |  |
| `utility` | list[float] | yes |  |

### `distinguishability`

COMPUTED pairwise JP 5-0 distinguishability dimensions.

- Primary key: `strategy_a`, `strategy_b`
- Foreign keys: `strategy_a` → `strategies.strategy_id`; `strategy_b` → `strategies.strategy_id`
- Computed columns: `dims_differing`, `pass`

| column | type | required | notes |
|---|---|---|---|
| `strategy_a` | str | yes |  |
| `strategy_b` | str | yes |  |
| `dims_differing` | list[enum `DistinguishDim`] | yes |  |
| `pass` | bool | yes | COMPUTED: len(dims_differing) >= 2 |

### `assumptions`

Theta: planning assumptions as predicates over world-model claims.

- Primary key: `assumption_id`
- Foreign keys: `strategy_id` → `strategies.strategy_id`; `subject_id` → `entities.entity_id`
- Computed columns: `p_holds`, `status`, `sensitivity`, `evpi`

| column | type | required | notes |
|---|---|---|---|
| `assumption_id` | str | yes |  |
| `strategy_id` | str | yes |  |
| `index_k` | int | yes |  |
| `statement` | str | yes |  |
| `subject_id` | str | yes |  |
| `predicate` | enum `Predicate` | yes |  |
| `tolerance` | Tolerance | yes |  |
| `role` | enum `AssumptionRole` | yes |  |
| `jp50_logical` | bool | yes |  |
| `jp50_realistic` | bool | yes |  |
| `jp50_essential` | bool | yes |  |
| `origin` | enum `AssumptionOrigin` | yes |  |
| `in_decision_matrix` | bool | no |  |
| `p_holds` | float or null | no |  |
| `status` | enum `AssumptionStatus` or null | no |  |
| `sensitivity` | float or null | no |  |
| `evpi` | float or null | no |  |

### `dependencies`

Typed dependency graph over claims, assumptions, strategies, actions, objectives, harmful events.

- Primary key: `edge_id`
- Polymorphic foreign keys: `from_id` resolved by `from_type`; `to_id` resolved by `to_type`

| column | type | required | notes |
|---|---|---|---|
| `edge_id` | str | yes |  |
| `from_type` | enum `NodeType` | yes |  |
| `from_id` | str | yes |  |
| `to_type` | enum `NodeType` | yes |  |
| `to_id` | str | yes |  |
| `kind` | enum `DependencyKind` | yes |  |
| `weight` | float | yes |  |
| `mechanism` | str | yes |  |
| `evidence_claim_ids` | list[str] | no |  |

### `problem_sets`

JRAM tier-0 problem sets with their risk context statement fields.

- Primary key: `problem_set_id`
- Foreign keys: `entity_id` → `entities.entity_id`; `risk_context_source_id` → `sources.source_id`

| column | type | required | notes |
|---|---|---|---|
| `problem_set_id` | str | yes |  |
| `entity_id` | str | yes |  |
| `name` | str | yes |  |
| `tier` | int | yes |  |
| `thing_of_value_ids` | list[str] | yes | FK objectives (things of value, JRAM Encl. B §1.a) |
| `risk_owner_role` | str | yes |  |
| `risk_context_source_id` | str or null | no | FK sources with doc_type risk_context |
| `tolerance_statement` | str | yes |  |
| `strategic_context` | str | yes | Fig. 3 para a |
| `scope_and_boundaries` | str | yes | Fig. 3 para c |
| `assumptions_and_constraints` | str | yes | Fig. 3 para e |
| `expected_outputs` | str | yes | Fig. 3 para f, second sentence |

### `harmful_events`

JRAM harmful events (Pillar 1) with consequence inputs.

- Primary key: `he_id`
- Foreign keys: `problem_set_id` → `problem_sets.problem_set_id`; `thing_of_value_id` → `objectives.objective_id`; `beneficial_counterpart_he_id` → `harmful_events.he_id`

| column | type | required | notes |
|---|---|---|---|
| `he_id` | str | yes |  |
| `problem_set_id` | str | yes |  |
| `statement` | str | yes | the harmful event phrase used in the Fig. 11 [harmful event] slot |
| `thing_of_value_id` | str | yes | FK objectives |
| `risk_type` | enum `RiskType` | yes |  |
| `risk_subset` | enum `RiskSubset` or null | no |  |
| `strategic_value` | enum `StrategicValue` or null | no |  |
| `damage_degree` | enum `DamageDegree` or null | no |  |
| `fig28_row` | str or null | no |  |
| `fig28_cell` | enum `CLevel` or null | no | MR only: the Fig. 28 cell (column) of fig28_row the assessor expects; MR consequence level |
| `base_p` | float | yes | baseline probability before drivers and cascade |
| `condition` | enum `HarmCondition` | yes |  |
| `posture_subject_ids` | list[str] | no | Blue entities whose posture_state claims decide the forced choice (JRAM Encl. C §4.d) |
| `beneficial_counterpart_he_id` | str or null | no |  |
| `beneficial_statement` | str or null | no | for opportunity statements (Fig. 12): the beneficial event phrase; set on the counterpart |
| `key_actions` | str or null | no | Fig. 12 [key actions/conditions] slot |

### `risk_sources`

Sources of risk: threats and hazards.

- Primary key: `rs_id`
- Foreign keys: `he_id` → `harmful_events.he_id`; `entity_id` → `entities.entity_id`

| column | type | required | notes |
|---|---|---|---|
| `rs_id` | str | yes |  |
| `he_id` | str | yes |  |
| `source_kind` | enum `SourceKind` | yes |  |
| `entity_id` | str | yes |  |
| `description` | str | yes |  |

### `risk_drivers`

Drivers of risk: claim terms that move P_raw.

- Primary key: `driver_id`
- Foreign keys: `he_id` → `harmful_events.he_id`; `claim_subject_id` → `entities.entity_id`

| column | type | required | notes |
|---|---|---|---|
| `driver_id` | str | yes |  |
| `he_id` | str | yes |  |
| `claim_subject_id` | str | yes |  |
| `claim_predicate` | enum `Predicate` | yes |  |
| `driver_kind` | enum `DriverKind` | yes |  |
| `locus` | enum `DriverLocus` | yes |  |
| `op` | enum `CmpOp` | yes |  |
| `value` | Any | no |  |
| `delta` | float | yes | added to P_raw when the current approved claim satisfies (op, value) |
| `horizons` | list[literal 'near' or 'mid' or 'long'] | no |  |
| `label` | str | yes | short phrase for the Fig. 11 [key drivers] slot |

### `risk_assessments`

COMPUTED Pillar-2 assessment per harmful event per horizon, with Fig. 11 statement.

- Primary key: `he_id`, `jsps_horizon`, `world_version`
- Foreign keys: `he_id` → `harmful_events.he_id`; `dominant_driver_id` → `risk_drivers.driver_id`
- Computed columns: `p_raw`, `p_level`, `forced_choice_applied`, `posture_rationale`, `dominant_driver_id`, `active_driver_ids`, `c_level`, `risk_level`, `trend`, `statement_text`

| column | type | required | notes |
|---|---|---|---|
| `he_id` | str | yes |  |
| `jsps_horizon` | literal 'near' or 'mid' or 'long' | yes |  |
| `world_version` | int | yes |  |
| `p_raw` | float | yes |  |
| `p_level` | enum `PLevel` | yes |  |
| `forced_choice_applied` | bool | no |  |
| `posture_rationale` | str or null | no |  |
| `dominant_driver_id` | str or null | no |  |
| `active_driver_ids` | list[str] | no |  |
| `c_level` | enum `CLevel` | yes |  |
| `risk_level` | enum `RiskLevel` | yes |  |
| `trend` | enum `Trend` | yes |  |
| `statement_text` | str | yes |  |

### `problem_set_assessments`

COMPUTED aggregated (Fig. 5) risk per problem set per horizon.

- Primary key: `problem_set_id`, `jsps_horizon`, `world_version`
- Foreign keys: `problem_set_id` → `problem_sets.problem_set_id`
- Computed columns: `max_risk_level`, `he_ids`, `aggregated_statement_text`

| column | type | required | notes |
|---|---|---|---|
| `problem_set_id` | str | yes |  |
| `jsps_horizon` | literal 'near' or 'mid' or 'long' | yes |  |
| `world_version` | int | yes |  |
| `max_risk_level` | enum `RiskLevel` | yes |  |
| `he_ids` | list[str] | yes |  |
| `aggregated_statement_text` | str | yes | JRAM Fig. 5 aggregated (complex) risk statement |

### `escalation_edges`

Cascade DAG between harmful events with conditional lift.

- Primary key: `edge_id`
- Foreign keys: `from_he_id` → `harmful_events.he_id`; `to_he_id` → `harmful_events.he_id`

| column | type | required | notes |
|---|---|---|---|
| `edge_id` | str | yes |  |
| `from_he_id` | str | yes |  |
| `to_he_id` | str | yes |  |
| `lift` | float | yes |  |
| `mechanism` | str | yes |  |
| `evidence_claim_ids` | list[str] | no |  |

### `pirs`

Priority intelligence requirements (JP 2-01 Ch. III §5.a).

- Primary key: `pir_id`

| column | type | required | notes |
|---|---|---|---|
| `pir_id` | str | yes |  |
| `statement` | str | yes |  |
| `commander_role` | str | yes |  |
| `priority_rank` | int | yes |  |
| `decision_point_ids` | list[str] | no |  |

### `collection_requirements`

Gaps as JP 2-01 collection requirements with computed EVPI priority and JIPCL rank.

- Primary key: `req_id`
- Foreign keys: `pir_id` → `pirs.pir_id`; `subject_id` → `entities.entity_id`; `assumption_id` → `assumptions.assumption_id`; `answered_by_source_id` → `sources.source_id`
- Computed columns: `priority`, `jipcl_rank`

| column | type | required | notes |
|---|---|---|---|
| `req_id` | str | yes |  |
| `pir_id` | str | yes |  |
| `eei` | str | yes |  |
| `indicators` | list[str] | yes |  |
| `sir` | str | yes |  |
| `gap_type` | enum `GapType` | yes |  |
| `subject_id` | str | yes |  |
| `predicate` | enum `Predicate` | yes |  |
| `assumption_id` | str or null | no | assumption whose grounding claim this gap resolves (priority = EVPI_k) |
| `rfi_disposition` | enum `RfiDisposition` | yes |  |
| `routing` | str | yes |  |
| `ltiov` | date | yes |  |
| `created_at` | date | yes |  |
| `status` | enum `ReqStatus` | yes |  |
| `answered_by_source_id` | str or null | no |  |
| `priority` | float or null | no |  |
| `jipcl_rank` | int or null | no |  |

### `injects/batch_n/manifest.json`

Documents, change events and COMPUTED expected effects of one inject batch (schema `inject_manifest.json`).

| column | type | required | notes |
|---|---|---|---|
| `batch` | int | yes |  |
| `as_of` | date | yes |  |
| `docs` | list[str] | yes |  |
| `change_events` | list[ChangeEvent] | yes |  |
| `expected_effects` | ExpectedEffects | yes |  |

`ChangeEvent`:

| column | type | required | notes |
|---|---|---|---|
| `fact_id_old` | str or null | yes |  |
| `fact_id_new` | str | yes |  |
| `subject_id` | str | yes |  |
| `predicate` | enum `Predicate` | yes |  |
| `old_value` | bool or int or float or str or null | no |  |
| `new_value` | bool or int or float or str or null | no |  |

`ExpectedEffects`:

| column | type | required | notes |
|---|---|---|---|
| `assumptions_changed` | list[AssumptionChange] | yes |  |
| `strategies_restated` | list[StrategyRestated] | yes |  |
| `ranking_before` | list[str] | yes |  |
| `ranking_after` | list[str] | yes |  |
| `requirements_closed` | list[str] | yes |  |
| `problem_sets_moved` | list[ProblemSetMoved] | yes |  |
| `risk_assessments_changed` | list[RiskAssessmentChanged] | yes |  |
| `validity_changed` | list[ValidityChanged] | yes |  |
| `jipcl_changed` | list[JipclChanged] | yes |  |

## 5. Invariants (enforced by `gen/validate.py`; `python -m gen check`)

1. Referential integrity on every FK (scalar, list and polymorphic) and PK uniqueness.
2. Every claim's `[span_start, span_end)` lies inside its source text and the span mentions the
   subject (canonical name or alias), the object, or the value.
3. Every fact is instantiated by ≥ 1 claim (`truth_claim_id`) at T0 or in an inject; every
   intelligence-bearing document (reference_entry, sitrep, news, message_traffic, tabular,
   assessment) yields ≥ 1 claim. Products that carry no world-model facts (risk_context,
   collection_plan, coa_statement, guidance) are exempt.
4. Approved claims on the same (subject, predicate) whose valid windows overlap instantiate the
   same fact (no conflicting approved claims); `supersedes_claim_id` chains are acyclic.
5. `policy_rules`: for each (strategy, condition, priority) group, probabilities sum to 1 ± 1e-9.
6. `strategy_objectives` weights sum to 1 per strategy; every strategy has weights; `opponent_models`
   distributions sum to 1.
7. `payoffs` covers every (strategy, opponent strategy in the strategy's opponent model, world)
   triple exactly once, with a utility vector of the actor's objective count.
8. `escalation_edges` is a DAG.
9. Every assumption's grounding (subject, predicate) has ≥ 1 fact.
10. Recomputing every computed column from truth (`eval/engine.py::recompute`) reproduces the
    stored value to 1e-9.
11. Every rendered product begins and ends with `UNCLASSIFIED` and carries the synthetic caveat on
    line 2; no other marking string appears (denylist regex in `eval/style_check.py`).
12. No sentence in any product contains both an ICD 203 likelihood term and a confidence term.
13. No product contains both an ICD 203 likelihood term and a JRAM probability term; the one
    deliberate `mixed_scale` negative example must be flagged by `eval/style_check.py`.
14. Every `risk_assessments.statement_text` matches the Fig. 11 slot order (regex with named
    groups) and is ≤ 90 words.
15. Every `assumptions.in_decision_matrix = true`; every rendered COA statement lists every
    assumption id its strategy requires.
16. Every strategy has all five `validity` entries and a status; invalid strategies are absent from
    every rendered comparison table.
17. Every rendered comparison table is followed by the App. F caution sentence.
18. Every `MSR` harmful event has `strategic_value` and `damage_degree`; every `MR` row has
    `risk_subset`, `fig28_row` and `fig28_cell`.
19. Every `risk_assessments` row produced by the forced-choice rule has non-null `posture_rationale`.
20. All acronyms used in products appear in `gen/styles/acronyms.yml`, are spelled out at first use,
    and are listed in the product's closing glossary; directive products use the CJCS paragraph
    scheme; dates follow §1A.3; intelligence products use no likelihood synonyms; length limits hold.

Additional gates run by `python -m gen check`: schema load (every row validates against its
model), reproducibility (regeneration with the seed is byte-identical), and, from P6 onward, the
evaluation harness scoring truth against truth at 1.0.
