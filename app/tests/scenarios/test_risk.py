"""The JRAM risk model is computed from the same claims the assumptions read.

Covers: the eight problem sets match the UI's clusters and carry the six Fig. 3 paragraphs; every
harmful event is typed and priced; drivers reference claims that exist, so evidence moves `p_raw`;
the escalation edges form a DAG and a driver change reaches a downstream problem set through one;
the forced-choice rule fires on the one roughly-even-chance estimate; and exactly one Military Risk
event is assessed High, which is what makes the JP 5-0 acceptable test bite.
"""
from __future__ import annotations

import copy

import pytest

UI_PROBLEM_SETS = ["ps_consensus", "ps_force_flow", "ps_iamd", "ps_closure",
                   "ps_spod", "ps_escalation", "ps_suwalki", "ps_c2"]
FIG3_PARAGRAPHS = ("risk_owner_role", "strategic_context", "scope_and_boundaries",
                   "tolerance_statement", "assumptions_and_constraints", "expected_outputs")


def _near(computed) -> dict[str, dict]:
    return {r["he_id"]: r for r in computed["risk_assessments"] if r["jsps_horizon"] == "near"}


def _levels(tables, horizon="near") -> dict[str, str]:
    return {r["problem_set_id"]: r["max_risk_level"]
            for r in tables["problem_set_assessments"] if r["jsps_horizon"] == horizon}


# ---------------------------------------------------------------- problem sets
def test_eight_problem_sets_one_per_ui_cluster(computed):
    assert [p["problem_set_id"] for p in computed["problem_sets"]] == UI_PROBLEM_SETS
    entities = {e["entity_id"] for e in computed["entities"] if e["entity_type"] == "problem_set"}
    for p in computed["problem_sets"]:
        assert p["entity_id"] in entities
        assert p["tier"] == 0
        assert p["thing_of_value_ids"], p["problem_set_id"]


def test_every_problem_set_carries_the_six_figure_3_paragraphs(computed):
    objectives = {o["objective_id"]: o for o in computed["objectives"]}
    for p in computed["problem_sets"]:
        for field in FIG3_PARAGRAPHS:
            text = p[field]
            assert text and not text.startswith("PLACEHOLDER"), f"{p['problem_set_id']}.{field}"
            floor = 4 if field == "risk_owner_role" else 12  # the owner is a role, not a paragraph
            assert len(text.split()) >= floor, f"{p['problem_set_id']}.{field} is a stub"
        for oid in p["thing_of_value_ids"]:
            assert objectives[oid]["kind"] == "objective", "a thing of value must be an objective"


def test_every_problem_set_has_events_and_an_aggregated_statement(computed):
    by_set: dict[str, list[str]] = {}
    for he in computed["harmful_events"]:
        by_set.setdefault(he["problem_set_id"], []).append(he["he_id"])
    for p in computed["problem_sets"]:
        assert 2 <= len(by_set[p["problem_set_id"]]) <= 3, p["problem_set_id"]
    for r in computed["problem_set_assessments"]:
        assert r["aggregated_statement_text"].startswith("If the following related harmful events")
        assert r["max_risk_level"] in {"low", "moderate", "significant", "high"}


# ---------------------------------------------------------------- harmful events
def test_events_are_typed_and_scored_against_the_right_matrix(computed):
    for he in computed["harmful_events"]:
        assert he["risk_type"] in {"MSR", "MR"}
        if he["risk_type"] == "MSR":
            assert he["strategic_value"] and he["damage_degree"]
            assert he["fig28_row"] is None and he["fig28_cell"] is None
        else:
            assert he["risk_subset"] and he["fig28_row"] and he["fig28_cell"]
            assert he["strategic_value"] is None and he["damage_degree"] is None
        assert 0.0 < he["base_p"] < 1.0
        assert he["condition"] in {"action", "inaction", "posture", "plan"}
    assert {he["risk_type"] for he in computed["harmful_events"]} == {"MSR", "MR"}


def test_every_event_names_a_threat_or_a_hazard(computed):
    covered = {rs["he_id"] for rs in computed["risk_sources"]}
    assert covered == {he["he_id"] for he in computed["harmful_events"]}
    kinds = {rs["source_kind"] for rs in computed["risk_sources"]}
    assert kinds == {"threat", "hazard"}, "sources of risk are all one kind"


# ---------------------------------------------------------------- drivers
def test_every_driver_references_a_claimable_subject_and_predicate(computed):
    keys = {(c["subject_id"], c["predicate"]) for c in computed["claims"]}
    for d in computed["risk_drivers"]:
        assert (d["claim_subject_id"], d["claim_predicate"]) in keys, d["driver_id"]
        assert d["label"] and not d["label"].startswith("PLACEHOLDER")
        assert -1.0 <= d["delta"] <= 1.0


def test_most_drivers_are_firing_and_some_are_watching(computed):
    """A driver that is not satisfied today is not dead weight: it is the indicator the assessment
    is watching. But if none were firing, `p_raw` would just be `base_p`."""
    active = {d for r in computed["risk_assessments"] for d in r["active_driver_ids"]}
    all_ids = {d["driver_id"] for d in computed["risk_drivers"]}
    assert active, "no driver is satisfied by the evidence"
    assert all_ids - active, "every driver fires; nothing is left to watch for"


def test_p_raw_is_base_p_plus_the_active_deltas_before_cascade(computed):
    """Events with no incoming escalation edge have no cascade term, so the arithmetic is visible."""
    downstream = {e["to_he_id"] for e in computed["escalation_edges"]}
    deltas = {d["driver_id"]: d["delta"] for d in computed["risk_drivers"]}
    events = {he["he_id"]: he for he in computed["harmful_events"]}
    checked = 0
    for r in _near(computed).values():
        if r["he_id"] in downstream:
            continue
        expected = events[r["he_id"]]["base_p"] + sum(deltas[d] for d in r["active_driver_ids"])
        assert r["p_raw"] == pytest.approx(min(0.99, max(0.01, expected))), r["he_id"]
        checked += 1
    assert checked >= 10


def test_changing_a_driver_claim_moves_the_probability(build, authored, engine, S):
    claims = copy.deepcopy(authored["claims"])
    target = next(c for c in claims if c["claim_id"] == "clm_ev_fleet_readiness")
    target["value"] = 0.55  # the fleet stands down: rd_spod_fleet stops firing
    after = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION, claims=claims)
    before = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION)
    assert _near(after)["he_spod_closed"]["p_raw"] < _near(before)["he_spod_closed"]["p_raw"]
    assert _levels(before)["ps_spod"] == "high"
    assert _levels(after)["ps_spod"] == "significant"


# ---------------------------------------------------------------- cascade
def test_escalation_edges_form_a_dag_across_problem_sets(computed):
    from eval.jram import topological_order

    events = {he["he_id"]: he for he in computed["harmful_events"]}
    edges = [(e["from_he_id"], e["to_he_id"]) for e in computed["escalation_edges"]]
    topological_order(list(events), edges)  # raises on a cycle
    assert len(edges) >= 5
    crossing = [(a, b) for a, b in edges if events[a]["problem_set_id"] != events[b]["problem_set_id"]]
    assert len(crossing) >= 4, "the cascade stays inside single problem sets"
    for e in computed["escalation_edges"]:
        assert 0.0 < e["lift"] <= 1.0
        assert len(e["mechanism"].split()) >= 8, e["edge_id"]
        assert e["evidence_claim_ids"], e["edge_id"]


def test_escalation_evidence_claims_exist(computed):
    ids = {c["claim_id"] for c in computed["claims"]}
    for e in computed["escalation_edges"]:
        assert set(e["evidence_claim_ids"]) <= ids, e["edge_id"]


def test_a_driver_change_moves_a_downstream_problem_set_through_a_cascade_edge(build, authored, engine, S):
    """Raise the Iskander brigade's readiness past the launch-ready alert threshold. That fires
    `rd_demo_alert` in the escalation problem set, and the `ee_demo_consensus` edge carries it into
    the consensus problem set, which crosses from Moderate to Significant. Nothing about the
    consensus problem set's own evidence changed."""
    before = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION)
    claims = copy.deepcopy(authored["claims"])
    next(c for c in claims if c["claim_id"] == "clm_a6")["value"] = 0.92
    after = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION, claims=claims)

    edge = next(e for e in authored["escalation_edges"] if e["edge_id"] == "ee_demo_consensus")
    assert (edge["from_he_id"], edge["to_he_id"]) == ("he_esc_demonstration", "he_consensus_fracture")
    assert _near(after)["he_esc_demonstration"]["p_raw"] > _near(before)["he_esc_demonstration"]["p_raw"]
    assert _near(after)["he_consensus_fracture"]["p_raw"] > _near(before)["he_consensus_fracture"]["p_raw"]
    assert _levels(before)["ps_consensus"] == "moderate"
    assert _levels(after)["ps_consensus"] == "significant"
    # the consensus problem set's own drivers are untouched
    assert _near(before)["he_consensus_narrative"]["p_raw"] == _near(after)["he_consensus_narrative"]["p_raw"]


def test_the_belarus_claim_reaches_the_corridor_and_beyond(build, authored, engine, S):
    """The other cascade the demo leans on: one more mobilized Belarusian brigade takes the
    Suwalki problem set up a level and still moves force flow and closure downstream."""
    before = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION)
    claims = copy.deepcopy(authored["claims"])
    next(c for c in claims if c["claim_id"] == "clm_a7")["value"] = 3
    after = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION, claims=claims)
    assert _levels(before)["ps_suwalki"] == "moderate"
    assert _levels(after)["ps_suwalki"] == "significant"
    for he_id in ("he_suwalki_closed", "he_flow_rail_slip", "he_closure_c21"):
        assert _near(after)[he_id]["p_raw"] > _near(before)[he_id]["p_raw"], he_id


# ---------------------------------------------------------------- levels and the forced choice
def test_exactly_one_military_risk_event_is_assessed_high(computed):
    events = {he["he_id"]: he for he in computed["harmful_events"]}
    high_mr = sorted({r["he_id"] for r in computed["risk_assessments"]
                      if r["risk_level"] == "high" and events[r["he_id"]]["risk_type"] == "MR"})
    assert high_mr == ["he_spod_closed"]
    row = _near(computed)["he_spod_closed"]
    assert (row["p_level"], row["c_level"]) == ("very_likely", "extreme")


def test_the_risk_levels_are_spread_across_the_contour(computed):
    levels = _levels(computed)
    assert set(levels) == set(UI_PROBLEM_SETS)
    assert len(set(levels.values())) >= 3, f"the board is flat: {levels}"
    assert levels["ps_spod"] == "high"


def test_the_forced_choice_rule_fires_on_the_one_coin_flip_estimate(computed):
    forced = [r for r in computed["risk_assessments"] if r["forced_choice_applied"]]
    assert forced, "no assessment reached the JRAM forced-choice rule"
    assert {r["he_id"] for r in forced} == {"he_spod_throughput"}
    for r in forced:
        assert r["posture_rationale"], r["he_id"]
        assert "Roughly even chance" in r["posture_rationale"]
    he = next(x for x in computed["harmful_events"] if x["he_id"] == "he_spod_throughput")
    assert he["posture_subject_ids"], "the forced choice needs friendly posture factors"
    postures = {(c["subject_id"], c["value"]) for c in computed["claims"] if c["predicate"] == "posture_state"}
    for pid in he["posture_subject_ids"]:
        assert any(s == pid for s, _ in postures), pid


def test_the_trend_is_computed_and_not_uniformly_flat(computed):
    trends = {r["trend"] for r in computed["risk_assessments"]}
    assert trends <= {"up", "down", "flat"}
    assert trends != {"flat"}, "no event trends: the horizon windows do nothing"
