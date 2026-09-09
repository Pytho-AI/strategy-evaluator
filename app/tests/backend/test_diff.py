"""GET /api/injects/{batch}/diff against the manifests.

The manifest is the oracle and is read only here. The endpoint computes the diff from the
two loaded snapshots; if the two ever disagree, one of them is wrong.
"""
from __future__ import annotations

import pytest

# The manifest's own field names, per expected_effects list.
KEYS = {
    "assumptions_changed": ("assumption_id", "from", "to"),
    "validity_changed": ("strategy_id", "test", "before", "after"),
    "strategies_restated": (
        "strategy_id", "value_before", "value_after", "status_before", "status_after",
    ),
    "risk_assessments_changed": (
        "he_id", "horizon", "level_before", "level_after", "trend_after",
        "p_before", "p_after",
    ),
    "problem_sets_moved": (
        "problem_set_id", "jsps_horizon", "level_before", "level_after",
    ),
    "jipcl_changed": (
        "req_id", "rank_before", "rank_after", "status_before", "status_after",
    ),
}
VALUE_FIELDS = {"value_before", "value_after", "p_before", "p_after"}


def diff(client, batch: int) -> dict:
    response = client.get(f"/api/injects/{batch}/diff")
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("batch", (1, 2, 3))
@pytest.mark.parametrize("field", sorted(KEYS))
def test_diff_rows_match_the_manifest_field_by_field(client, manifests, batch, field):
    expected = manifests[batch]["expected_effects"][field]
    actual = diff(client, batch)[field]
    assert len(actual) == len(expected), f"{field}: row count differs"
    for got, want in zip(actual, expected):
        for key in KEYS[field]:
            if key in VALUE_FIELDS:
                assert got[key] == pytest.approx(want[key], abs=1e-9), f"{field}.{key}"
            else:
                assert got[key] == want[key], f"{field}.{key}"


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_diff_rankings_and_closures_match_the_manifest(client, manifests, batch):
    effects = manifests[batch]["expected_effects"]
    body = diff(client, batch)
    assert body["ranking_before"] == effects["ranking_before"]
    assert body["ranking_after"] == effects["ranking_after"]
    assert body["requirements_closed"] == effects["requirements_closed"]
    assert body["as_of_after"] == manifests[batch]["as_of"]


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_diff_reports_the_new_evidence_of_the_batch(client, manifests, batch):
    body = diff(client, batch)
    added = {c["claim_id"] for c in body["evidence"]["claims_added"]}
    docs = set(manifests[batch]["docs"])
    assert added, "a batch always brings new claims"
    assert {c["source_id"] for c in body["evidence"]["claims_added"]} <= docs
    superseded = {c["claim_id"] for c in body["evidence"]["claims_superseded"]}
    assert superseded and not superseded & added


def test_batch_3_diff_flags_the_contradicted_throughput_claim(client):
    contradicted = diff(client, 3)["evidence"]["claims_contradicted"]
    assert [c["claim_id"] for c in contradicted] == ["clm_0862"]
    assert contradicted[0]["status"] == "proposed"
    assert contradicted[0]["reliability"] == "D"


def test_batch_3_cascade_path_carries_the_energy_problem_set(client):
    changed = {
        (r["he_id"], r["horizon"]): r for r in diff(client, 3)["risk_assessments_changed"]
    }
    # he_05 (logistics network) escalates into he_04 (blackout halts sustainment).
    assert ["he_05", "he_04"] in changed[("he_04", "near")]["cascade_paths"]
    assert changed[("he_05", "near")]["level_after"] == "significant"


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_only_meridian_strategies_move_between_batches(client, adapter, batch):
    """The diff is scoped to the Meridian game; nothing else may change unseen."""
    def others(index):
        return {
            s["strategy_id"]: (s["value"], s["status"])
            for s in index.rows("strategies")
            if s["game_id"] != "meridian"
        }

    assert others(adapter.index(batch - 1)) == others(adapter.index(batch))


@pytest.mark.parametrize("batch", ("0", "4", "x"))
def test_diff_rejects_a_batch_without_a_predecessor(client, batch):
    response = client.get(f"/api/injects/{batch}/diff")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
