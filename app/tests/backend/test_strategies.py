"""GET /api/strategies: the three Blue options side by side."""
from __future__ import annotations

import pytest

BATCHES = (0, 1, 2, 3)
TESTS = ("suitable", "feasible", "acceptable", "distinguishable", "complete")


def strategies(client, batch: int) -> list[dict]:
    response = client.get("/api/strategies", params={"batch": batch})
    assert response.status_code == 200
    return response.json()["strategies"]


@pytest.mark.parametrize("batch", BATCHES)
def test_only_the_three_blue_meridian_options_are_served(client, batch):
    """The RPS game is a dataset test fixture, not an operator option."""
    ids = [s["strategy_id"] for s in strategies(client, batch)]
    assert ids == ["str_blue_1", "str_blue_2", "str_blue_3"]
    assert not [i for i in ids if "rps" in i or "red" in i]


def test_rps_and_red_strategies_are_not_addressable(client):
    for strategy_id in ("str_rps_p1_uniform", "str_red_ml"):
        response = client.get(f"/api/strategies/{strategy_id}", params={"batch": 0})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "unknown_id"


def test_the_invalid_option_names_the_gate_it_failed(client, manifests):
    failed = sorted(
        row["test"]
        for row in manifests[1]["expected_effects"]["validity_changed"]
        if row["strategy_id"] == "str_blue_1" and row["after"] is False
    )
    strategy = next(
        s for s in strategies(client, 1) if s["strategy_id"] == "str_blue_1"
    )
    assert strategy["status"] == "invalid"
    assert strategy["gate_failed"] == "acceptable"
    assert strategy["gates_failed"] == failed
    evidence = {t["test"]: t["evidence"] for t in strategy["validity"]}
    assert "aspiration" in evidence["acceptable"]


@pytest.mark.parametrize("batch", BATCHES)
def test_every_option_carries_all_five_validity_tests_with_evidence(client, batch):
    for strategy in strategies(client, batch):
        assert [t["test"] for t in strategy["validity"]] == list(TESTS)
        assert all(t["evidence"] for t in strategy["validity"])
        assert (strategy["gate_failed"] is None) == (strategy["status"] == "valid")


@pytest.mark.parametrize("batch", BATCHES)
def test_objective_contributions_agree_with_the_app_f_ratings(client, batch):
    """E[u_k] is computed with eval.value; the loader's rating is its rank. They must agree."""
    rows = strategies(client, batch)
    valid = [s for s in rows if s["status"] == "valid"]
    for objective_id in {o["objective_id"] for o in rows[0]["objectives"]}:
        pairs = [
            (
                next(o for o in s["objectives"] if o["objective_id"] == objective_id),
                s["strategy_id"],
            )
            for s in valid
        ]
        by_contribution = sorted(pairs, key=lambda p: p[0]["expected_contribution"])
        ratings = [p[0]["rating_1_to_3"] for p in by_contribution]
        assert ratings == sorted(ratings), (
            f"{objective_id}: a higher E[u_k] must not carry a lower App. F rating"
        )


@pytest.mark.parametrize("batch", BATCHES)
def test_weights_sum_to_one_and_resources_report_worst_case_use(client, batch):
    for strategy in strategies(client, batch):
        assert sum(o["weight"] for o in strategy["objectives"]) == pytest.approx(1.0)
        assert strategy["resources"]
        for resource in strategy["resources"]:
            assert resource["worst_case_use"] >= 0.0
            assert resource["within_budget"] == (
                resource["worst_case_use"] <= resource["budget"]
            )
        feasible = next(t for t in strategy["validity"] if t["test"] == "feasible")
        assert feasible["passed"] == all(r["within_budget"] for r in strategy["resources"])


def test_theory_of_victory_and_opponent_model_resolve_to_names(client):
    strategy = next(s for s in strategies(client, 0) if s["strategy_id"] == "str_blue_1")
    chain = strategy["theory_of_victory"]
    assert chain and all(e["from_name"] and e["to_name"] for e in chain)
    assert {e["from_type"] for e in chain} <= {
        "action", "claim", "objective", "assumption", "strategy", "harmful_event",
        "problem_set",
    }
    assert chain[0]["from_name"] != chain[0]["from_id"], "names, not raw ids"

    model = strategy["opponent_model"]
    assert model["actor_name"] == "Varenia"
    assert sum(c["probability"] for c in model["coas"]) == pytest.approx(1.0)
    assert {c["adversary_coa_label"] for c in model["coas"]} == {
        "most_likely", "most_dangerous", "alternative",
    }


def test_assumptions_carry_grounding_and_jp50_flags(client):
    strategy = next(s for s in strategies(client, 3) if s["strategy_id"] == "str_blue_3")
    unrealistic = [a for a in strategy["assumptions"] if not a["jp50_realistic"]]
    assert unrealistic, "COA 3 is authored with an unrealistic assumption"
    for assumption in strategy["assumptions"]:
        assert assumption["subject_name"]
        assert assumption["predicate"] and assumption["tolerance_op"]
        assert assumption["origin"] in {"own", "higher_hq"}


def test_mitigated_and_unmitigated_events_carry_current_risk_levels(client):
    strategy = next(s for s in strategies(client, 3) if s["strategy_id"] == "str_blue_2")
    mitigated = strategy["mitigated_harmful_events"]
    unmitigated = strategy["unmitigated_harmful_events"]
    events = mitigated + unmitigated
    assert len(events) == 9
    assert not {e["he_id"] for e in mitigated} & {e["he_id"] for e in unmitigated}
    # No COA in the shipped dataset claims a mitigation: mitigates_he_ids is empty on all
    # nine strategies, so every harmful event is reported unmitigated.
    assert mitigated == []
    for event in events:
        assert [h["jsps_horizon"] for h in event["horizons"]] == ["near", "mid", "long"]
        assert all(h["risk_level"] for h in event["horizons"])


def test_the_caution_comes_from_the_dataset_style_checker(client):
    from eval.style_check import CAUTION

    body = client.get("/api/strategies", params={"batch": 0}).json()
    assert body["caution"] == CAUTION
    assert body["ranking"] == ["str_blue_1", "str_blue_2", "str_blue_3"]
