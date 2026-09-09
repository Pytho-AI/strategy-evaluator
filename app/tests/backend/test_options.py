"""The v3 comparison endpoints, against Meridian.

Everything here is checked against a direct call into ``dataset/eval`` on the same tables,
never against a number written into this file. The honesty rules the API promises --
``adversary_range`` is not a confidence interval, ``p_meets_aspiration`` is a probability
over enumerated worlds and not "probability of success", likelihood and confidence stay
apart, and the App. F caution rides with every ranked comparison -- are asserted here too,
because they are contract, not prose.
"""
from __future__ import annotations

import time

import pytest

from app.backend.adapter import eval_module
from app.backend.options import (
    BIN_COUNT,
    DEFAULT_WEIGHTS,
    MAX_LEVEL_SCORE,
    level_for,
    level_score,
)
from app.backend.scenarios import CRITERION_KEYS

BATCHES = (0, 1, 2, 3)
CRITERIA = list(CRITERION_KEYS)


def options(client, batch=0, **params):
    response = client.get("/api/options", params={"batch": batch, **params})
    assert response.status_code == 200, response.text
    return response.json()


def ranked(client, batch=0, **params):
    response = client.get("/api/options/rank", params={"batch": batch, **params})
    assert response.status_code == 200, response.text
    return response.json()


def distribution(client, batch=0, **params):
    response = client.get(
        "/api/options/outcome-distribution", params={"batch": batch, **params}
    )
    assert response.status_code == 200, response.text
    return response.json()


def what_if(client, assumption, batch=0, **params):
    response = client.get(
        "/api/options/what-if",
        params={"assumption": assumption, "batch": batch, **params},
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------- /api/options
@pytest.mark.parametrize("batch", BATCHES)
def test_the_option_set_is_the_scenarios_own_options_numbered_from_one(client, batch):
    body = options(client, batch)
    assert body["scenario"] == "meridian"
    ids = [o["strategy_id"] for o in body["options"]]
    assert ids == ["str_blue_1", "str_blue_2", "str_blue_3"]
    assert [o["number"] for o in body["options"]] == [1, 2, 3]


@pytest.mark.parametrize("batch", BATCHES)
def test_every_option_carries_what_the_comparison_screen_draws(client, batch):
    for option in options(client, batch)["options"]:
        assert option["title"] and option["approach"] and option["concept"]
        assert option["tasks"], "an option with no tasks has no 'how'"
        assert option["status"] in {"valid", "invalid", "infeasible"}
        assert [t["test"] for t in option["validity"]] == [
            "suitable", "feasible", "acceptable", "distinguishable", "complete"
        ]
        for test in option["validity"]:
            assert test["evidence"], f"{test['test']} passed no evidence"
        failed = [t["test"] for t in option["validity"] if not t["passed"]]
        assert option["gates_failed"] == failed
        assert option["gate_failed"] == (failed[0] if failed else None)
        assert option["adversary_range"]["min"] <= option["adversary_range"]["max"]
        assert [c["key"] for c in option["criteria"]] == CRITERIA


@pytest.mark.parametrize("batch", BATCHES)
def test_value_range_robustness_and_status_are_the_loaders_own_columns(client, adapter, batch):
    index = adapter.index(batch)
    for option in options(client, batch)["options"]:
        row = index.strategies[option["strategy_id"]]
        assert option["expected_value"] == row["value"]
        assert option["robustness"] == row["robustness"]
        assert option["aspiration"] == row["aspiration"]
        assert option["status"] == row["status"]
        assert [option["adversary_range"]["min"], option["adversary_range"]["max"]] == (
            row["value_ci"]
        )


@pytest.mark.parametrize("batch", BATCHES)
def test_a_single_objective_criterion_is_exactly_that_objectives_expected_value(
    client, adapter, batch
):
    """personnel and escalation each cover one Meridian objective, so E[u_k] must match."""
    index = adapter.index(batch)
    single = {"personnel": "obj_preserve_force", "escalation": "obj_limit_escalation"}
    for option in options(client, batch)["options"]:
        contributions = index.contributions(option["strategy_id"])
        for criterion in option["criteria"]:
            objective_id = single.get(criterion["key"])
            if objective_id is None:
                continue
            assert criterion["expected_value"] == pytest.approx(
                contributions[objective_id], abs=1e-9
            )


@pytest.mark.parametrize("batch", BATCHES)
def test_a_resource_criterion_is_the_tightest_worst_case_budget_ratio(client, adapter, batch):
    index = adapter.index(batch)
    for option in options(client, batch)["options"]:
        used = index.worst_case_cost(option["strategy_id"])
        budgets = {
            r["resource_id"]: r["budget"]
            for r in index.rows("strategy_resources")
            if r["strategy_id"] == option["strategy_id"]
        }
        for criterion in option["criteria"]:
            if criterion["basis"] != "resources":
                continue
            expected = max(
                used.get(m["id"], 0.0) / budgets[m["id"]] for m in criterion["members"]
            )
            assert criterion["shortfall"] == pytest.approx(expected, abs=1e-9)
            assert criterion["expected_value"] == pytest.approx(1.0 - expected, abs=1e-9)
            for member in criterion["members"]:
                assert member["worst_case_use"] == used.get(member["id"], 0.0)


@pytest.mark.parametrize("batch", BATCHES)
def test_levels_come_from_the_jram_bands_and_score_four_to_one(client, batch):
    jram = eval_module("jram")
    body = options(client, batch)
    assert [t["level"] for t in body["level_thresholds"]] == list(jram.RISK_LEVELS)
    assert [t["shortfall_to"] for t in body["level_thresholds"]] == [
        upper for _, upper in jram.P_BANDS
    ]
    assert [t["score"] for t in body["level_thresholds"]] == [4, 3, 2, 1]
    assert MAX_LEVEL_SCORE == len(jram.RISK_LEVELS)
    for option in body["options"]:
        for criterion in option["criteria"]:
            assert criterion["level"] == level_for(criterion["shortfall"])
            assert criterion["score"] == level_score(criterion["level"])
            assert criterion["level_label"] == jram.RISK_LABEL[criterion["level"]]


def test_the_threshold_table_matches_the_bands_it_says_it_uses(client):
    jram = eval_module("jram")
    for row in options(client)["level_thresholds"]:
        band = row["jram_probability_band"]
        # A shortfall just inside the band's upper edge must bin to that band.
        assert jram.p_bin(row["shortfall_to"] - 1e-9) == band
        assert level_for(row["shortfall_to"] - 1e-9) == row["level"]


@pytest.mark.parametrize("batch", BATCHES)
def test_contributions_are_weight_times_score_and_sum_to_the_total(client, batch):
    body = options(client, batch)
    assert body["weights"] == DEFAULT_WEIGHTS
    assert body["weighted_max"] == sum(DEFAULT_WEIGHTS.values()) * MAX_LEVEL_SCORE
    for option in body["options"]:
        for criterion in option["criteria"]:
            assert criterion["weight"] == DEFAULT_WEIGHTS[criterion["key"]]
            assert criterion["contribution"] == criterion["weight"] * criterion["score"]
        assert option["weighted_total"] == sum(
            c["contribution"] for c in option["criteria"]
        )
        assert option["weighted_max"] == body["weighted_max"]


def test_weights_can_be_overridden_per_request(client):
    body = options(client, mission=5, resources=0)
    assert body["weights"]["mission"] == 5
    assert body["weights"]["resources"] == 0
    assert body["weights"]["personnel"] == DEFAULT_WEIGHTS["personnel"]
    for option in body["options"]:
        resources = next(c for c in option["criteria"] if c["key"] == "resources")
        assert resources["contribution"] == 0


@pytest.mark.parametrize("batch", BATCHES)
def test_each_option_lists_the_assumptions_it_depends_on(client, adapter, batch):
    index = adapter.index(batch)
    for option in options(client, batch)["options"]:
        rows = [
            a for a in index.rows("assumptions")
            if a["strategy_id"] == option["strategy_id"]
        ]
        assert [a["assumption_id"] for a in option["assumptions"]] == [
            a["assumption_id"] for a in sorted(rows, key=lambda a: a["index_k"])
        ]
        for served, row in zip(option["assumptions"], sorted(rows, key=lambda a: a["index_k"])):
            assert served["status"] == row["status"]
            assert served["p_holds"] == row["p_holds"]
            assert served["sensitivity"] == row["sensitivity"]
            assert served["evpi"] == row["evpi"]


# ---------------------------------------------------------------- /api/options/rank
@pytest.mark.parametrize("batch", BATCHES)
def test_the_ranking_orders_by_the_weighted_total(client, batch):
    body = ranked(client, batch)
    totals = [row["weighted_total"] for row in body["ranked"]]
    assert totals == sorted(totals, reverse=True)
    assert [row["rank"] for row in body["ranked"]] == list(range(1, len(totals) + 1))
    for row in body["ranked"]:
        assert row["weighted_pct"] == round(
            row["weighted_total"] / body["weighted_max"] * 100
        )


def test_get_and_post_rank_agree(client):
    from_get = client.get("/api/options/rank", params={"mission": 5, "time": 0}).json()
    from_post = client.post(
        "/api/options/rank", params={"scenario": "meridian"},
        json={"mission": 5, "time": 0},
    ).json()
    assert from_get["weights"] == from_post["weights"] == {
        **DEFAULT_WEIGHTS, "mission": 5, "time": 0
    }
    assert [r["strategy_id"] for r in from_get["ranked"]] == [
        r["strategy_id"] for r in from_post["ranked"]
    ]


@pytest.mark.parametrize("batch", BATCHES)
def test_weight_stability_is_deterministic_and_enumerated(client, batch):
    first = ranked(client, batch)["weight_stability"]
    second = ranked(client, batch)["weight_stability"]
    assert first == second, "weight stability is not deterministic"
    assert "no sampling" in first["method"].lower()
    assert first["weightings_evaluated"] > 0
    assert first["top_option_id"] == ranked(client, batch)["ranked"][0]["strategy_id"]
    assert 0.0 <= first["fraction_top"] <= 1.0
    assert sum(row["fraction_top"] for row in first["per_option"]) == pytest.approx(
        1.0, abs=1e-9
    )


def test_weight_stability_enumerates_the_clamped_perturbation_product(client):
    """The count is the product of the distinct clamped values, not a sample size."""
    from app.backend.options import WEIGHT_MAX, WEIGHT_MIN, WEIGHT_PERTURBATIONS

    body = ranked(client)
    expected = 1
    for key in CRITERIA:
        expected *= len(
            {min(WEIGHT_MAX, max(WEIGHT_MIN, body["weights"][key] + d))
             for d in WEIGHT_PERTURBATIONS}
        )
    assert body["weight_stability"]["weightings_evaluated"] == expected


def test_a_weighting_that_values_one_criterion_leads_with_that_criterions_best_option(client):
    """The rank must actually follow the weights, not a fixed order."""
    for key in CRITERIA:
        body = ranked(client, **{k: (5 if k == key else 0) for k in CRITERIA})
        scores = {
            row["strategy_id"]: next(c["score"] for c in row["criteria"] if c["key"] == key)
            for row in body["ranked"]
        }
        leader = body["ranked"][0]["strategy_id"]
        assert scores[leader] == max(scores.values()), key


# ---------------------------------------------------------------- distribution
@pytest.mark.parametrize("batch", BATCHES)
def test_the_distribution_is_the_enumerated_worlds_and_sums_to_one(client, adapter, batch):
    index = adapter.index(batch)
    engine = eval_module("engine")
    n_worlds, _, _ = engine.assumption_vector(
        index.snapshot.raw, "meridian", "ent_blue", index.claimset, index.as_of
    )
    for row in distribution(client, batch)["options"]:
        adversaries = len(index.opponent_dist(index.strategies[row["strategy_id"]]))
        assert row["assumption_worlds"] == 2 ** n_worlds
        assert row["adversary_coas"] == adversaries
        assert row["worlds"] == 2 ** n_worlds * adversaries
        assert len(row["bins"]) == BIN_COUNT
        assert sum(b["mass"] for b in row["bins"]) == pytest.approx(1.0, abs=1e-9)
        assert sum(b["count"] for b in row["bins"]) == row["worlds"]
        assert row["total_mass"] == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("batch", BATCHES)
def test_p_meets_aspiration_is_the_mass_at_or_above_the_aspiration(client, adapter, batch):
    """Recomputed straight from eval.value.outcomes_for, not from the served bins."""
    index = adapter.index(batch)
    value = eval_module("value")
    engine = eval_module("engine")
    tables = index.snapshot.raw
    n_worlds, probabilities, _ = engine.assumption_vector(
        tables, "meridian", "ent_blue", index.claimset, index.as_of
    )
    order = index.objective_order("meridian", "ent_blue")
    for row in distribution(client, batch)["options"]:
        strategy = index.strategies[row["strategy_id"]]
        outcomes = value.outcomes_for(
            row["strategy_id"], index.payoff_index,
            engine.weights_for(tables, row["strategy_id"], order),
            index.opponent_dist(strategy), probabilities, n_worlds,
        )
        aspiration = strategy["aspiration"]
        expected = sum(p for p, x in outcomes if x >= aspiration - 1e-12)
        assert row["p_meets_aspiration"] == pytest.approx(expected, abs=1e-9)
        assert 0.0 <= row["p_meets_aspiration"] <= 1.0
        mean = sum(p * x for p, x in outcomes)
        variance = sum(p * (x - mean) ** 2 for p, x in outcomes)
        assert row["mean_outcome"] == pytest.approx(mean, abs=1e-9)
        assert row["std_dev"] == pytest.approx(variance ** 0.5, abs=1e-9)
        supported = [x for p, x in outcomes if p > 0]
        assert row["outcome_range"] == [
            pytest.approx(min(supported), abs=1e-9), pytest.approx(max(supported), abs=1e-9)
        ]


def test_the_distribution_is_the_same_on_every_call(client):
    """No sampling anywhere: two calls are byte-identical."""
    first = distribution(client)["options"]
    second = distribution(client)["options"]
    assert first == second


def test_one_option_can_be_asked_for(client):
    body = distribution(client, strategy="str_blue_2")
    assert [o["strategy_id"] for o in body["options"]] == ["str_blue_2"]


def test_an_unknown_option_is_404(client):
    response = client.get(
        "/api/options/outcome-distribution", params={"strategy": "str_nope"}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"


# ---------------------------------------------------------------- what-if
def _assumption_ids(client, batch=0):
    return [
        a["assumption_id"]
        for option in options(client, batch)["options"]
        for a in option["assumptions"]
    ]


@pytest.mark.parametrize("batch", BATCHES)
def test_what_if_changes_at_least_one_options_value(client, batch):
    moved = False
    for assumption_id in _assumption_ids(client, batch):
        body = what_if(client, assumption_id, batch)
        if any(o["delta_conditioned"] != 0.0 for o in body["options"]):
            moved = True
            break
    assert moved, "no assumption changed any option's value"


@pytest.mark.parametrize("batch", BATCHES)
def test_the_conditioned_value_is_eval_value_with_theta_k_zero(client, adapter, batch):
    index = adapter.index(batch)
    value = eval_module("value")
    engine = eval_module("engine")
    tables = index.snapshot.raw
    n_worlds, probabilities, _ = engine.assumption_vector(
        tables, "meridian", "ent_blue", index.claimset, index.as_of
    )
    order = index.objective_order("meridian", "ent_blue")
    assumption_id = _assumption_ids(client, batch)[0]
    k = index.assumptions[assumption_id]["index_k"]
    body = what_if(client, assumption_id, batch)
    assert body["assumption"]["index_k"] == k
    for row in body["options"]:
        strategy = index.strategies[row["strategy_id"]]
        expected = value.value(
            row["strategy_id"], index.payoff_index,
            engine.weights_for(tables, row["strategy_id"], order),
            index.opponent_dist(strategy), probabilities, n_worlds,
            strategy["risk_functional"], strategy.get("risk_alpha"), {k: 0},
        )
        assert row["value_after_conditioned"] == pytest.approx(expected, abs=1e-9)
        assert row["value_before"] == strategy["value"]


def test_what_if_names_both_mechanisms_and_the_claims_it_withdrew(client):
    body = what_if(client, "asm_blue_1_k0", batch=3)
    assert set(body["method"]) == {"value", "status_ranking_and_risk"}
    assert "cond={k: 0}" in body["method"]["value"]
    assert body["withdrawn_claim_ids"], "the evidence-withdrawal half withdrew nothing"
    assert body["assumption"]["predicate"] == "range_km"


def test_what_if_reports_the_ranking_before_and_after(client):
    body = what_if(client, "asm_blue_1_k0", batch=3)
    assert body["ranking_before"] == ["str_blue_1", "str_blue_2", "str_blue_3"]
    assert set(body["ranking_after_conditioned"]) <= set(body["ranking_before"])
    # Conditioning k0 false costs str_blue_1 more than str_blue_2, so the order changes.
    assert body["ranking_after_conditioned"] != body["ranking_before"]


def test_what_if_moves_the_risk_tables_when_the_assumption_shares_a_driver(client):
    """asm_blue_1_k0's (subject, predicate) is also a risk driver, so risk must move."""
    body = what_if(client, "asm_blue_1_k0", batch=3)
    assert body["harmful_events_moved"], "the withdrawal moved no harmful event"
    for row in body["harmful_events_moved"]:
        assert row["level_before"] != row["level_after"]
        assert row["jsps_horizon"] in {"near", "mid", "long"}


def test_what_if_never_mutates_the_cached_evaluation(client, adapter):
    before = client.get("/api/snapshot", params={"batch": 3}).json()
    risks_before = client.get("/api/risks", params={"batch": 3}).json()
    strategies_before = {
        s["strategy_id"]: dict(s) for s in adapter.index(3).rows("strategies")
    }
    for assumption_id in _assumption_ids(client, 3):
        what_if(client, assumption_id, 3)
    assert client.get("/api/snapshot", params={"batch": 3}).json()["strategies"] == (
        before["strategies"]
    )
    assert client.get("/api/risks", params={"batch": 3}).json()["harmful_events"] == (
        risks_before["harmful_events"]
    )
    assert {
        s["strategy_id"]: dict(s) for s in adapter.index(3).rows("strategies")
    } == strategies_before


def test_an_unknown_assumption_is_404(client):
    response = client.get("/api/options/what-if", params={"assumption": "asm_nope"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"


# ---------------------------------------------------------------- honesty rules
def test_the_adversary_range_is_never_called_a_confidence_interval(client):
    body = options(client)
    for option in body["options"]:
        basis = option["adversary_range"]["basis"].lower()
        assert "adversary coa" in basis
        assert "not a statistical confidence interval" in basis
    schema = client.get("/openapi.json").json()
    for name in ("AdversaryRangeView", "OptionView", "StrategyView", "StrategyDetailView"):
        text = str(schema["components"]["schemas"][name]).lower()
        assert "confidence interval" not in text or "not a statistical confidence interval" in text


def test_p_meets_aspiration_is_described_as_an_aspiration_probability(client):
    body = distribution(client)
    basis = body["aspiration_basis"].lower()
    assert "aspiration" in basis
    assert "not a probability of success in the real world" in basis
    assert "probability of success" not in basis.replace(
        "not a probability of success in the real world", ""
    )
    schema = client.get("/openapi.json").json()["components"]["schemas"]
    field = schema["OutcomeDistributionView"]["properties"]["p_meets_aspiration"]
    assert "aspiration" in field["description"].lower()


def test_likelihood_and_confidence_stay_separate_fields(client):
    schema = client.get("/openapi.json").json()["components"]["schemas"]
    claim = schema["ClaimView"]["properties"]
    assert "likelihood_icd203" in claim
    assert "confidence_icd203" in claim
    assert "not a probability of truth" in claim["confidence"]["description"]
    rows = client.get("/api/claims", params={"batch": 3, "limit": 50}).json()["claims"]
    for row in rows:
        assert "likelihood_icd203" in row and "confidence_icd203" in row


@pytest.mark.parametrize("batch", BATCHES)
def test_the_app_f_caution_rides_with_every_ranked_comparison(client, batch):
    caution = eval_module("style_check").CAUTION
    assert options(client, batch)["caution"] == caution
    assert ranked(client, batch)["caution"] == caution
    assert what_if(client, "asm_blue_1_k0", batch)["caution"] == caution
    assert client.get("/api/strategies", params={"batch": batch}).json()["caution"] == caution


def test_no_endpoint_reports_a_monte_carlo_run_count(client):
    body = distribution(client)
    text = str(body).lower()
    assert "monte carlo" not in text
    assert "simulat" not in text
    assert "sampled" not in text and "sampling" not in text
    assert body["bin_note"]


# ---------------------------------------------------------------- performance
NEW_URLS = (
    "/api/options?batch=3",
    "/api/options/rank?batch=3",
    "/api/options/outcome-distribution?batch=3",
    "/api/options/what-if?batch=3&assumption=asm_blue_1_k0",
)


@pytest.mark.parametrize("url", NEW_URLS)
def test_each_new_endpoint_answers_in_under_two_seconds_from_cold(url):
    from conftest import MeridianClient

    from app.backend.adapter import DatasetAdapter
    from app.backend.main import create_app

    client = MeridianClient(create_app(DatasetAdapter()))  # empty cache per endpoint
    started = time.perf_counter()
    response = client.get(url)
    elapsed = time.perf_counter() - started
    assert response.status_code == 200, response.text
    assert elapsed < 2.0, f"cold {url} took {elapsed:.3f}s"


def test_the_option_set_is_under_300ms_warm(client):
    client.get("/api/options", params={"batch": 3})  # prime
    started = time.perf_counter()
    assert client.get("/api/options", params={"batch": 3}).status_code == 200
    elapsed = time.perf_counter() - started
    assert elapsed < 0.3, f"warm /api/options took {elapsed:.3f}s"
