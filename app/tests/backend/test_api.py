"""P0 endpoint contracts."""
from __future__ import annotations

import json

import pytest

from app.backend.branding import MARKING, PRODUCT_NAME

BATCHES = (0, 1, 2, 3)


def test_health_reports_dataset_identity_and_load_time(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert len(body["dataset"]["archive_sha256"]) == 64
    assert body["dataset"]["key"].startswith(body["dataset"]["archive_sha256"])
    assert body["load_ms"] > 0


def test_meta_reports_branding_marking_batches_and_worlds(client):
    response = client.get("/api/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["product_name"] == PRODUCT_NAME
    assert body["marking"] == MARKING
    assert body["dataset_name"] == "strategy-evaluation-dataset-pytho"
    assert [b["batch"] for b in body["batches"]] == list(BATCHES)
    for batch in body["batches"]:
        assert batch["as_of"]
        assert batch["table_counts"]["strategies"] > 0
    # Reported honestly: 64 Blue worlds; 66 is the distinct-label figure on the data card.
    assert body["worlds"]["blue_worlds"] == 64
    assert body["worlds"]["distinct_world_labels"] == 66
    assert "66" in body["worlds"]["note"]


def test_meta_as_of_dates_come_from_the_manifests(client, manifests):
    body = client.get("/api/meta").json()
    as_of = {b["batch"]: b["as_of"] for b in body["batches"]}
    for batch, manifest in manifests.items():
        assert as_of[batch] == manifest["as_of"]


def test_injects_returns_the_three_manifests(client, manifests):
    body = client.get("/api/injects").json()
    assert [i["batch"] for i in body["injects"]] == [1, 2, 3]
    for inject in body["injects"]:
        manifest = manifests[inject["batch"]]
        assert inject["as_of"] == manifest["as_of"]
        assert inject["docs"] == manifest["docs"]
        assert inject["change_events"] == manifest["change_events"]
        assert inject["expected_effects"] == manifest["expected_effects"]


@pytest.mark.parametrize("batch", BATCHES)
def test_snapshot_loads_every_batch_with_nonempty_tables(client, batch):
    response = client.get("/api/snapshot", params={"batch": batch})
    assert response.status_code == 200
    body = response.json()
    assert body["batch"] == batch
    assert body["marking"] == MARKING
    assert body["as_of"]
    for table in (
        "strategies",
        "rankings",
        "assumptions",
        "problem_set_assessments",
        "collection_requirements",
    ):
        assert body[table], f"{table} empty at batch {batch}"


@pytest.mark.parametrize("batch", BATCHES)
def test_snapshot_strategy_fields(client, batch):
    body = client.get("/api/snapshot", params={"batch": batch}).json()
    for strategy in body["strategies"]:
        assert strategy["status"] in {"valid", "invalid", "infeasible"}
        assert isinstance(strategy["value"], float)
        low, high = strategy["adversary_range"]
        assert low <= high
        assert [t["test"] for t in strategy["validity"]] == [
            "suitable",
            "feasible",
            "acceptable",
            "distinguishable",
            "complete",
        ]


@pytest.mark.parametrize("batch", BATCHES)
def test_rankings_list_only_valid_strategies(client, batch):
    body = client.get("/api/snapshot", params={"batch": batch}).json()
    status = {s["strategy_id"]: s["status"] for s in body["strategies"]}
    value = {s["strategy_id"]: s["value"] for s in body["strategies"]}
    for ranking in body["rankings"]:
        assert all(status[sid] == "valid" for sid in ranking["strategy_ids"])
        values = [value[sid] for sid in ranking["strategy_ids"]]
        assert values == sorted(values, reverse=True)


@pytest.mark.parametrize("batch", ["4", "-1", "x", "", "1.5"])
def test_invalid_batch_is_rejected_with_422(client, batch):
    response = client.get("/api/snapshot", params={"batch": batch})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "invalid_request"
    assert "batch must be an integer 0, 1, 2 or 3." == body["error"]["message"]


def test_snapshot_reports_response_ms_beside_load_ms(client):
    body = client.get("/api/snapshot", params={"batch": 0}).json()
    assert body["load_ms"] > 0
    assert body["response_ms"] >= 0


def test_strategy_lookup_matches_the_manifest_at_batch_1(client, manifests):
    """Oracle: the batch-1 manifest, read here in the test, never by the app."""
    restated = {
        row["strategy_id"]: row
        for row in manifests[1]["expected_effects"]["strategies_restated"]
    }
    expected = restated["str_blue_1"]
    failed_tests = sorted(
        row["test"]
        for row in manifests[1]["expected_effects"]["validity_changed"]
        if row["strategy_id"] == "str_blue_1" and row["after"] is False
    )
    assert expected["status_after"] == "invalid"
    assert failed_tests == ["acceptable"]

    response = client.get("/api/strategies/str_blue_1", params={"batch": 1})
    assert response.status_code == 200
    body = response.json()
    strategy = body["strategy"]
    assert strategy["strategy_id"] == "str_blue_1"
    assert strategy["status"] == expected["status_after"]
    assert strategy["value"] == pytest.approx(expected["value_after"], abs=1e-9)
    assert [t["test"] for t in strategy["validity"] if not t["passed"]] == failed_tests


def test_strategy_lookup_carries_assumptions_and_objective_weights(client):
    body = client.get("/api/strategies/str_blue_1", params={"batch": 1}).json()
    assert body["batch"] == 1
    assert body["marking"] == MARKING
    assert body["assumptions"]
    assert {a["strategy_id"] for a in body["assumptions"]} == {"str_blue_1"}
    assert body["objectives"]
    assert all(0.0 <= o["weight"] <= 1.0 for o in body["objectives"])
    snapshot_strategy = next(
        s
        for s in client.get("/api/snapshot", params={"batch": 1}).json()["strategies"]
        if s["strategy_id"] == "str_blue_1"
    )
    assert body["strategy"] == snapshot_strategy


def test_strategy_lookup_default_batch_is_0(client):
    default = client.get("/api/strategies/str_blue_1").json()
    assert default["batch"] == 0
    assert default["strategy"]["status"] == "valid"


def test_unknown_strategy_id_returns_404_unknown_id(client):
    response = client.get("/api/strategies/str_does_not_exist", params={"batch": 1})
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "unknown_id"
    assert "str_does_not_exist" in error["message"]


def test_claim_lookup_returns_the_claim_row_and_its_source(client):
    snapshot_claim_id = "clm_0001"
    response = client.get(f"/api/claims/{snapshot_claim_id}")
    assert response.status_code == 200
    body = response.json()
    claim = body["claim"]
    assert claim["claim_id"] == snapshot_claim_id
    assert claim["source_id"] == body["source"]["source_id"]
    assert body["source"]["title"]
    assert body["source"]["path"].endswith(".md")


def test_unknown_claim_id_returns_404_unknown_id(client):
    response = client.get("/api/claims/clm_does_not_exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "unknown_id"
    assert "clm_does_not_exist" in error["message"]


@pytest.mark.parametrize("batch", ["4", "-1", "x", "", "1.5"])
def test_lookup_rejects_an_invalid_batch_with_422(client, batch):
    for url in ("/api/strategies/str_blue_1", "/api/claims/clm_0001"):
        response = client.get(url, params={"batch": batch})
        assert response.status_code == 422, url
        assert response.json()["error"]["code"] == "invalid_request"


def test_batch_1_response_survives_a_mutation_attempt(client):
    """R4: a caller that mutates what it was handed cannot change later responses."""
    def canonical() -> str:
        body = client.get("/api/snapshot", params={"batch": 1}).json()
        body.pop("response_ms")  # per-request timer; everything else must be identical
        return json.dumps(body, sort_keys=True)

    before = canonical()
    served = client.get("/api/snapshot", params={"batch": 1}).json()
    served["strategies"][0]["value"] = 42.0
    served["strategies"].append({"strategy_id": "str_injected"})
    served["assumptions"][0]["status"] = "violated"
    assert canonical() == before
