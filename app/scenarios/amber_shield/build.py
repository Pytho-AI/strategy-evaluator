"""Assemble AMBER SHIELD, run the frozen dataset's reference evaluator over it, write truth/.

    python -m app.scenarios.amber_shield.build      # rebuild truth/*.jsonl and print row counts
    from app.scenarios.amber_shield.build import load, SCENARIO

`load()` is the entry point the API calls. It returns `{table_name: [row dict, ...]}` in exactly
the shape `dataset/eval/tables.py::TABLE_FILES` names, with every COMPUTED column filled by
`eval/engine.py::recompute` - the same function `dataset.load()` runs on the frozen dataset. The
build is fully deterministic (no RNG anywhere) so two runs are byte-identical.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

from . import payoffs as P
from . import placeholders as PH
from . import scenario as S
from ._dataset import eval_module, gen_module

TRUTH_DIR = Path(__file__).resolve().parent / "truth"

SCENARIO = {
    "id": "amber_shield",
    "name": "USEUCOM Operation AMBER SHIELD",
    "as_of": S.AS_OF,
    "marking": "UNCLASSIFIED — SYNTHETIC",
    "fiction_notice": (
        "For exercise and demonstration use only. Not a real plan. Doctrine, product types and "
        "organizational roles are real and cited; every unit disposition, assumption, course of "
        "action, number and assessment is fictional."
    ),
}


# ---------------------------------------------------------------- dependency graph
def _dependencies(strategies: list[dict], assumptions: list[dict], rules: list[dict]) -> list[dict]:
    """The typed edges the theory-of-victory chain and assumption grounding need.

    action -enables-> waypoint claim -supports-> objective -supports-> end state, plus
    claim -grounds-> assumption and assumption -requires-> strategy.
    """
    edges: list[dict] = []
    end_state = {S.BLUE: "obj_end_state", S.RED: "obj_rus_end_state"}
    supports_edge: dict[str, str] = {}
    for key, objective_id in PH.TOV_OBJECTIVE.items():
        edge_id = f"dep_sup_{key}"
        supports_edge[objective_id] = edge_id
        edges.append(dict(edge_id=edge_id, from_type="claim", from_id=f"clm_ph_tov_{key}",
                          to_type="objective", to_id=objective_id, kind="supports", weight=0.6,
                          mechanism="the waypoint condition is evidence the objective is being met",
                          evidence_claim_ids=[f"clm_ph_tov_{key}"]))
    for objective_id in PH.TOV_OBJECTIVE.values():
        actor = next(o for o in S.OBJECTIVES if o[0] == objective_id)[1]
        edges.append(dict(edge_id=f"dep_end_{objective_id[4:]}", from_type="objective", from_id=objective_id,
                          to_type="objective", to_id=end_state[actor], kind="supports", weight=0.7,
                          mechanism="objective nests under the military end state (JP 5-0 Fig. IV-9)",
                          evidence_claim_ids=[]))
    rules_by_strategy: dict[str, list[dict]] = {}
    for r in rules:
        rules_by_strategy.setdefault(r["strategy_id"], []).append(r)
    for s in strategies:
        sid = s["strategy_id"]
        acts = [r["action_id"] for r in rules_by_strategy[sid]]
        objective_ids = [o for o in PH.TOV_OBJECTIVE.values()
                         if next(x for x in S.OBJECTIVES if x[0] == o)[1] == s["actor_id"]]
        tov = []
        for i, objective_id in enumerate(objective_ids):
            key = next(k for k, v in PH.TOV_OBJECTIVE.items() if v == objective_id)
            edge_id = f"dep_en_{sid[4:]}_{key}"
            edges.append(dict(edge_id=edge_id, from_type="action", from_id=acts[i % len(acts)],
                              to_type="claim", to_id=f"clm_ph_tov_{key}", kind="enables", weight=0.5,
                              mechanism="the action produces the waypoint condition", evidence_claim_ids=[]))
            tov.extend([edge_id, supports_edge[objective_id]])
        s["theory_of_victory"] = tov
    for a in assumptions:
        key = f"a{a['index_k'] + 1}" if a["strategy_id"].startswith("str_coa") else "rus_k0"
        edges.append(dict(edge_id=f"dep_gr_{a['assumption_id'][4:]}", from_type="claim", from_id=f"clm_ph_{key}",
                          to_type="assumption", to_id=a["assumption_id"], kind="grounds", weight=0.8,
                          mechanism="the approved claim decides whether the assumption holds",
                          evidence_claim_ids=[f"clm_ph_{key}"]))
        edges.append(dict(edge_id=f"dep_rq_{a['assumption_id'][4:]}", from_type="assumption", from_id=a["assumption_id"],
                          to_type="strategy", to_id=a["strategy_id"], kind="requires", weight=0.7,
                          mechanism="the course of action depends on this assumption (COA_LIB deps)",
                          evidence_claim_ids=[]))
    return edges


# ---------------------------------------------------------------- assembly
def tables(as_of: date | None = None) -> dict[str, list[dict]]:
    """Every authored row, validated against the dataset's pydantic models, before recompute."""
    as_of = as_of or S.AS_OF
    engine = eval_module("engine")
    models = gen_module("models")

    strategies, sobj, sres, rules, dps, assumptions = S.strategy_rows()
    he_ids = PH.all_he_ids()
    for s in strategies:
        # HOOK (risk agent): replace with the harmful events this COA actually mitigates. While the
        # placeholders stand, every COA mitigates every placeholder event so the acceptable test is
        # decided by value against aspiration and not by an unowned High event.
        s["mitigates_he_ids"] = list(he_ids)
    edges = _dependencies(strategies, assumptions, rules)

    pir_rows = PH.pirs()
    by_pir: dict[str, list[str]] = {}
    for dp in dps:
        by_pir.setdefault(dp["pir_id"], []).append(dp["dp_id"])
    for p in pir_rows:
        p["decision_point_ids"] = sorted(by_pir.get(p["pir_id"], []))

    # Bind the placeholder collection requirements to real assumption rows.
    assumption_ids = {a["assumption_id"] for a in assumptions}
    reqs = PH.collection_requirements()
    for r in reqs:
        if r["assumption_id"] and r["assumption_id"] not in assumption_ids:
            stem = r["assumption_id"].rsplit("_coa_", 1)[0]
            match = sorted(a for a in assumption_ids if a.startswith(stem + "_"))
            r["assumption_id"] = match[0] if match else None

    t: dict[str, list[dict]] = {
        "sources": PH.SOURCES,
        "entities": S.entities(),
        "claims": PH.claims(),
        "facts": PH.facts(),
        "guidance": S.guidance(),
        "games": S.games(),
        "actions": S.actions(),
        "objectives": S.objectives(),
        "resources": S.resources(),
        "strategies": strategies,
        "strategy_objectives": sobj,
        "strategy_resources": sres,
        "policy_rules": rules,
        "decision_points": dps,
        "opponent_models": S.opponent_models(),
        "payoffs": [],
        "distinguishability": [],
        "assumptions": assumptions,
        "dependencies": edges,
        "problem_sets": PH.problem_sets(),
        "harmful_events": PH.harmful_events(),
        "risk_sources": PH.risk_sources(),
        "risk_drivers": PH.risk_drivers(),
        "risk_assessments": [],
        "problem_set_assessments": [],
        "escalation_edges": PH.escalation_edges(),
        "pirs": pir_rows,
        "collection_requirements": reqs,
    }
    t["payoffs"] = P.build(engine.objective_order(t, S.GAME_ID, S.BLUE),
                           engine.objective_order(t, S.GAME_ID, S.RED))

    # Validate every row against its model, and normalize to the model's own JSON shape.
    for spec in models.TABLES:
        t[spec.name] = [spec.model(**row).model_dump(mode="json", by_alias=True) for row in t[spec.name]]
    return t


def load(as_of: date | None = None, *, through_batch: int = 0) -> dict[str, list[dict]]:
    """The API entry point: authored rows with every computed column filled by the reference engine.

    `through_batch` is accepted because `app/backend/scenarios.py::PackageAdapter` calls
    `load(through_batch=batch)`. There are no injects yet, so batch 0 is the only batch.
    """
    if through_batch not in BATCHES:
        raise ValueError(f"amber_shield has no batch {through_batch}; it loads {list(BATCHES)}")
    as_of = as_of or S.AS_OF
    recompute = eval_module("engine").recompute
    return recompute(tables(as_of), as_of, S.WORLD_VERSION)


# ---------------------------------------------------------------- registry surface
# What `app/backend/scenarios.py::PackageAdapter` reads off a scenario package. Kept here rather
# than in the registry so the scenario owns its own identity.
NAME = SCENARIO["name"]
MARKING = SCENARIO["marking"]
GAME_ID = S.GAME_ID
ACTOR_ID = S.BLUE
BATCHES = (0,)
#: `sources.path` is relative to this directory.
ROOT = Path(__file__).resolve().parent
#: The five UI comparison criteria, one objective each, in the UI's own order.
CRITERIA = list(S.CRITERIA)


def as_of(batch: int = 0) -> str:
    if batch not in BATCHES:
        raise ValueError(f"amber_shield has no batch {batch}; it loads {list(BATCHES)}")
    return S.AS_OF.isoformat()


# ---------------------------------------------------------------- output
def write(out_dir: Path | None = None, computed: dict[str, list[dict]] | None = None) -> dict[str, int]:
    out_dir = Path(out_dir or TRUTH_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = computed if computed is not None else load()
    counts = {}
    for name in eval_module("tables").TABLE_FILES:
        path = out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows[name]:
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
        counts[name] = len(rows[name])
    return counts


def main() -> int:
    start = time.perf_counter()
    authored = tables()
    t_authored = time.perf_counter() - start

    start = time.perf_counter()
    computed = eval_module("engine").recompute(authored, S.AS_OF, S.WORLD_VERSION)
    t_recompute = time.perf_counter() - start

    counts = write(computed=computed)
    print(f"{SCENARIO['name']} ({SCENARIO['id']})  as_of {SCENARIO['as_of']}  {SCENARIO['marking']}")
    print(f"worlds 2^{P.K_BLUE} = {2 ** P.K_BLUE} (Blue), 2^{P.K_RED} = {2 ** P.K_RED} (Red)")
    print(f"assemble {t_authored * 1000:.1f} ms   recompute {t_recompute * 1000:.1f} ms")
    print(f"truth -> {TRUTH_DIR}")
    width = max(len(n) for n in counts)
    for name, n in counts.items():
        print(f"  {name:<{width}}  {n}")
    print(f"  {'TOTAL':<{width}}  {sum(counts.values())}")
    print()
    order = eval_module("engine").objective_order(computed, S.GAME_ID, S.BLUE)
    print("Blue courses of action (value order):")
    blue = sorted((s for s in computed["strategies"] if s["actor_id"] == S.BLUE), key=lambda s: -s["value"])
    for s in blue:
        tests = " ".join(f"{k[:4]}{'+' if v['pass'] else '-'}" for k, v in s["validity"].items())
        print(f"  {s['strategy_id']}  V={s['value']:.4f}  asp={s['aspiration']:.4f}  {s['status']:<10} {tests}  {s['name']}")
    print(f"utility vector order: {order}")
    ks = sorted({a["index_k"] for a in computed["assumptions"] if a["strategy_id"].startswith("str_coa")})
    print("assumptions:")
    for k in ks:
        a = next(x for x in computed["assumptions"] if x["index_k"] == k and x["strategy_id"].startswith("str_coa"))
        print(f"  A{k + 1} p_holds={a['p_holds']:.5f} status={a['status']:<9} EVPI={a['evpi']:.6f} "
              f"realistic={a['jp50_realistic']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
