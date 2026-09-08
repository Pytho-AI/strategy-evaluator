"""Regression checks for temporal evaluation, validity gates, and negative examples."""
import copy
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dataset"))

from eval import engine, style_check, validity, value
from eval.claimset import ClaimSet
from gen import rps, validate
from gen.context import Ctx, T0


@pytest.fixture
def tables(tmp_path):
    ctx = Ctx(20260908, tmp_path)
    rps.build(ctx)
    return ctx.tables


def test_transaction_time_blocks_future_assertions(tables):
    claim = copy.deepcopy(tables["claims"][0])
    claim["asserted_at"] = "2026-10-01"
    cs = ClaimSet([claim])
    assert cs.current(claim["subject_id"], claim["predicate"], T0) is None
    assert cs.in_window(claim["subject_id"], claim["predicate"], T0, date(2027, 1, 1), known_at=T0) == []
    assumption = next(a for a in tables["assumptions"] if a["subject_id"] == claim["subject_id"])
    assert value.assumption_state(cs, assumption, T0)[:2] == (0.5, "unknown")


def test_external_claims_get_derived_confidence(tables):
    supplied = copy.deepcopy(tables["claims"])
    for c in supplied:
        c["confidence"] = 0.1
    result = engine.recompute(tables, T0, 0, claims=supplied)
    assert all(a["p_holds"] == 0.97 for a in result["assumptions"])
    assert all(c["confidence"] == 0.1 for c in supplied)


def test_high_risk_does_not_cross_game_or_actor(tables, monkeypatch):
    tables["objectives"].append({"objective_id": "obj_other", "game_id": "other", "actor_id": "ent_other"})
    tables["harmful_events"] = [{"he_id": "he_other", "risk_type": "MR", "thing_of_value_id": "obj_other"}]
    monkeypatch.setattr(engine, "assess_risk", lambda *args: ([{"he_id": "he_other", "risk_level": "high"}], []))
    result = engine.recompute(tables, T0, 0)
    uniform = next(s for s in result["strategies"] if s["strategy_id"] == "str_rps_p1_uniform")
    assert uniform["validity"]["acceptable"]["pass"]


def test_infeasible_strategy_cannot_create_evpi(tables):
    paper = next(s for s in tables["strategies"] if s["strategy_id"] == "str_rps_p1_paper")
    next(a for a in tables["actions"] if a["action_id"] == "act_rps_p1_paper_commit")["cost"] = {"res_absent": 1}
    result = engine.recompute(tables, T0, 0)
    assert next(s for s in result["strategies"] if s["strategy_id"] == paper["strategy_id"])["status"] == "infeasible"
    assert all(a["evpi"] == 0 for a in result["assumptions"])


def test_impossible_rules_have_no_resource_cost():
    rules = [{"action_id": "act_never", "condition": False}]
    assert validity.test_feasible({}, rules, {"act_never": {"cost": {"res_fuel": 10}}}, {}, 2)[0]


def test_zero_cvar_mass_is_rejected():
    with pytest.raises(ValueError, match="alpha"):
        value.rho_apply([(0.5, 1), (0.5, 2)], "cvar", 0)


def test_mixed_scale_exception_preserves_other_failures(tables, monkeypatch, tmp_path):
    tables["sources"][0]["perturbations"] = ["mixed_scale"]
    monkeypatch.setattr(style_check, "check_file", lambda *a, **k: [
        style_check.Violation(3, "13", "mixed scale"), style_check.Violation(4, "11", "bad marking")])
    assert validate.inv13_mixed_scale(tables, tmp_path).passed
    assert not validate.inv11_markings(tables, tmp_path).passed
    assert validate.inv12_likelihood_confidence(tables, tmp_path).passed


def test_mixed_scale_label_requires_actual_detection(tables, monkeypatch, tmp_path):
    tables["sources"][0]["perturbations"] = ["mixed_scale"]
    monkeypatch.setattr(style_check, "check_file", lambda *a, **k: [])
    assert not validate.inv13_mixed_scale(tables, tmp_path).passed


def test_phase_subset_does_not_run_other_invariants(tables, monkeypatch, tmp_path):
    def unexpected(**kwargs):
        pytest.fail("unselected invariant executed")
    monkeypatch.setattr(validate, "ALL", [unexpected, validate.inv02_spans, unexpected, unexpected, validate.inv05_rule_probabilities])
    assert [r.id for r in validate.run_all(tables, tmp_path, T0, 0, only={"05"})] == ["05"]


def test_shared_assumption_index_requires_identical_proposition(tables):
    tables["assumptions"][1]["tolerance"] = {"op": "abs_le", "value": 0.4}
    assert not validate.inv09_grounding(tables).passed


def test_schema_validation_rejects_mistyped_values_and_negative_costs(tables):
    tables["claims"][0]["value"] = "not a number"
    tables["actions"][0]["cost"] = {"res_bad": -1}
    assert not validate.schema_load(tables).passed


def test_policy_cannot_use_another_actors_action(tables):
    tables["policy_rules"][0]["action_id"] = "act_rps_p2_rock"
    assert not validate.inv01_referential_integrity(tables).passed


def test_policy_cannot_observe_an_undeclared_variable(tables):
    tables["policy_rules"][0]["condition"] = {"var": "opponent_hand", "op": "==", "value": "rock"}
    assert not validate.inv01_referential_integrity(tables).passed


def test_opponent_distribution_cannot_repeat_a_strategy(tables):
    mix = tables["opponent_models"][0]["distribution"]
    mix[0]["probability"] = 0.5
    mix.append(copy.deepcopy(mix[0]))
    assert not validate.inv01_referential_integrity(tables).passed


def test_objective_ratings_preserve_ties():
    assert engine.ordinal_rating(0.5, [0.1, 0.5, 0.5, 0.9]) == 2
    assert engine.ordinal_rating(0.9, [0.1, 0.5, 0.5, 0.9]) == 3
    assert engine.ordinal_rating(0.5, [0.5, 0.5]) == 3
