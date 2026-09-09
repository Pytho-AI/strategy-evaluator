"""GET /api/risks, checked against a direct eval.engine.recompute of the same batch."""
from __future__ import annotations

from datetime import date

import pytest

BATCHES = (0, 1, 2, 3)


def risks(client, batch: int) -> dict:
    response = client.get("/api/risks", params={"batch": batch})
    assert response.status_code == 200
    return response.json()


def horizons(body: dict) -> dict:
    return {
        (he["he_id"], h["jsps_horizon"]): h
        for he in body["harmful_events"]
        for h in he["horizons"]
    }


@pytest.fixture(scope="module")
def recomputed(adapter):
    """A direct engine.recompute over each batch's tables: the API's independent oracle."""
    from eval.engine import recompute

    out = {}
    for batch in BATCHES:
        snapshot = adapter.snapshot(batch)
        tables = recompute(snapshot.tables, date.fromisoformat(snapshot.as_of), batch)
        out[batch] = {
            (r["he_id"], r["jsps_horizon"]): r for r in tables["risk_assessments"]
        }
    return out


@pytest.mark.parametrize("batch", BATCHES)
def test_every_assessment_equals_a_direct_recompute(client, recomputed, batch):
    served = horizons(risks(client, batch))
    assert set(served) == set(recomputed[batch])
    for key, row in served.items():
        expected = recomputed[batch][key]
        for field in (
            "p_raw", "p_level", "c_level", "risk_level", "trend", "statement_text",
            "forced_choice_applied", "posture_rationale", "dominant_driver_id",
        ):
            assert row[field] == expected[field], f"{key} {field}"
        assert [d["driver_id"] for d in row["active_drivers"]] == expected[
            "active_driver_ids"
        ]


def test_the_batch_3_forced_choice_fires_on_he_05_and_he_06(client, recomputed):
    """A roughly-even-chance estimate maps to a JRAM level through friendly posture."""
    served = horizons(risks(client, 3))
    forced = sorted({key[0] for key, row in served.items() if row["forced_choice_applied"]})
    assert forced == ["he_05", "he_06"]
    assert sorted(
        {key[0] for key, row in recomputed[3].items() if row["forced_choice_applied"]}
    ) == forced
    for he_id in forced:
        for horizon in ("near", "mid", "long"):
            row = served[(he_id, horizon)]
            assert row["posture_rationale"], "invariant 19: a forced row states its posture"
            assert row["posture_rationale"] == recomputed[3][(he_id, horizon)][
                "posture_rationale"
            ]
            assert row["p_level"] == "likely"
            dominant = next(d for d in row["active_drivers"] if d["dominant"])
            assert dominant["claims"], "the dominant driver names the claim that fired it"
            assert "roughly_even_chance" in {
                c["likelihood_icd203"] for c in dominant["claims"]
            }
    assert served[("he_05", "near")]["risk_level"] == "significant"


def test_no_forced_choice_before_batch_3(client):
    for batch in (0, 1, 2):
        assert not [
            key for key, row in horizons(risks(client, batch)).items()
            if row["forced_choice_applied"]
        ]


@pytest.mark.parametrize("batch", BATCHES)
def test_problem_sets_carry_their_risk_context_and_per_horizon_level(client, batch):
    body = risks(client, batch)
    assert {p["problem_set_id"] for p in body["problem_sets"]} == {
        "ps_chokepoint", "ps_energy", "ps_cyber", "ps_humanitarian",
    }
    for problem_set in body["problem_sets"]:
        assert [h["jsps_horizon"] for h in problem_set["horizons"]] == [
            "near", "mid", "long",
        ]
        for horizon in problem_set["horizons"]:
            assert horizon["aggregated_statement_text"]
            assert horizon["he_ids"]
        for field in (
            "strategic_context", "scope_and_boundaries", "assumptions_and_constraints",
            "expected_outputs", "tolerance_statement", "risk_owner_role",
        ):
            assert problem_set[field], field
        assert problem_set["thing_of_value_names"]


def test_problem_set_levels_are_the_max_of_their_events(client):
    body = risks(client, 3)
    events = horizons(body)
    for problem_set in body["problem_sets"]:
        for horizon in problem_set["horizons"]:
            levels = {
                events[(he_id, horizon["jsps_horizon"])]["risk_level"]
                for he_id in horizon["he_ids"]
            }
            assert horizon["max_risk_level"] in levels


def test_consequence_basis_states_msr_or_mr_inputs(client):
    for event in risks(client, 0)["harmful_events"]:
        basis = event["consequence_basis"]
        if event["risk_type"] == "MSR":
            assert basis["basis"] == "msr"
            assert basis["strategic_value"] and basis["damage_degree"]
        else:
            assert basis["basis"] == "mr"
            assert basis["fig28_row"] and basis["fig28_cell"]
            assert event["risk_subset"]


def test_the_cascade_reports_edges_and_upstream_paths(client):
    body = risks(client, 3)
    events = {e["he_id"]: e for e in body["harmful_events"]}
    assert len(body["escalation_edges"]) == 6
    assert all(e["from_statement"] and e["to_statement"] for e in body["escalation_edges"])
    blackout = events["he_04"]["cascade"]
    assert ["he_05", "he_04"] in blackout["upstream_paths"]
    assert ["he_06", "he_03", "he_04"] in blackout["upstream_paths"]
    assert {e["edge_id"] for e in blackout["upstream_edges"]} == {"ee_0005", "ee_0006"}
    assert events["he_05"]["cascade"]["upstream_paths"] == []
    assert [e["to_he_id"] for e in events["he_05"]["cascade"]["downstream_edges"]] == [
        "he_04"
    ]


def test_active_drivers_name_the_claims_that_satisfy_them(client):
    body = risks(client, 1)
    strait = next(e for e in body["harmful_events"] if e["he_id"] == "he_01")
    near = next(h for h in strait["horizons"] if h["jsps_horizon"] == "near")
    reach = next(d for d in near["active_drivers"] if d["driver_id"] == "rd_0001")
    assert reach["claim_subject_name"] and reach["driver_kind"] == "accessibility"
    values = {c["value"] for c in reach["claims"]}
    assert values and all(value >= reach["value"] for value in values)
    assert near["risk_level"] == "significant"


def test_sources_of_risk_resolve_to_entity_names(client):
    for event in risks(client, 0)["harmful_events"]:
        for source in event["sources_of_risk"]:
            assert source["source_kind"] in {"threat", "hazard"}
            assert source["entity_name"] and source["entity_name"] != source["entity_id"]
