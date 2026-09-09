"""Review: accepting a proposed claim recomputes the batch through the reference evaluator.

Every expected number in this file comes from calling ``eval.engine.recompute`` here, on the
same tables plus the accepted claim. Nothing is typed in.
"""
from __future__ import annotations

from datetime import date

import pytest
from reports_fixture import dorne_report

from app.backend.adapter import eval_module
from app.backend.product.store import Workspace

BATCH = 3


def ingest(client, workspace, text, filename="dorne.md", batch=BATCH):
    response = client.post(
        "/api/reports",
        params={"batch": batch, "workspace": workspace},
        json={"filename": filename, "actor": "analyst", "text": text},
    )
    assert response.status_code == 200, response.text
    return response.json()


def decide(client, workspace, claim_id, decision="accept", batch=BATCH, **body):
    return client.post(
        f"/api/claims/proposed/{claim_id}/decision",
        params={"batch": batch, "workspace": workspace},
        json={"decision": decision, "actor": "reviewer", **body},
    )


def range_claim_id(body: dict) -> str:
    return next(c["claim_id"] for c in body["proposed_claims"] if c["predicate"] == "range_km")


def oracle(adapter, workspace: str, as_of: str, batch: int = BATCH) -> dict:
    """What the reference evaluator says about this batch plus the accepted product claims."""
    recompute = eval_module("engine").recompute
    tables = adapter.snapshot(batch).tables
    accepted = [record["claim"] for record in Workspace(workspace).accepted_claims()]
    return recompute(
        tables, date.fromisoformat(as_of), batch, claims=tables["claims"] + accepted
    )


def blue_assumptions(tables: dict) -> dict[str, dict]:
    return {
        a["assumption_id"]: a
        for a in tables["assumptions"]
        if a["strategy_id"].startswith("str_blue")
    }


def blue_strategies(tables: dict) -> dict[str, dict]:
    return {
        s["strategy_id"]: s for s in tables["strategies"] if s["game_id"] == "meridian"
    }


@pytest.mark.parametrize("value_km", [360, 260])
def test_the_accepted_range_drives_the_assumption_and_the_values(
    client, adapter, workspace_id, value_km
):
    """The k0 grounding claim, varied. The assumption state and every value follow the
    accepted content, and match a direct recompute at the overlay's as-of date."""
    body = ingest(client, workspace_id, dorne_report(value_km, "18 November 2026"))
    response = decide(client, workspace_id, range_claim_id(body), reason="corroborated")
    assert response.status_code == 200, response.text
    decision = response.json()

    snapshot = client.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}
    ).json()
    assert snapshot["overlay_applied"] is True
    assert snapshot["batch_as_of"] == "2026-11-17"
    assert snapshot["as_of"] == "2026-11-20"  # the report's own date-time group
    assert snapshot["graph_version"] == 1

    expected = oracle(adapter, workspace_id, snapshot["as_of"])
    expected_assumptions = blue_assumptions(expected)
    served = {a["assumption_id"]: a for a in snapshot["assumptions"]}
    for assumption_id, row in expected_assumptions.items():
        assert served[assumption_id]["status"] == row["status"], assumption_id
        assert served[assumption_id]["p_holds"] == pytest.approx(row["p_holds"])

    expected_strategies = blue_strategies(expected)
    for strategy in snapshot["strategies"]:
        if strategy["strategy_id"] in expected_strategies:
            row = expected_strategies[strategy["strategy_id"]]
            assert strategy["value"] == pytest.approx(row["value"])
            assert strategy["status"] == row["status"]

    # The assumption follows the tolerance the dataset states, not a number typed here.
    k0 = expected_assumptions["asm_blue_1_k0"]
    satisfies = eval_module("claimset").satisfies
    tolerance = k0["tolerance"]
    holds = satisfies(value_km, tolerance["op"], tolerance["value"])
    assert (k0["status"] == "holds") is holds
    assert served["asm_blue_1_k0"]["status"] == k0["status"]
    assert decision["chosen_claim_id"].startswith("pclm_")


def test_the_two_reported_values_give_different_assumption_states_and_rankings(
    client, adapter, workspace_id
):
    """The same report with a different number is a different answer, not the same one."""
    states = {}
    values = {}
    for value_km in (360, 260):
        workspace = f"{workspace_id[:56]}_{value_km}"
        Workspace(workspace).reset()
        body = ingest(client, workspace, dorne_report(value_km, "18 November 2026"))
        decide(client, workspace, range_claim_id(body))
        snapshot = client.get(
            "/api/snapshot", params={"batch": BATCH, "workspace": workspace}
        ).json()
        states[value_km] = {
            a["assumption_id"]: a["status"] for a in snapshot["assumptions"]
        }["asm_blue_1_k0"]
        values[value_km] = {
            s["strategy_id"]: s["value"] for s in snapshot["strategies"]
        }["str_blue_1"]
    assert states[360] != states[260]
    assert values[360] != values[260]


def test_a_later_report_date_moves_the_evaluation_date_and_the_result_follows(
    client, adapter, workspace_id
):
    body = ingest(
        client, workspace_id,
        dorne_report(360, "24 November 2026", dtg="261000Z NOV 26"),
    )
    decide(client, workspace_id, range_claim_id(body))
    snapshot = client.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}
    ).json()
    assert snapshot["as_of"] == "2026-11-26"
    expected = oracle(adapter, workspace_id, "2026-11-26")
    served = {s["strategy_id"]: s for s in snapshot["strategies"]}
    for strategy_id, row in blue_strategies(expected).items():
        assert served[strategy_id]["value"] == pytest.approx(row["value"])
    risks = client.get("/api/risks", params={"batch": BATCH, "workspace": workspace_id}).json()
    expected_risks = {
        (r["he_id"], r["jsps_horizon"]): r for r in expected["risk_assessments"]
    }
    for event in risks["harmful_events"]:
        for horizon in event["horizons"]:
            row = expected_risks[(event["he_id"], horizon["jsps_horizon"])]
            assert horizon["risk_level"] == row["risk_level"]
            assert horizon["p_raw"] == pytest.approx(row["p_raw"])


def test_a_contradictory_accepted_claim_leaves_both_visible_and_names_the_chosen_one(
    client, workspace_id
):
    body = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    claim_id = range_claim_id(body)
    decision = decide(client, workspace_id, claim_id, reason="new imagery").json()

    assert decision["contradicts"] == ["clm_0844"]
    assert "both remain visible" in decision["contradiction_reason"]
    assert decision["chosen_claim_id"] == claim_id

    claims = client.get(
        "/api/claims",
        params={"batch": BATCH, "workspace": workspace_id, "entity": "sys_dorne_asm",
                "limit": 100},
    ).json()["claims"]
    by_id = {c["claim_id"]: c for c in claims}
    assert claim_id in by_id and "clm_0844" in by_id
    assert by_id["clm_0844"]["status"] == "approved"  # dataset evidence is not overwritten
    assert by_id[claim_id]["status"] == "approved"
    assert by_id[claim_id]["flags"]["contradiction"] is True
    assert "clm_0844" in by_id[claim_id]["flags"]["contradicts_claim_ids"]
    assert claim_id in by_id["clm_0844"]["flags"]["contradicts_claim_ids"]

    trace = client.get(
        f"/api/claims/{claim_id}", params={"batch": BATCH, "workspace": workspace_id}
    ).json()
    assert trace["claim"]["span_text"].endswith("as of 18 November 2026.")
    assert any(
        path["nodes"][-1]["type"] == "strategy" for path in trace["trace"]["paths"]
    )


def test_rejecting_a_claim_records_the_decision_and_changes_no_evaluation(
    client, workspace_id
):
    body = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    before = client.get("/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}).json()
    response = decide(
        client, workspace_id, range_claim_id(body), decision="reject",
        reason="single source, not corroborated",
    )
    assert response.status_code == 200
    decision = response.json()
    assert decision["graph_version"] == 0
    assert decision["changes"]["assumptions_changed"] == []
    after = client.get("/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}).json()
    assert after["strategies"] == before["strategies"]
    assert "overlay_applied" not in after

    audit = client.get("/api/workspace", params={"workspace": workspace_id}).json()
    assert audit["rejected_claims"] == 1
    assert any(entry["action"] == "claim_rejected" for entry in audit["audit"])


def test_a_claim_the_report_does_not_fully_state_needs_a_reviewer_revision(
    client, workspace_id
):
    from reports_fixture import STRAIT_TRAFFIC

    body = ingest(client, workspace_id, STRAIT_TRAFFIC, filename="strait.md")
    incomplete = next(
        c for c in body["proposed_claims"] if "confidence_missing" in c["flags"]
    )
    response = decide(client, workspace_id, incomplete["claim_id"])
    assert response.status_code == 422
    error = response.json()["error"]
    assert "confidence_icd203" in error["detail"]["missing"]
    assert "Nothing is filled in for you" in error["message"]

    fixed = decide(
        client, workspace_id, incomplete["claim_id"],
        reason="confidence rated by the reviewer",
        revision={"confidence_icd203": "moderate"},
    )
    assert fixed.status_code == 200
    assert fixed.json()["decision"]["revision"] == {"confidence_icd203": "moderate"}
    assert fixed.json()["claim"]["confidence_icd203"] == "moderate"


def test_a_second_decision_on_the_same_claim_is_409(client, workspace_id):
    body = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    claim_id = range_claim_id(body)
    assert decide(client, workspace_id, claim_id).status_code == 200
    again = decide(client, workspace_id, claim_id, decision="reject")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "already_decided"


def test_an_unknown_proposed_claim_is_404(client, workspace_id):
    response = decide(client, workspace_id, "pclm_9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"
