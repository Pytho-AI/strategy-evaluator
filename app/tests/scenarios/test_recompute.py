"""`eval/engine.py::recompute` runs on the scenario unchanged and produces real answers."""
from __future__ import annotations

import time


def test_five_blue_coas_with_a_value_and_five_validity_tests(blue):
    assert [s["strategy_id"] for s in blue] == [f"str_coa_{i}" for i in range(1, 6)]
    for s in blue:
        assert isinstance(s["value"], float)
        assert s["value_ci"][0] <= s["value"] <= s["value_ci"][1]
        assert isinstance(s["robustness"], float)
        assert set(s["validity"]) == {"suitable", "feasible", "acceptable", "distinguishable", "complete"}
        for test, outcome in s["validity"].items():
            assert isinstance(outcome["pass"], bool), test
            assert outcome["evidence"].strip(), test
        assert s["status"] in {"valid", "invalid", "infeasible"}
        assert s["world_version"] == 0


def test_utility_vector_order_is_the_five_ui_criteria(computed, engine, S):
    order = engine.objective_order(computed, S.GAME_ID, S.BLUE)
    assert order == sorted(S.CRITERIA)
    assert all(len(p["utility"]) == len(order) for p in computed["payoffs"]
               if p["strategy_id"].startswith("str_coa"))


def test_assumption_probabilities_come_from_evidence(computed):
    rows = {a["index_k"]: a for a in computed["assumptions"] if a["strategy_id"].startswith("str_coa")}
    assert sorted(rows) == list(range(8))
    for k, a in rows.items():
        assert 0.0 < a["p_holds"] < 1.0
        assert a["status"] in {"holds", "violated", "stale", "unknown"}
        assert a["sensitivity"] is not None
        assert a["evpi"] is not None
    # p_holds tracks the confidence percentages the UI shows for A1..A8
    assert rows[0]["p_holds"] > rows[2]["p_holds"] > rows[4]["p_holds"]


def test_exactly_one_assumption_is_not_realistic(computed, S):
    unrealistic = {a["index_k"] for a in computed["assumptions"]
                   if a["strategy_id"].startswith("str_coa") and not a["jp50_realistic"]}
    assert unrealistic == {S.UNREALISTIC_INDEX_K}
    assert S.UNREALISTIC_INDEX_K == 2  # A3, the no-strikes-on-CONUS assumption


def test_ratings_are_assigned_to_every_strategy_objective(computed):
    assert all(so["rating_1_to_3"] in (1, 2, 3) for so in computed["strategy_objectives"])


def test_risk_and_collection_columns_are_computed(computed):
    assert len(computed["risk_assessments"]) == 3 * len(computed["harmful_events"])
    assert all(r["statement_text"] for r in computed["risk_assessments"])
    ranked = [r for r in computed["collection_requirements"] if r["jipcl_rank"] is not None]
    assert ranked, "no collection requirement was ranked"
    assert sorted(r["jipcl_rank"] for r in ranked) == list(range(1, len(ranked) + 1))


def test_recompute_is_fast_enough_for_an_api_call(build, authored, engine, S):
    best = min(_time_recompute(engine, authored, S) for _ in range(3))
    assert best < 0.300, f"recompute took {best * 1000:.0f} ms with 2^8 worlds"


def _time_recompute(engine, authored, S) -> float:
    start = time.perf_counter()
    engine.recompute(authored, S.AS_OF, S.WORLD_VERSION)
    return time.perf_counter() - start
