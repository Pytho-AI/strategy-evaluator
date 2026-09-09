"""The decision overview answers the first screen's three questions from the data."""
from __future__ import annotations

import pytest

BATCHES = (0, 1, 2, 3)


def overview(client, batch: int) -> dict:
    body = client.get("/api/snapshot", params={"batch": batch}).json()
    return body["decision_overview"]


@pytest.mark.parametrize("batch", BATCHES)
def test_the_recommendation_is_the_first_valid_strategy(client, batch):
    body = client.get("/api/snapshot", params={"batch": batch}).json()
    view = body["decision_overview"]
    ranking = next(
        r["strategy_ids"]
        for r in body["rankings"]
        if (r["game_id"], r["actor_id"]) == ("meridian", "ent_blue")
    )
    assert view["ranking"] == ranking
    assert view["recommended"]["strategy_id"] == ranking[0]
    status = {s["strategy_id"]: s["status"] for s in body["strategies"]}
    assert status[view["recommended"]["strategy_id"]] == "valid"


def test_an_invalid_strategy_is_never_recommended(client, manifests):
    """Batch 1 invalidates str_blue_1; the overview must move off it."""
    assert manifests[1]["expected_effects"]["ranking_after"][0] != "str_blue_1"
    view = overview(client, 1)
    assert view["recommended"]["strategy_id"] == "str_blue_2"
    assert "str_blue_1" not in view["ranking"]


@pytest.mark.parametrize("batch", BATCHES)
def test_why_states_criteria_the_tradeoff_and_the_validity_evidence(client, batch):
    view = overview(client, batch)
    why = view["why"]
    assert [t["test"] for t in why["validity_evidence"]] == [
        "suitable", "feasible", "acceptable", "distinguishable", "complete",
    ]
    assert all(t["passed"] for t in why["validity_evidence"])
    assert why["winning_criteria"], "a recommendation always wins on some criterion"
    weights = [c["weight"] for c in why["winning_criteria"]]
    assert weights == sorted(weights, reverse=True)
    tradeoff = why["tradeoff"]
    if len(view["ranking"]) > 1:
        assert tradeoff["runner_up_id"] == view["ranking"][1]
        assert tradeoff["value_gap"] > 0
        for criterion in tradeoff["objectives_favouring_runner_up"]:
            assert criterion["runner_up_contribution"] > criterion["contribution"]
    else:
        assert tradeoff is None


@pytest.mark.parametrize("batch", BATCHES)
def test_the_highest_sensitivity_assumptions_belong_to_the_recommendation(client, batch):
    view = overview(client, batch)
    listed = view["highest_sensitivity_assumptions"]
    assert 0 < len(listed) <= 3
    assert {a["strategy_id"] for a in listed} == {view["recommended"]["strategy_id"]}
    magnitudes = [abs(a["sensitivity"]) for a in listed]
    assert magnitudes == sorted(magnitudes, reverse=True)
    assert all(a["status"] in {"holds", "violated", "stale", "unknown"} for a in listed)


@pytest.mark.parametrize("batch", BATCHES)
def test_the_top_requirement_is_the_first_open_one_with_a_stated_basis(client, batch):
    view = overview(client, batch)
    requirement = view["top_collection_requirement"]
    assert requirement["jipcl_rank"] == 1
    assert requirement["status"] not in ("satisfaction", "closed")
    basis = requirement["priority_basis"]
    assert basis["basis"] in ("evpi", "fallback")
    if basis["basis"] == "evpi":
        assert basis["assumption_id"] and basis["evpi"] == requirement["priority"]
    else:
        assert basis["confidence"] is not None and basis["degree"] is not None


@pytest.mark.parametrize("batch", BATCHES)
def test_highest_risks_are_the_worst_levels_currently_assessed(client, batch):
    from eval.jram import RISK_LEVELS

    view = overview(client, batch)
    risks = view["highest_risks"]
    assert 0 < len(risks) <= 5
    ranks = [RISK_LEVELS.index(r["risk_level"]) for r in risks]
    assert ranks == sorted(ranks, reverse=True)
    top = risks[0]["risk_level"]
    assert {p["max_risk_level"] for p in view["problem_sets_at_highest_level"]} == {top}
    assert all(r["problem_set_name"] and r["statement"] for r in risks)


def test_batch_1_overview_shows_the_chokepoint_moving_to_significant(client, manifests):
    moved = manifests[1]["expected_effects"]["problem_sets_moved"]
    assert {row["problem_set_id"] for row in moved} == {"ps_chokepoint"}
    view = overview(client, 1)
    assert {p["problem_set_id"] for p in view["problem_sets_at_highest_level"]} == {
        "ps_chokepoint"
    }
    assert view["highest_risks"][0]["risk_level"] == "significant"


def test_the_overview_carries_the_batch_marking_and_caution(client):
    from app.backend.branding import MARKING
    from eval.style_check import CAUTION

    view = overview(client, 2)
    assert view["batch"] == 2 and view["as_of"] == "2026-10-23"
    assert view["marking"] == MARKING == "UNCLASSIFIED — SYNTHETIC"
    assert view["caution"] == CAUTION
