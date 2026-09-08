"""Generate schema/SCHEMA.md from the pydantic models (columns, PK, FKs, computed) plus the
hand-written contract sections (computed definitions, predicate vocabulary, enum sources,
invariants). Run: cd dataset && python -m gen.schema_md   (also run by `python -m gen schema`)."""
from __future__ import annotations

import inspect
from enum import Enum
from pathlib import Path
from typing import get_args, get_origin

from gen import vocab as V
from gen.models import TABLES, Manifest

OUT = Path(__file__).resolve().parents[1] / "schema" / "SCHEMA.md"


def _type_name(ann) -> str:
    import types
    from typing import Literal, Union

    origin = get_origin(ann)
    if origin is None:
        if isinstance(ann, type) and issubclass(ann, Enum):
            return f"enum `{ann.__name__}`"
        if isinstance(ann, type):
            return ann.__name__
        return str(ann).replace("typing.", "")
    args = get_args(ann)
    if origin is Union or origin is types.UnionType:
        parts = [a for a in args if a is not type(None)]
        s = " or ".join(_type_name(a) for a in parts)
        return s + (" or null" if len(parts) < len(args) else "")
    if origin is list:
        return f"list[{_type_name(args[0])}]" if args else "list"
    if origin is dict:
        return f"dict[{_type_name(args[0])} → {_type_name(args[1])}]"
    if origin is Literal:
        return "literal " + " or ".join(repr(a) for a in args)
    return str(ann).replace("typing.", "")


def columns_table(model) -> str:
    rows = ["| column | type | required | notes |", "|---|---|---|---|"]
    for name, f in model.model_fields.items():
        col = f.alias or name
        req = "yes" if f.is_required() else "no"
        note = f.description or ""
        rows.append(f"| `{col}` | {_type_name(f.annotation)} | {req} | {note} |")
    return "\n".join(rows)


def enum_section() -> str:
    out = ["| enum | values | doctrinal source | note |", "|---|---|---|---|"]
    for name, (src, note) in V.SOURCE.items():
        e = getattr(V, name)
        vals = ", ".join(f"`{m.value}`" for m in e)
        out.append(f"| `{name}` | {vals} | {src} | {note} |")
    return "\n".join(out)


def predicate_section() -> str:
    out = ["| predicate | value_type | unit | allowed values | meaning |", "|---|---|---|---|---|"]
    for p, (vt, unit, vals, meaning) in V.PREDICATES.items():
        out.append(f"| `{p}` | {vt} | {unit or '—'} | {', '.join(vals) if vals else '—'} | {meaning} |")
    return "\n".join(out)


HEAD = """# SCHEMA.md — the schema contract

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

"""

INVARIANTS = """
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
"""


def main() -> None:
    parts = [HEAD, predicate_section(), "\n\n## 3. Enumerations and their doctrinal sources\n\n", enum_section(), "\n\n## 4. Tables\n"]
    for t in TABLES:
        parts.append(f"\n### `{t.name}`\n\n{t.purpose}\n\n")
        parts.append(f"- Primary key: {', '.join(f'`{c}`' for c in t.pk)}\n")
        if t.fks:
            parts.append("- Foreign keys: " + "; ".join(f"`{c}` → `{r}`" for c, r in t.fks.items()) + "\n")
        if t.polymorphic_fks:
            parts.append("- Polymorphic foreign keys: " + "; ".join(f"`{c}` resolved by `{d}`" for c, d in t.polymorphic_fks.items()) + "\n")
        if t.computed:
            parts.append("- Computed columns: " + ", ".join(f"`{c}`" for c in t.computed) + "\n")
        if t.truth_only:
            parts.append("- truth/ only.\n")
        parts.append("\n" + columns_table(t.model) + "\n")
    parts.append("\n### `injects/batch_n/manifest.json`\n\nDocuments, change events and COMPUTED expected effects of one inject batch (schema `inject_manifest.json`).\n\n")
    parts.append(columns_table(Manifest) + "\n")
    for sub in ("ChangeEvent", "ExpectedEffects"):
        from gen import models as M
        parts.append(f"\n`{sub}`:\n\n" + columns_table(getattr(M, sub)) + "\n")
    parts.append(INVARIANTS)
    OUT.write_text("".join(parts), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
