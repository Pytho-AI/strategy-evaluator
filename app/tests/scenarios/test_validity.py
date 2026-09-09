"""The five JP 5-0 validity tests decide something on this scenario rather than passing by default."""
from __future__ import annotations

import copy


def test_suitable_reaches_every_guidance_objective(blue, computed):
    guidance = next(g for g in computed["guidance"] if g["guidance_id"] == "gd_opord_26_004")
    assert len(guidance["objective_ids"]) == 5
    for s in blue:
        assert s["validity"]["suitable"]["pass"], s["validity"]["suitable"]["evidence"]
        assert s["theory_of_victory"], s["strategy_id"]


def test_guidance_chain_is_the_full_jsps_ladder(computed):
    chain, node = [], "gd_opord_26_004"
    by_id = {g["guidance_id"]: g for g in computed["guidance"]}
    while node:
        chain.append(by_id[node]["product_type"])
        node = by_id[node]["parent_guidance_id"]
    assert chain == ["OPORD", "contingency_plan", "JSCP", "NMS", "NDS", "NSS"]


def test_feasible_passes_with_real_headroom(blue):
    for s in blue:
        assert s["validity"]["feasible"]["pass"], s["validity"]["feasible"]["evidence"]
        assert "within budget" in s["validity"]["feasible"]["evidence"]


def test_feasible_is_not_vacuous(build, authored, engine, S):
    """Halving one COA's munitions allocation makes it infeasible: the ceiling is real."""
    tables = copy.deepcopy(authored)
    for row in tables["strategy_resources"]:
        if row["strategy_id"] == "str_coa_4" and row["resource_id"] == "res_munitions":
            row["budget"] = row["budget"] / 2
    out = engine.recompute(tables, S.AS_OF, S.WORLD_VERSION)
    coa4 = next(s for s in out["strategies"] if s["strategy_id"] == "str_coa_4")
    assert not coa4["validity"]["feasible"]["pass"]
    assert coa4["status"] == "infeasible"


def test_acceptable_separates_the_coas(blue):
    """Aspiration w.tau sits inside the value spread, so the test decides rather than waving through."""
    passed = [s["strategy_id"] for s in blue if s["validity"]["acceptable"]["pass"]]
    failed = [s["strategy_id"] for s in blue if not s["validity"]["acceptable"]["pass"]]
    assert passed and failed, "the acceptable test is vacuous"
    assert all(abs(s["aspiration"] - 0.44) < 1e-9 for s in blue)
    for s in blue:
        assert (s["value"] >= s["aspiration"]) == s["validity"]["acceptable"]["pass"]


def test_statuses_follow_from_the_tests(blue):
    for s in blue:
        v = s["validity"]
        if not v["feasible"]["pass"]:
            assert s["status"] == "infeasible"
        elif all(v[t]["pass"] for t in ("suitable", "acceptable", "distinguishable", "complete")):
            assert s["status"] == "valid"
        else:
            assert s["status"] == "invalid"
    assert sum(1 for s in blue if s["status"] == "valid") == 3


def test_distinguishable_over_every_pair(blue, computed):
    rows = [d for d in computed["distinguishability"]
            if d["strategy_a"].startswith("str_coa") and d["strategy_b"].startswith("str_coa")]
    assert len(rows) == 5 * 4
    for d in rows:
        assert d["pass"], f"{d['strategy_a']} vs {d['strategy_b']}: {d['dims_differing']}"
        assert len(d["dims_differing"]) >= 2
    for s in blue:
        assert s["validity"]["distinguishable"]["pass"]


def test_complete_covers_mission_end_state_rules_and_decision_points(blue, computed):
    dps = {}
    for dp in computed["decision_points"]:
        dps.setdefault(dp["strategy_id"], []).append(dp)
    for s in blue:
        assert s["validity"]["complete"]["pass"], s["validity"]["complete"]["evidence"]
        for field in ("mission_who", "mission_what", "mission_when", "mission_where", "mission_why"):
            assert s[field].strip()
        assert s["end_state_objective_id"] == "obj_end_state"
        assert len(dps[s["strategy_id"]]) == 4, "DP1-DP3 plus one COA-specific decision point"


def test_every_decision_point_is_tied_to_a_pir(computed):
    pirs = {p["pir_id"]: p for p in computed["pirs"]}
    for dp in computed["decision_points"]:
        assert dp["pir_id"] in pirs, dp["dp_id"]
        assert dp["dp_id"] in pirs[dp["pir_id"]]["decision_point_ids"]
    named = {dp["name"].split(" - ")[0] for dp in computed["decision_points"]}
    assert {"DP1", "DP2", "DP3", "DP4"} == named


def test_policy_rules_are_conditioned_on_observable_state(computed, S):
    observable = {o["variable"] for o in computed["games"][0]["observables"] if o["actor_id"] == S.BLUE}
    used = set()
    for r in computed["policy_rules"]:
        if not r["strategy_id"].startswith("str_coa"):
            continue
        cond = r["condition"]
        if isinstance(cond, dict):
            used.add(cond["var"])
    assert used <= observable
    assert len(used) >= 5, "the policies barely branch on state"
    per_coa = {}
    for r in computed["policy_rules"]:
        per_coa.setdefault(r["strategy_id"], []).append(r)
    for sid in [c[0] for c in S.COAS]:
        assert 6 <= len(per_coa[sid]) <= 12
