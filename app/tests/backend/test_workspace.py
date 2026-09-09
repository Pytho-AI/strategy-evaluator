"""The workspace itself: persistence, reset, and the promise that an empty one changes nothing."""
from __future__ import annotations

import time

from conftest import MeridianClient
from fastapi.testclient import TestClient
from reports_fixture import dorne_report
from test_review import BATCH, decide, ingest, range_claim_id

from app.backend.adapter import DatasetAdapter
from app.backend.main import create_app
from app.backend.product.overlay import clear_cache

READ_ENDPOINTS = (
    "/api/snapshot", "/api/strategies", "/api/claims", "/api/risks", "/api/collection",
)


def test_state_survives_a_fresh_create_app_on_the_same_workspace(client, workspace_id):
    body = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    claim_id = range_claim_id(body)
    decide(client, workspace_id, claim_id, reason="corroborated")

    restarted = MeridianClient(create_app(DatasetAdapter()))
    clear_cache()  # a new process has no in-memory overlay cache either
    state = restarted.get("/api/workspace", params={"workspace": workspace_id}).json()
    assert state["graph_version"] == 1
    assert state["accepted_claims"] == 1
    assert state["reports"] == 1

    snapshot = restarted.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}
    ).json()
    assert snapshot["overlay_applied"] is True
    assert snapshot["product_claim_ids"] == [claim_id]
    assert snapshot["as_of"] == "2026-11-20"

    report = restarted.get(
        f"/api/reports/{body['report']['report_id']}", params={"workspace": workspace_id}
    ).json()
    assert len(report["text"]) == body["report"]["text_length"]
    assert [c["status"] for c in report["proposed_claims"] if c["claim_id"] == claim_id] == [
        "approved"
    ]


def test_reset_clears_only_the_named_workspace(client, workspace_id):
    other = f"{workspace_id[:58]}_keep"
    for workspace in (workspace_id, other):
        body = ingest(client, workspace, dorne_report(360, "18 November 2026"))
        decide(client, workspace, range_claim_id(body))

    response = client.post(
        "/api/workspace/reset", params={"workspace": workspace_id}, json={"actor": "operator"}
    )
    assert response.status_code == 200
    cleared = response.json()
    assert cleared["graph_version"] == 0
    assert cleared["accepted_claims"] == 0
    assert cleared["reports"] == 0

    kept = client.get("/api/workspace", params={"workspace": other}).json()
    assert kept["accepted_claims"] == 1
    assert client.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": other}
    ).json()["overlay_applied"] is True
    assert "overlay_applied" not in client.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}
    ).json()


def test_an_empty_workspace_leaves_every_read_response_unchanged(client, workspace_id):
    """The overlay keys appear only when the workspace has accepted claims or requirements."""
    before = {
        (path, batch): client.get(path, params={"batch": batch}).json()
        for path in READ_ENDPOINTS
        for batch in (0, 3)
    }
    for (path, batch), body in before.items():
        for key in ("overlay_applied", "workspace", "graph_version", "product_claim_ids",
                    "batch_as_of"):
            assert key not in body, f"{path}?batch={batch} carries {key} with no workspace"

    report = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    decide(client, workspace_id, range_claim_id(report))
    changed = client.get(
        "/api/snapshot", params={"batch": BATCH, "workspace": workspace_id}
    ).json()
    assert changed["overlay_applied"] is True

    client.post("/api/workspace/reset", params={"workspace": workspace_id}, json={"actor": "op"})
    after = {
        (path, batch): client.get(
            path, params={"batch": batch, "workspace": workspace_id}
        ).json()
        for path in READ_ENDPOINTS
        for batch in (0, 3)
    }
    for key, body in before.items():
        served = after[key]
        for field in ("load_ms", "response_ms"):
            body = {k: v for k, v in body.items() if k != field}
            served = {k: v for k, v in served.items() if k != field}
        assert served == body, key


def test_a_draft_requirement_alone_applies_the_overlay_without_moving_the_as_of_date(
    client, workspace_id
):
    response = client.post(
        "/api/collection/drafts",
        params={"batch": BATCH, "workspace": workspace_id},
        json={
            "actor": "collection manager", "gap_type": "missing",
            "required_evidence": "a basing decision", "gap_reason": "no valid claim",
            "proposed_owner": "the theater JIOC", "ltiov": "2026-12-01",
            "strategy_question": "Can str_blue_1 stage from Halden?",
            "assumption_id": "asm_blue_1_k2",
        },
    )
    assert response.status_code == 200
    body = client.get("/api/collection", params={"batch": BATCH, "workspace": workspace_id}).json()
    assert body["overlay_applied"] is True
    assert body["graph_version"] == 0  # no accepted claim yet
    assert body["product_claim_ids"] == []
    assert body["as_of"] == body["batch_as_of"] == "2026-11-17"


def test_the_whole_product_flow_stays_inside_the_two_second_budget(client, workspace_id):
    started = time.perf_counter()
    body = ingest(client, workspace_id, dorne_report(360, "18 November 2026"))
    ingest_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    decide(client, workspace_id, range_claim_id(body))
    decision_ms = (time.perf_counter() - started) * 1000

    timings = {"POST /api/reports": ingest_ms, "POST .../decision": decision_ms}
    for path in READ_ENDPOINTS + ("/api/planning",):
        started = time.perf_counter()
        response = client.get(path, params={"batch": BATCH, "workspace": workspace_id})
        assert response.status_code == 200
        timings[f"GET {path}"] = (time.perf_counter() - started) * 1000
    print("\n" + "\n".join(f"{name}: {ms:.0f} ms" for name, ms in timings.items()))
    for name, ms in timings.items():
        assert ms < 2000, f"{name} took {ms:.0f} ms"
