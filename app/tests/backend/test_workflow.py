"""The collection workflow: draft, route, status, satisfaction on reviewed evidence, reopening."""
from __future__ import annotations

from test_review import decide, ingest, BATCH

CORVANE_ACCESS = """Date-time group: 201430Z NOV 26
From: the embassy country team
Subject: Corvane access

1. Corvane grants Blue basing access as of 19 November 2026, valid until 22 November 2026.
2. Confidence is moderate.
"""

LANE_61 = """Date-time group: 211200Z NOV 26
From: Task Group Kestrel

1. The Kestrel Strait sea lane carries 61 transits per day as of 20 November 2026.
2. Confidence is high.
"""

LANE_58 = """Date-time group: 231200Z NOV 26
From: Task Group Kestrel

1. The Kestrel Strait sea lane carries 58 transits per day as of 22 November 2026.
2. Confidence is high.
"""

SERATH_RANGE = """Date-time group: 241200Z NOV 26
From: the theater JIOC

1. The Serath long-range strike system has a maximum range of 420 km as of 23 November 2026.
2. Confidence is moderate.
"""


def draft(client, workspace, *, batch=BATCH, **body):
    payload = {
        "actor": "collection manager",
        "gap_type": "missing",
        "required_evidence": "a reported grant or refusal of basing access at Halden",
        "gap_reason": "the option's basing assumption has no claim valid at the as-of date",
        "proposed_owner": "the theater JIOC",
        "ltiov": "2026-12-01",
        "strategy_question": "Can str_blue_1 stage from Halden?",
        **body,
    }
    return client.post(
        "/api/collection/drafts", params={"batch": batch, "workspace": workspace}, json=payload
    )


def requirement(client, workspace, req_id, batch=BATCH):
    rows = client.get(
        "/api/collection", params={"batch": batch, "workspace": workspace}
    ).json()["requirements"]
    return next(r for r in rows if r["req_id"] == req_id)


def claim_id_for(body, predicate):
    return next(c["claim_id"] for c in body["proposed_claims"] if c["predicate"] == predicate)


# ---------------------------------------------------------------- drafting
def test_a_draft_needs_an_explicit_strategy_question_or_pir(client, workspace_id):
    response = draft(
        client, workspace_id, strategy_question=None, assumption_id="asm_blue_1_k2"
    )
    assert response.status_code == 422
    assert response.json()["error"]["detail"]["missing"] == [
        "strategy_question", "pir_id"
    ]


def test_a_draft_needs_a_gap(client, workspace_id):
    response = draft(client, workspace_id, subject_id=None, predicate=None)
    assert response.status_code == 422
    assert "subject_id" in response.json()["error"]["detail"]["missing"]


def test_a_draft_records_the_gap_the_link_and_the_owner(client, workspace_id):
    response = draft(client, workspace_id, assumption_id="asm_blue_1_k2", pir_id="pir_01")
    assert response.status_code == 200, response.text
    row = response.json()["requirement"]
    assert row["req_id"] == "preq_0001"
    assert row["owner"] == "product"
    assert row["status"] == "research"
    assert row["subject_id"] == "ent_corvane"
    assert row["predicate"] == "basing_access"
    assert row["gap_type"] == "missing"
    assert row["assumption"]["assumption_id"] == "asm_blue_1_k2"
    assert row["product"]["strategy_id"] == "str_blue_1"
    assert row["product"]["proposed_owner"] == "the theater JIOC"
    assert row["product"]["required_evidence"].startswith("a reported grant")
    assert row["product"]["status_history"][0]["status"] == "research"
    assert row["closure_basis"] is None
    # It is ranked by the same JIPCL rule the dataset requirements are ranked by.
    assert row["priority"] is not None and row["jipcl_rank"] is not None


def test_dataset_requirements_stay_read_only_replay_rows_alongside_product_ones(
    client, workspace_id
):
    draft(client, workspace_id, assumption_id="asm_blue_1_k2")
    rows = client.get(
        "/api/collection", params={"batch": BATCH, "workspace": workspace_id}
    ).json()["requirements"]
    dataset_rows = [r for r in rows if r["req_id"].startswith("req_")]
    product_rows = [r for r in rows if r["req_id"].startswith("preq_")]
    assert dataset_rows and product_rows
    assert all("owner" not in r for r in dataset_rows)
    assert all(r["owner"] == "product" for r in product_rows)
    ranked = [r["jipcl_rank"] for r in rows if r["jipcl_rank"] is not None]
    assert ranked == sorted(ranked) == list(range(1, len(ranked) + 1))

    for req_id in ("req_01", "req_99"):
        response = client.post(
            f"/api/collection/{req_id}/route",
            params={"batch": BATCH, "workspace": workspace_id},
            json={"queue": "JIOC", "actor": "collection manager"},
        )
        assert response.status_code == 404
        assert "read-only replay rows" in response.json()["error"]["message"]


def test_a_repeated_draft_for_the_same_gap_returns_the_open_one_and_records_duplicate_of(
    client, workspace_id
):
    first = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()
    second = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()
    assert second["requirement"]["req_id"] == first["requirement"]["req_id"]
    assert second["duplicate_of"] == first["requirement"]["req_id"]
    assert second["decision"]["decision"] == "duplicate_of"
    assert second["decision"]["actor"] == "collection manager"
    rows = client.get(
        "/api/collection", params={"batch": BATCH, "workspace": workspace_id}
    ).json()["requirements"]
    assert len([r for r in rows if r["req_id"].startswith("preq_")]) == 1


# ---------------------------------------------------------------- routing and status
def test_routing_assigns_a_queue_and_the_authority_tier(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    response = client.post(
        f"/api/collection/{req_id}/route",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"queue": "JIOC", "actor": "collection manager", "reason": "theater asset"},
    )
    assert response.status_code == 200, response.text
    row = response.json()["requirement"]
    assert row["routing"] == "JIOC"
    assert row["status"] == "submission"
    assert row["product"]["authority_tier_id"] == "tier_3"
    assert row["routing_authority"]["recommendation_type"] == "requirement_submit"
    assert row["product"]["status_history"][-1]["reason"] == "theater asset"

    bad = client.post(
        f"/api/collection/{req_id}/route",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"queue": "an external partner", "actor": "collection manager"},
    )
    assert bad.status_code == 422
    assert "JIOC, JCMB" in bad.json()["error"]["message"]


def test_a_unit_j2_queue_is_accepted(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    response = client.post(
        f"/api/collection/{req_id}/route",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"queue": "Task Group Kestrel J-2", "actor": "collection manager"},
    )
    assert response.status_code == 200
    assert response.json()["requirement"]["routing"] == "Task Group Kestrel J-2"


def test_satisfaction_cannot_be_set_by_hand(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    response = client.post(
        f"/api/collection/{req_id}/status",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"status": "satisfaction", "actor": "collection manager"},
    )
    assert response.status_code == 422
    assert "only when an accepted claim" in response.json()["error"]["message"]

    ok = client.post(
        f"/api/collection/{req_id}/status",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"status": "validation", "actor": "collection manager", "reason": "RFI raised"},
    )
    assert ok.status_code == 200
    assert ok.json()["requirement"]["status"] == "validation"


# ---------------------------------------------------------------- satisfaction
def test_document_arrival_alone_leaves_the_requirement_open(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    client.post(
        f"/api/collection/{req_id}/route",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"queue": "JIOC", "actor": "collection manager"},
    )
    body = ingest(client, workspace_id, CORVANE_ACCESS, filename="corvane.md")
    assert any(c["predicate"] == "basing_access" for c in body["proposed_claims"])
    row = requirement(client, workspace_id, req_id)
    assert row["status"] == "submission"
    assert row["closure_basis"] is None
    assert row["product"]["satisfied_by_claim_id"] is None


def test_accepted_evidence_closes_the_requirement_on_reviewed_evidence(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    body = ingest(client, workspace_id, CORVANE_ACCESS, filename="corvane.md")
    claim_id = claim_id_for(body, "basing_access")
    decision = decide(client, workspace_id, claim_id, reason="embassy confirmed").json()

    assert req_id in decision["changes"]["requirements_closed"]
    closed = next(r for r in decision["requirements_changed"] if r["req_id"] == req_id)
    assert closed["status"] == "satisfaction"
    assert closed["closure_basis"] == "reviewed_evidence"
    assert closed["product"]["satisfied_by_claim_id"] == claim_id
    assert closed["jipcl_rank"] is None
    assert "satisfied by accepted claim" in closed["product"]["status_history"][-1]["reason"]
    assert closed["answered_by_source"]["source_id"].startswith("psrc_")


def test_a_low_confidence_gap_needs_at_least_moderate_confidence(client, workspace_id):
    req_id = draft(
        client, workspace_id,
        gap_type="low_confidence",
        subject_id="sys_serath_lrs",
        predicate="range_km",
        required_evidence="a rated range measurement for the Serath system",
        gap_reason="the current claim is rated low confidence",
    ).json()["requirement"]["req_id"]

    from reports_fixture import STRAIT_TRAFFIC

    body = ingest(client, workspace_id, STRAIT_TRAFFIC, filename="strait.md")
    weak = next(
        c for c in body["proposed_claims"]
        if c["predicate"] == "range_km" and c["subject_id"] == "sys_serath_lrs"
    )
    decide(
        client, workspace_id, weak["claim_id"], reason="single unrated source",
        revision={"confidence_icd203": "low"},
    )
    assert requirement(client, workspace_id, req_id)["status"] != "satisfaction"

    stronger = ingest(client, workspace_id, SERATH_RANGE, filename="serath.md")
    decide(client, workspace_id, claim_id_for(stronger, "range_km"), reason="rated source")
    row = requirement(client, workspace_id, req_id)
    assert row["status"] == "satisfaction"
    assert "at least moderate" in row["product"]["status_history"][-1]["reason"]


def test_the_requirement_reopens_when_the_satisfying_claim_expires(client, workspace_id):
    req_id = draft(client, workspace_id, assumption_id="asm_blue_1_k2").json()["requirement"]["req_id"]
    body = ingest(client, workspace_id, CORVANE_ACCESS, filename="corvane.md")
    decide(client, workspace_id, claim_id_for(body, "basing_access"))
    assert requirement(client, workspace_id, req_id)["status"] == "satisfaction"

    # A later report moves the evaluation date past the satisfying claim's valid_to.
    later = ingest(client, workspace_id, LANE_58, filename="lane58.md")
    decide(client, workspace_id, claim_id_for(later, "throughput_per_day"))
    row = requirement(client, workspace_id, req_id)
    assert row["status"] == "research"
    assert row["closure_basis"] is None
    assert "expired" in row["product"]["status_history"][-1]["reason"]
    assert row["product"]["satisfied_by_claim_id"] is None


def test_the_requirement_reopens_when_a_later_accepted_claim_contradicts_it(
    client, workspace_id
):
    req_id = draft(
        client, workspace_id,
        gap_type="stale",
        subject_id="inf_kestrel_lane",
        predicate="throughput_per_day",
        required_evidence="a current transit count for the strait",
        gap_reason="the throughput claim has expired",
    ).json()["requirement"]["req_id"]

    first = ingest(client, workspace_id, LANE_61, filename="lane61.md")
    decide(client, workspace_id, claim_id_for(first, "throughput_per_day"))
    assert requirement(client, workspace_id, req_id)["status"] == "satisfaction"

    second = ingest(client, workspace_id, LANE_58, filename="lane58.md")
    decide(client, workspace_id, claim_id_for(second, "throughput_per_day"))
    row = requirement(client, workspace_id, req_id)
    assert row["status"] == "research"  # back to the status it was reopened to
    assert row["closure_basis"] is None
    assert row["jipcl_rank"] is not None  # ranked again on the JIPCL
    assert "contradicts" in row["product"]["status_history"][-1]["reason"]


def test_an_unknown_product_requirement_is_404(client, workspace_id):
    response = client.post(
        "/api/collection/preq_9999/status",
        params={"batch": BATCH, "workspace": workspace_id},
        json={"status": "validation", "actor": "collection manager"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"
