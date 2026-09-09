"""`p_holds` comes from a claim, not from a constant.

Each of the eight OPORD planning assumptions is grounded by exactly one approved claim whose value
the assumption's tolerance is applied to. These tests prove the wiring both ways: the claim exists
and carries the assumption's own (subject, predicate), and changing that claim's value moves
`p_holds`, the assumption status and the value of every COA that depends on it.
"""
from __future__ import annotations

import copy

import pytest

BLUE_COAS = [f"str_coa_{i}" for i in range(1, 6)]

#: A value that fails each assumption's tolerance, so flipping the claim flips the assumption.
#: (See `scenario.ASSUMPTIONS` for the tolerances themselves.)
VIOLATING_VALUE = {
    0: "red_aligned",   # A1  alignment == blue_aligned
    1: False,           # A2  basing_access == True
    2: 4000,            # A3  range_km <= 2500
    3: 45,              # A4  mobilization_days <= 21
    4: 12,              # A5  throughput_per_day >= 30
    5: 0.95,            # A6  readiness <= 0.80
    6: 6,               # A7  mobilized_brigades <= 2
    7: "degraded",      # A8  status == operational
}


def _blue_assumptions(computed) -> dict[int, dict]:
    return {a["index_k"]: a for a in computed["assumptions"] if a["strategy_id"].startswith("str_coa")}


def test_every_assumption_is_grounded_by_a_claim_on_its_own_subject_and_predicate(computed, rows, S):
    claims = {c["claim_id"]: c for c in computed["claims"]}
    for k, aid, subject, predicate, *_ in S.ASSUMPTIONS:
        claim = claims[rows.grounding_claim_id(k)]
        assert (claim["subject_id"], claim["predicate"]) == (subject, predicate), aid
        assert claim["status"] == "approved"
        assert claim["truth_claim_id"], "the grounding claim must instantiate a fact (invariant 9)"
    red = claims[rows.claim_id(rows.RED_GROUNDING_KEY)]
    assert (red["subject_id"], red["predicate"]) == (S.RED_ASSUMPTION[1], S.RED_ASSUMPTION[2])


def test_the_grounding_edge_in_the_dependency_graph_names_that_claim(computed, rows):
    edges = {d["to_id"]: d for d in computed["dependencies"] if d["kind"] == "grounds"}
    for a in computed["assumptions"]:
        edge = edges[a["assumption_id"]]
        assert edge["from_type"] == "claim"
        if a["strategy_id"].startswith("str_coa"):
            assert edge["from_id"] == rows.grounding_claim_id(a["index_k"])
        assert edge["evidence_claim_ids"] == [edge["from_id"]]


def test_p_holds_is_the_derived_confidence_of_the_grounding_claim(computed, rows, value):
    """SCHEMA.md §1: p = confidence when the tolerance is satisfied, 1 - confidence when it is not.
    Nothing here is typed by hand."""
    claims = {c["claim_id"]: c for c in computed["claims"]}
    for k, a in _blue_assumptions(computed).items():
        claim = claims[rows.grounding_claim_id(k)]
        derived = value.derived_confidence(claim["estimative"], claim["likelihood_icd203"],
                                           claim["confidence_icd203"])
        assert claim["confidence"] == pytest.approx(derived)
        assert a["p_holds"] == pytest.approx(derived), f"A{k + 1}"
        assert a["status"] in {"holds", "stale"}


def test_low_confidence_evidence_makes_the_assumption_stale(computed, rows):
    claims = {c["claim_id"]: c for c in computed["claims"]}
    for k, a in _blue_assumptions(computed).items():
        low = claims[rows.grounding_claim_id(k)]["confidence_icd203"] == "low"
        assert (a["status"] == "stale") == low, f"A{k + 1}"
    stale = {k for k, a in _blue_assumptions(computed).items() if a["status"] == "stale"}
    assert stale, "no assumption is flagged for revalidation"


def test_the_ui_confidence_ordering_survives_the_move_to_evidence(computed):
    """The UI's tracker shows A1 and A8 high and A5 lowest. The evidence has to reproduce that
    ordering or the workbench and the demo screen disagree."""
    p = {k: a["p_holds"] for k, a in _blue_assumptions(computed).items()}
    assert p[4] == min(p.values()), "A5 is not the least supported assumption"
    assert p[0] > 0.8 and p[7] > 0.8, "A1 and A8 should be the well supported ones"
    assert p[0] > p[2] > p[4]


@pytest.mark.parametrize("k", sorted(VIOLATING_VALUE))
def test_changing_the_grounding_claim_moves_p_holds(build, authored, engine, rows, S, k):
    claims = copy.deepcopy(authored["claims"])
    target = next(c for c in claims if c["claim_id"] == rows.grounding_claim_id(k))
    before = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION)
    if target["value_type"] == "entity":
        target["object_id"] = VIOLATING_VALUE[k]
    else:
        target["value"] = VIOLATING_VALUE[k]
    after = engine.recompute(authored, S.AS_OF, S.WORLD_VERSION, claims=claims)

    a0 = _blue_assumptions(before)[k]
    a1 = _blue_assumptions(after)[k]
    assert a1["p_holds"] == pytest.approx(1.0 - a0["p_holds"]), f"A{k + 1} did not move"
    assert a1["status"] in {"violated", "stale"}
    if a0["status"] == "holds":
        assert a1["status"] == "violated"
    # and the change reaches the decision: every COA that depends on A(k+1) revalues.
    depends = [sid for sid, deps in ((c[0], c[4]) for c in S.COAS) if k + 1 in deps]
    assert depends, f"A{k + 1} is not a dependency of any COA"
    v0 = {s["strategy_id"]: s["value"] for s in before["strategies"]}
    v1 = {s["strategy_id"]: s["value"] for s in after["strategies"]}
    if a0["p_holds"] == pytest.approx(0.5):
        # A5 is a roughly-even-chance estimate held at high confidence, so p = 0.5 whether the
        # tolerance is met or not. The status flips and the value cannot: that is why A5 prices at
        # zero EVPI and why the JRAM forced-choice rule exists for exactly this estimate.
        assert k == 4 and a1["p_holds"] == pytest.approx(0.5)
        return
    for sid in depends:
        assert v1[sid] != pytest.approx(v0[sid]), f"{sid} did not revalue on A{k + 1}"


def test_the_theory_of_victory_waypoints_are_claims_in_the_corpus(computed, rows):
    claims = {c["claim_id"]: c for c in computed["claims"]}
    for key, objective_id in rows.TOV_OBJECTIVE.items():
        cid = rows.tov_claim_id(key)
        assert cid in claims, key
        assert claims[cid]["source_id"].startswith("src_")
    edges = [d for d in computed["dependencies"] if d["kind"] == "supports" and d["from_type"] == "claim"]
    assert {d["from_id"] for d in edges} == {rows.tov_claim_id(k) for k in rows.TOV_OBJECTIVE}
