"""Reference recomputation of every COMPUTED column from the truth tables (v2 §1 'mathematically
honest'; invariant 10). `recompute(tables, as_of, world_version)` returns new table dicts; the
generator stores its output and validate.py checks that a fresh recomputation reproduces it."""
from __future__ import annotations

import copy
from datetime import date
from typing import Optional

from eval import jram, validity
from eval import value as val
from eval.claimset import ClaimSet, horizon_window, satisfies

HORIZONS = ["near", "mid", "long"]


def _d(s):
    return s if isinstance(s, date) else date.fromisoformat(s)


def ordinal_rating(value: float, values: list[float]) -> int:
    """Map an objective contribution to 1–3 without breaking equal-value ties."""
    levels = sorted(set(values))
    if len(levels) == 1:
        return 3
    return 1 + round(2 * levels.index(value) / (len(levels) - 1))


def objective_order(tables: dict, game_id: str, actor_id: str) -> list[str]:
    """Utility-vector order: the actor's objectives of kind `objective` sorted by objective_id."""
    return sorted(o["objective_id"] for o in tables["objectives"] if o["game_id"] == game_id and o["actor_id"] == actor_id and o["kind"] == "objective")


def weights_for(tables: dict, sid: str, order: list[str]) -> list[float]:
    w = {so["objective_id"]: so["weight"] for so in tables["strategy_objectives"] if so["strategy_id"] == sid}
    return [w.get(o, 0.0) for o in order]


def opponent_dist(tables: dict, om_id: str) -> dict[str, float]:
    om = next(o for o in tables["opponent_models"] if o["opponent_model_id"] == om_id)
    return {m["strategy_id"]: m["probability"] for m in om["distribution"]}


def assumption_vector(tables: dict, game_id: str, actor_id: str, cs: ClaimSet, as_of: date) -> tuple[int, list[float], dict[int, list[dict]]]:
    """K and p_k per index_k for the actor's strategies (shared index_k -> one p_k)."""
    sids = {s["strategy_id"] for s in tables["strategies"] if s["game_id"] == game_id and s["actor_id"] == actor_id}
    by_k: dict[int, list[dict]] = {}
    for a in tables["assumptions"]:
        if a["strategy_id"] in sids:
            by_k.setdefault(a["index_k"], []).append(a)
    if not by_k:
        return 0, [], {}
    K = max(by_k) + 1
    p = [0.5] * K
    for k, rows in by_k.items():
        pk, _, _ = val.assumption_state(cs, rows[0], as_of)
        p[k] = pk
    return K, p, by_k


# ---------------------------------------------------------------- risk (JRAM)
def assess_risk(tables: dict, cs: ClaimSet, as_of: date, world_version: int) -> tuple[list[dict], list[dict]]:
    events = tables["harmful_events"]
    drivers_by_he: dict[str, list[dict]] = {}
    for d in tables["risk_drivers"]:
        drivers_by_he.setdefault(d["he_id"], []).append(d)
    edges = [(e["from_he_id"], e["to_he_id"], e["lift"]) for e in tables["escalation_edges"]]
    obj = {o["objective_id"]: o for o in tables["objectives"]}
    ent = {e["entity_id"]: e for e in tables["entities"]}
    per_h: dict[str, dict[str, dict]] = {h: {} for h in HORIZONS}
    for h in HORIZONS:
        start, end = horizon_window(as_of, h)
        base: dict[str, float] = {}
        meta: dict[str, dict] = {}
        for he in events:
            p = he["base_p"]
            active, dom, dom_delta = [], None, 0.0
            for d in drivers_by_he.get(he["he_id"], []):
                if h not in d.get("horizons", HORIZONS):
                    continue
                hits = [c for c in cs.in_window(d["claim_subject_id"], d["claim_predicate"], start, end, known_at=as_of)
                        if satisfies(cs.value_of(c), d["op"], d["value"])]
                if hits:
                    p += d["delta"]
                    active.append(d["driver_id"])
                    if abs(d["delta"]) > dom_delta:
                        dom, dom_delta = (d, hits), abs(d["delta"])
            base[he["he_id"]] = jram.clip_p(p)
            meta[he["he_id"]] = {"active": active, "dominant": dom}
        cascaded = jram.noisy_or_cascade(base, edges)
        for he in events:
            hid = he["he_id"]
            p_raw = cascaded[hid]
            p_level = jram.p_bin(p_raw)
            forced, rationale, dom_id = False, None, None
            dom = meta[hid]["dominant"]
            if dom is not None:
                d, hits = dom
                dom_id = d["driver_id"]
                latest = max(hits, key=lambda c: (c.get("asserted_at", c["valid_from"]), c["valid_from"]))
                if latest.get("likelihood_icd203") == "roughly_even_chance":
                    posture = []
                    for pid in he.get("posture_subject_ids", []):
                        pc = cs.current(pid, "posture_state", as_of)
                        if pc is not None:
                            posture.append((ent.get(pid, {}).get("canonical_name", pid), pc["value"]))
                    p_level, forced, rationale = jram.crosswalk("roughly_even_chance", posture)
            c_level = jram.msr_consequence(he["strategic_value"], he["damage_degree"]) if he["risk_type"] == "MSR" else jram.mr_consequence(he["fig28_row"], he["fig28_cell"])
            per_h[h][hid] = {
                "he_id": hid, "jsps_horizon": h, "world_version": world_version, "p_raw": round(p_raw, 6),
                "p_level": p_level, "forced_choice_applied": forced, "posture_rationale": rationale,
                "dominant_driver_id": dom_id, "active_driver_ids": meta[hid]["active"], "c_level": c_level,
                "risk_level": jram.risk_level(p_level, c_level), "trend": "flat", "statement_text": "",
            }
    # trend across horizons, then statements
    drv_label = {d["driver_id"]: d["label"] for d in tables["risk_drivers"]}
    rows: list[dict] = []
    for he in events:
        hid = he["he_id"]
        tr = jram.trend({h: per_h[h][hid]["p_raw"] for h in HORIZONS})
        tov = obj[he["thing_of_value_id"]]["name"]
        for h in HORIZONS:
            r = per_h[h][hid]
            r["trend"] = tr
            labels = [drv_label[d] for d in r["active_driver_ids"]][:3] or [d["label"] for d in drivers_by_he.get(hid, [])][:2]
            r["statement_text"] = jram.render_risk_statement(r["p_level"], he["statement"], h, labels, he["condition"],
                                                             r["c_level"], r["risk_level"], tr, he["risk_type"], he.get("risk_subset"), tov)
            rows.append(r)
    # problem-set aggregation (Fig. 5): max risk level over the set's events per horizon
    ps_rows: list[dict] = []
    for ps in tables["problem_sets"]:
        hes = [he for he in events if he["problem_set_id"] == ps["problem_set_id"]]
        tov = obj[ps["thing_of_value_ids"][0]]["name"] if ps.get("thing_of_value_ids") else ps["name"]
        for h in HORIZONS:
            lv = max((per_h[h][he["he_id"]]["risk_level"] for he in hes), key=jram.RISK_LEVELS.index, default="low")
            effect = "denied" if lv == "high" else "degraded"
            ps_rows.append({
                "problem_set_id": ps["problem_set_id"], "jsps_horizon": h, "world_version": world_version,
                "max_risk_level": lv, "he_ids": [he["he_id"] for he in hes],
                "aggregated_statement_text": jram.render_aggregated_statement(h, [he["statement"] for he in hes], f"protect {tov}", effect, lv, tov),
            })
    return rows, ps_rows


# ---------------------------------------------------------------- full recompute
def recompute(tables: dict, as_of: date, world_version: int, claims: Optional[list[dict]] = None) -> dict:
    """Returns deep-copied tables with every COMPUTED column filled from `claims` (default: tables['claims'])."""
    t = copy.deepcopy(tables)
    if claims is not None:
        t["claims"] = copy.deepcopy(claims)
    for c in t["claims"] + t["facts"]:
        c["confidence"] = val.derived_confidence(c["estimative"], c.get("likelihood_icd203"), c["confidence_icd203"])
    cs = ClaimSet(t["claims"])
    idx = val.PayoffIndex(t["payoffs"])
    actions = {a["action_id"]: a for a in t["actions"]}
    deps = {d["edge_id"]: d for d in t["dependencies"]}
    guidance = {g["guidance_id"]: g for g in t["guidance"]}
    games = {g["game_id"]: g for g in t["games"]}
    rules_by = {}
    for r in t["policy_rules"]:
        rules_by.setdefault(r["strategy_id"], []).append(r)
    dps_by = {}
    for d in t["decision_points"]:
        dps_by.setdefault(d["strategy_id"], []).append(d)
    budgets_by = {}
    for sr in t["strategy_resources"]:
        budgets_by.setdefault(sr["strategy_id"], {})[sr["resource_id"]] = sr["budget"]
    obj = {o["objective_id"]: o for o in t["objectives"]}

    # risk first (acceptable test needs it)
    ra, psa = assess_risk(t, cs, as_of, world_version)
    t["risk_assessments"], t["problem_set_assessments"] = ra, psa
    events = {he["he_id"]: he for he in t["harmful_events"]}
    high_mr = sorted({r["he_id"] for r in ra if r["risk_level"] == "high" and events[r["he_id"]]["risk_type"] == "MR"})

    dist_rows: list[dict] = []
    for (game_id, actor_id) in sorted({(s["game_id"], s["actor_id"]) for s in t["strategies"]}):
        strategies = [s for s in t["strategies"] if s["game_id"] == game_id and s["actor_id"] == actor_id]
        relevant_high = [h for h in high_mr
                         if (obj[events[h]["thing_of_value_id"]]["game_id"], obj[events[h]["thing_of_value_id"]]["actor_id"]) == (game_id, actor_id)]
        order = objective_order(t, game_id, actor_id)
        K, p, by_k = assumption_vector(t, game_id, actor_id, cs, as_of)
        weights = {s["strategy_id"]: weights_for(t, s["strategy_id"], order) for s in strategies}
        opps = {s["strategy_id"]: opponent_dist(t, s["opponent_model_id"]) for s in strategies}
        # assumptions
        for k, rows in by_k.items():
            for a in rows:
                pk, st, _ = val.assumption_state(cs, a, as_of)
                a["p_holds"], a["status"] = pk, st
                s = next(x for x in strategies if x["strategy_id"] == a["strategy_id"])
                a["sensitivity"] = round(val.sensitivity(s["strategy_id"], k, idx, weights[s["strategy_id"]], opps[s["strategy_id"]], p, K, s["risk_functional"], s.get("risk_alpha")), 9)
        # strategies
        for s in strategies:
            sid = s["strategy_id"]
            s["aspiration"] = round(sum(w * (obj[o].get("aspiration") or 0.0) for o, w in zip(order, weights[sid])), 9)
            s["value"] = round(val.value(sid, idx, weights[sid], opps[sid], p, K, s["risk_functional"], s.get("risk_alpha")), 9)
            s["value_ci"] = [round(x, 9) for x in val.value_range(sid, idx, weights[sid], opps[sid], p, K)]
            s["robustness"] = round(val.robustness(sid, idx, weights[sid], opps[sid], K), 9)
            s["world_version"] = world_version
            g = guidance.get(s.get("guidance_source"))
            if g is not None:  # the guidance objectives that belong to this actor
                g = dict(g, objective_ids=[o for o in g.get("objective_ids", []) if obj[o]["actor_id"] == actor_id])
            ok_s, ev_s = validity.test_suitable(s, g, deps, rules_by.get(sid, []))
            ok_f, ev_f = validity.test_feasible(s, rules_by.get(sid, []), actions, budgets_by.get(sid, {}), games[game_id]["horizon"])
            unmit = [h for h in relevant_high if h not in set(s.get("mitigates_he_ids", []))]
            ok_a, ev_a = validity.test_acceptable(s["value"], s["aspiration"], unmit)
            ok_d, ev_d, rows = validity.test_distinguishable(s, [o for o in strategies if o["strategy_id"] != sid], rules_by, actions)
            dist_rows.extend(rows)
            ok_c, ev_c = validity.test_complete(s, rules_by.get(sid, []), dps_by.get(sid, []))
            s["validity"] = {
                "suitable": {"pass": ok_s, "evidence": ev_s}, "feasible": {"pass": ok_f, "evidence": ev_f},
                "acceptable": {"pass": ok_a, "evidence": ev_a}, "distinguishable": {"pass": ok_d, "evidence": ev_d},
                "complete": {"pass": ok_c, "evidence": ev_c},
            }
            s["status"] = "infeasible" if not ok_f else ("valid" if all([ok_s, ok_a, ok_d, ok_c]) else "invalid")
        # Learning can change aspiration acceptance, but cannot repair missing guidance,
        # resources, policy structure, or an unmitigated High event.
        candidates = [s for s in strategies
                      if all(s["validity"][test]["pass"] for test in ("suitable", "feasible", "distinguishable", "complete"))
                      and not set(relevant_high).difference(s.get("mitigates_he_ids", []))]
        for k, rows in by_k.items():
            price = round(val.evpi(k, candidates, idx, weights, opps, p, K), 9)
            for a in rows:
                a["evpi"] = price
        # App. F ratings: rank of E[u_k] among the actor's valid strategies (3 = best)
        valid = [s for s in strategies if s["status"] == "valid"]
        wp = val.conditioned_world_probs(p, K)
        contrib = {}
        for s in valid:
            sid = s["strategy_id"]
            e = [0.0] * len(order)
            for world, pw in wp.items():
                for osid, q in opps[sid].items():
                    u = idx.get(sid, osid, world)
                    for i in range(len(order)):
                        e[i] += pw * q * u[i]
            contrib[sid] = e
        for i, oid in enumerate(order):
            valid_values = [contrib[s["strategy_id"]][i] for s in valid]
            for s in strategies:
                so = next((x for x in t["strategy_objectives"] if x["strategy_id"] == s["strategy_id"] and x["objective_id"] == oid), None)
                if so is None:
                    continue
                if s in valid:
                    so["rating_1_to_3"] = ordinal_rating(contrib[s["strategy_id"]][i], valid_values)
                else:
                    so["rating_1_to_3"] = 1
    t["distinguishability"] = dist_rows

    # collection requirements: priority and JIPCL rank
    asm = {a["assumption_id"]: a for a in t["assumptions"]}
    deg: dict[str, int] = {}
    for d in t["dependencies"]:
        for typ, nid in ((d["from_type"], d["from_id"]), (d["to_type"], d["to_id"])):
            if typ == "claim":
                deg[nid] = deg.get(nid, 0) + 1
    for r in t["collection_requirements"]:
        if _d(r["created_at"]) > as_of:
            r["priority"], r["jipcl_rank"] = None, None
            continue
        a = asm.get(r.get("assumption_id") or "")
        if a is not None and a.get("evpi") is not None:
            r["priority"] = round(a["evpi"], 9)
        else:
            c = cs.current(r["subject_id"], r["predicate"], as_of)
            conf = c["confidence"] if c else 0.0
            d = deg.get(c["claim_id"], 0) if c is not None else 0
            r["priority"] = round((1.0 - conf) * d, 9)
    open_reqs = [r for r in t["collection_requirements"] if _d(r["created_at"]) <= as_of and r["status"] not in ("satisfaction", "closed")]
    for rank, r in enumerate(sorted(open_reqs, key=lambda r: (-r["priority"], r["req_id"])), start=1):
        r["jipcl_rank"] = rank
    for r in t["collection_requirements"]:
        if r["status"] in ("satisfaction", "closed"):
            r["jipcl_rank"] = None
    return t


def ranking(tables: dict, game_id: str, actor_id: str) -> list[str]:
    ss = [s for s in tables["strategies"] if s["game_id"] == game_id and s["actor_id"] == actor_id and s.get("status") == "valid"]
    return [s["strategy_id"] for s in sorted(ss, key=lambda s: (-s["value"], s["strategy_id"]))]
