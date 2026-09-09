"""GET /api/planning: tracked assumptions, constraints and restraints, and their review."""
from __future__ import annotations

from reports_fixture import dorne_report
from test_review import BATCH, decide, ingest, range_claim_id


def planning(client, workspace, batch=BATCH):
    response = client.get("/api/planning", params={"batch": batch, "workspace": workspace})
    assert response.status_code == 200, response.text
    return response.json()


def by_id(body):
    return {o["object_id"]: o for o in body["objects"]}


def test_assumptions_are_seeded_with_their_grounding_span_validity_and_confidence(
    client, workspace_id
):
    objects = by_id(planning(client, workspace_id))
    k0 = objects["asm_blue_1_k0"]
    assert k0["kind"] == "assumption"
    assert k0["strategy_id"] == "str_blue_1"
    assert k0["subject_id"] == "sys_dorne_asm"
    assert k0["predicate"] == "range_km"
    assert k0["status"] in ("holds", "violated", "stale", "unknown")
    assert k0["review_status"] == "unreviewed"
    assert k0["provenance"] == "dataset"

    link = k0["source_links"][0]
    assert link["claim_id"].startswith("clm_")
    assert link["span_end"] > link["span_start"]
    assert link["span_text"]
    claim = client.get(
        f"/api/claims/{link['claim_id']}", params={"batch": BATCH, "workspace": workspace_id}
    ).json()["claim"]
    assert link["span_text"] == claim["span_text"]
    assert k0["validity"]["valid_from"] == claim["valid_from"]
    assert k0["confidence"]["confidence_icd203"] == claim["confidence_icd203"]


def test_constraints_and_restraints_are_sidecars_that_state_their_provenance_as_absent(
    client, workspace_id
):
    objects = by_id(planning(client, workspace_id))
    sidecars = [o for o in objects.values() if o["kind"] in ("constraint", "restraint")]
    assert sidecars, "the Blue options carry constraints and restraints"
    assert {o["kind"] for o in sidecars} == {"constraint", "restraint"}
    for record in sidecars:
        assert record["object_id"].startswith(("pcon_", "pres_"))
        assert record["source_links"] == []
        assert record["validity"] is None
        assert record["confidence"] is None
        assert record["review_status"] == "unreviewed"
        assert record["provenance"].startswith("absent:")
        assert record["text"]
    # The ids are stable across calls, so a review can key on them.
    assert by_id(planning(client, workspace_id)).keys() == objects.keys()


def test_a_review_is_recorded_with_actor_time_reason_and_source_links(client, workspace_id):
    objects = by_id(planning(client, workspace_id))
    target = next(o for o in objects.values() if o["kind"] == "restraint")
    claim_id = objects["asm_blue_1_k0"]["source_links"][0]["claim_id"]

    response = client.post(
        f"/api/planning/{target['object_id']}/review",
        params={"batch": BATCH, "workspace": workspace_id},
        json={
            "review_status": "reviewed",
            "actor": "the theater J-5",
            "reason": "confirmed against the OPORD",
            "source_links": [{"claim_id": claim_id}],
            "validity": {"valid_from": "2026-09-08", "valid_to": None},
        },
    )
    assert response.status_code == 200, response.text
    record = response.json()["object"]
    assert record["review_status"] == "reviewed"
    assert record["review"]["reviewed_by"] == "the theater J-5"
    assert record["review"]["reason"] == "confirmed against the OPORD"
    assert record["source_links"][0]["claim_id"] == claim_id
    assert record["validity"]["valid_from"] == "2026-09-08"
    assert len(record["review"]["history"]) == 1

    again = by_id(planning(client, workspace_id))[target["object_id"]]
    assert again["review_status"] == "reviewed"
    assert again["review"]["reviewed_at"]


def test_an_unknown_planning_object_is_404(client, workspace_id):
    response = client.post(
        "/api/planning/pcon_nothing_0/review",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"review_status": "reviewed", "actor": "the theater J-5"},
    )
    assert response.status_code == 404


def test_an_unknown_review_status_is_rejected(client, workspace_id):
    response = client.post(
        "/api/planning/asm_blue_1_k0/review",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"review_status": "approved-ish", "actor": "the theater J-5"},
    )
    assert response.status_code == 404
    assert "review_status must be one of" in response.json()["error"]["message"]


def test_accepted_evidence_flags_the_objects_it_touches_and_their_dependent_options(
    client, workspace_id
):
    body = ingest(client, workspace_id, dorne_report(260, "18 November 2026"))
    decision = decide(client, workspace_id, range_claim_id(body), reason="new imagery").json()
    flagged = {flag["object_id"]: flag for flag in decision["planning_flags"]}
    assert set(flagged) == {"asm_blue_1_k0", "asm_blue_2_k0"}
    for flag in flagged.values():
        assert flag["kind"] == "assumption"
        assert flag["claim_ids"] == [decision["claim"]["claim_id"]]
        assert "grounds this assumption" in flag["reason"]
    assert flagged["asm_blue_1_k0"]["dependent_options"] == ["str_blue_1"]
    assert flagged["asm_blue_2_k0"]["dependent_options"] == ["str_blue_2"]

    served = planning(client, workspace_id)
    assert {f["object_id"] for f in served["flags"]} == set(flagged)
    assert by_id(served)["asm_blue_1_k0"]["source_links"][0]["claim_id"].startswith("pclm_")


def test_a_reviewed_constraint_is_flagged_when_its_linked_claim_changes(
    client, workspace_id
):
    """An unreviewed sidecar has no links, so it is never flagged on a guess; a reviewed one
    with a link to the changed claim is."""
    body = ingest(client, workspace_id, dorne_report(260, "18 November 2026"))
    claim_id = range_claim_id(body)
    constraint = next(
        o for o in planning(client, workspace_id)["objects"] if o["kind"] == "constraint"
    )["object_id"]
    decide(client, workspace_id, claim_id, reason="new imagery")

    assert constraint not in {
        f["object_id"] for f in planning(client, workspace_id)["flags"]
    }
    client.post(
        f"/api/planning/{constraint}/review",
        params={"batch": BATCH, "workspace": workspace_id},
        json={
            "review_status": "needs_review", "actor": "the theater J-5",
            "reason": "the constraint depends on the missile range",
            "source_links": [{"claim_id": claim_id}],
        },
    )
    flags = {f["object_id"]: f for f in planning(client, workspace_id)["flags"]}
    assert constraint in flags
    assert "a reviewer linked" in flags[constraint]["reason"]
