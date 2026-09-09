"""The payoff tensor is structured, and the structure buys the three properties it was built for:

1. information about at least two assumptions changes which COA is best (EVPI is not an artefact);
2. no COA dominates on every objective;
3. the weighted ranking under the UI's default weights is not degenerate.
"""
from __future__ import annotations

import pytest

BLUE_COAS = [f"str_coa_{i}" for i in range(1, 6)]


# ---------------------------------------------------------------- structure
def test_deltas_are_nonzero_exactly_on_the_coa_lib_dependencies(P):
    for sid, deps in P.BLUE_DEPS.items():
        for k in range(P.K_BLUE):
            nonzero = any(abs(v) > 0 for v in P.delta(sid, k).values())
            assert nonzero == (k in deps), f"{sid} delta on k={k}"


def test_the_dominant_dependency_has_the_largest_magnitude(P):
    dominant = {"str_coa_1": 3, "str_coa_2": 5, "str_coa_3": 6, "str_coa_4": 2, "str_coa_5": 2}
    for sid, k in dominant.items():
        assert max(P.MAGNITUDE[sid], key=P.MAGNITUDE[sid].get) == k


def test_all_assumptions_hold_reproduces_the_authored_table(P):
    top = P.authored_utility()
    floor = P.floor_utility()
    for sid, deps in P.BLUE_DEPS.items():
        for oid in P.CRITERION_FIELD:
            rebuilt = floor[sid][oid] + sum(P.delta(sid, k)[oid] for k in deps)
            assert rebuilt == pytest.approx(top[sid][oid], abs=1e-12)


def test_authored_standing_matches_the_ui_constants(P):
    """Per criterion, the ordering of the five COAs is COA_LIB's ordering."""
    u = P.authored_utility()
    best = {oid: max(u, key=lambda sid: u[sid][oid]) for oid in P.CRITERION_FIELD}
    assert best["obj_mission"] == "str_coa_1"
    assert best["obj_personnel"] == "str_coa_5"
    assert best["obj_escalation"] == "str_coa_5"
    assert best["obj_time"] == "str_coa_4"
    assert best["obj_resources"] == "str_coa_5"
    worst = {oid: min(u, key=lambda sid: u[sid][oid]) for oid in P.CRITERION_FIELD}
    assert worst["obj_escalation"] == "str_coa_4"
    assert worst["obj_resources"] == "str_coa_1"
    assert worst["obj_mission"] == "str_coa_5"


def test_no_coa_dominates_on_every_objective(P):
    u = P.authored_utility()
    for sid in u:
        beaten = [oid for oid in P.CRITERION_FIELD if any(u[o][oid] > u[sid][oid] for o in u if o != sid)]
        assert beaten, f"{sid} is best on every objective"


# ---------------------------------------------------------------- EVPI sanity
def _blue_setup(computed, engine, value, claimset, S):
    idx = value.PayoffIndex(computed["payoffs"])
    order = engine.objective_order(computed, S.GAME_ID, S.BLUE)
    rows = {s["strategy_id"]: s for s in computed["strategies"] if s["strategy_id"] in BLUE_COAS}
    weights = {sid: engine.weights_for(computed, sid, order) for sid in rows}
    opps = {sid: engine.opponent_dist(computed, rows[sid]["opponent_model_id"]) for sid in rows}
    K, p, _ = engine.assumption_vector(computed, S.GAME_ID, S.BLUE,
                                       claimset.ClaimSet(computed["claims"]), S.AS_OF)
    return idx, weights, opps, p, K


def _argmax(idx, weights, opps, p, K, value, k, bit):
    scores = {sid: value.value(sid, idx, weights[sid], opps[sid], p, K, "expected", None, {k: bit})
              for sid in weights}
    return max(scores, key=lambda sid: (scores[sid], sid))


def test_at_least_two_assumptions_flip_the_best_coa(computed, engine, value, claimset, S):
    idx, weights, opps, p, K = _blue_setup(computed, engine, value, claimset, S)
    flips = [k for k in range(K)
             if _argmax(idx, weights, opps, p, K, value, k, 1) != _argmax(idx, weights, opps, p, K, value, k, 0)]
    assert len(flips) >= 2, f"only {flips} change the argmax; EVPI would be an artefact"
    # A3 and A6 are the two the payoff structure was designed around.
    assert {2, 5} <= set(flips)


def test_evpi_is_positive_exactly_where_the_argmax_flips(computed, engine, value, claimset, S):
    idx, weights, opps, p, K = _blue_setup(computed, engine, value, claimset, S)
    evpi = {a["index_k"]: a["evpi"] for a in computed["assumptions"] if a["strategy_id"] in BLUE_COAS}
    for k in range(K):
        flips = _argmax(idx, weights, opps, p, K, value, k, 1) != _argmax(idx, weights, opps, p, K, value, k, 0)
        assert (evpi[k] > 0) == flips, f"k={k}: evpi={evpi[k]} flips={flips}"
    assert evpi[2] > 0 and evpi[5] > 0


def test_sensitivity_is_nonzero_exactly_on_a_coas_own_dependencies(computed, P):
    for a in computed["assumptions"]:
        if a["strategy_id"] not in BLUE_COAS:
            continue
        assert a["index_k"] in P.BLUE_DEPS[a["strategy_id"]]
        assert abs(a["sensitivity"]) > 1e-9


# ---------------------------------------------------------------- ranking
def test_weighted_ranking_under_the_ui_weights_is_not_degenerate(blue, P):
    values = [s["value"] for s in blue]
    assert len(set(round(v, 9) for v in values)) == 5, "two COAs share a value"
    assert max(values) - min(values) > 0.05, "the five COAs are indistinguishable by value"
    leader = max(blue, key=lambda s: s["value"])["strategy_id"]
    # The weights do real work: the leader is not the argmax on any single criterion, and it is
    # not the COA with the highest authored success probability either.
    u = P.authored_utility()
    per_criterion_best = {max(u, key=lambda sid: u[sid][oid]) for oid in P.CRITERION_FIELD}
    assert leader not in per_criterion_best
    assert leader != max(P.AUTHORED, key=lambda sid: P.AUTHORED[sid]["s"])


def test_opponent_distribution_sums_to_one_over_three_labelled_coas(computed):
    om = next(o for o in computed["opponent_models"] if o["opponent_model_id"] == "om_blue")
    assert sum(m["probability"] for m in om["distribution"]) == pytest.approx(1.0)
    labels = {s["adversary_coa_label"] for s in computed["strategies"] if s["actor_id"] == "ent_rus"}
    assert labels == {"most_likely", "most_dangerous", "alternative"}


def test_payoff_coverage_is_exact(computed, P):
    triples = {(p["strategy_id"], p["opponent_strategy_id"], p["world"]) for p in computed["payoffs"]}
    assert len(triples) == len(computed["payoffs"])
    assert len(triples) == 5 * 3 * 2 ** P.K_BLUE + 3 * 5 * 2 ** P.K_RED
