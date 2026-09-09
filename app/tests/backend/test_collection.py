"""GET /api/collection: the JIPCL, its priority basis and what each requirement affects."""
from __future__ import annotations

import pytest

BATCHES = (0, 1, 2, 3)


def requirements(client, batch: int) -> list[dict]:
    response = client.get("/api/collection", params={"batch": batch})
    assert response.status_code == 200
    return response.json()["requirements"]


def by_id(client, batch: int) -> dict[str, dict]:
    return {r["req_id"]: r for r in requirements(client, batch)}


@pytest.mark.parametrize("batch", BATCHES)
def test_requirements_are_served_in_jipcl_rank_order(client, batch):
    rows = requirements(client, batch)
    ranked = [r["jipcl_rank"] for r in rows if r["jipcl_rank"] is not None]
    assert ranked == sorted(ranked) == list(range(1, len(ranked) + 1))
    unranked = [r for r in rows if r["jipcl_rank"] is None]
    assert all(r["jipcl_rank"] is None for r in rows[len(ranked) :])
    for requirement in unranked:
        assert requirement["status"] in ("satisfaction", "closed")


@pytest.mark.parametrize("batch", BATCHES)
def test_priority_ranks_descend_with_the_computed_priority(client, batch):
    ranked = [r for r in requirements(client, batch) if r["jipcl_rank"] is not None]
    priorities = [r["priority"] for r in ranked]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.parametrize("batch", BATCHES)
def test_every_requirement_states_its_pir_context_and_priority_basis(client, batch):
    for requirement in requirements(client, batch):
        assert requirement["pir_statement"] and requirement["commander_role"]
        assert requirement["eei"] and requirement["sir"] and requirement["indicators"]
        assert requirement["ltiov"] and requirement["routing"]
        assert requirement["gap_type"] in {
            "missing", "stale", "low_confidence", "contradiction",
        }
        basis = requirement["priority_basis"]
        if requirement["priority"] is None:
            assert basis is None
            continue
        if basis["basis"] == "evpi":
            assert basis["assumption_id"] and basis["evpi"] == requirement["priority"]
            assert requirement["assumption"]["evpi"] == basis["evpi"]
        else:
            assert basis["basis"] == "fallback"
            assert basis["confidence"] is not None and basis["degree"] is not None


def test_req_01_closes_at_batch_2_with_a_manifest_replay_basis(client, manifests):
    assert manifests[2]["expected_effects"]["requirements_closed"] == ["req_01"]
    before = by_id(client, 1)["req_01"]
    assert before["status"] == "research" and before["closure_basis"] is None
    after = by_id(client, 2)["req_01"]
    assert after["status"] == "satisfaction"
    assert after["jipcl_rank"] is None
    assert after["closure_basis"] == "manifest_replay"
    assert after["answered_by_source"]["source_id"]
    assert after["answered_by_source"]["reliability"] == "B"


def test_req_07_opens_at_batch_3_as_the_top_contradiction_gap(client, manifests):
    jipcl = {row["req_id"]: row for row in manifests[3]["expected_effects"]["jipcl_changed"]}
    assert jipcl["req_07"]["rank_after"] == 1
    assert "req_07" not in by_id(client, 2)
    requirement = by_id(client, 3)["req_07"]
    assert requirement["jipcl_rank"] == 1
    assert requirement["gap_type"] == "contradiction"
    assert requirement["status"] == "validation"
    assert requirement["closure_basis"] is None
    assert requirement["subject_id"] == "inf_kestrel_lane"
    assert requirement["priority_basis"]["basis"] == "fallback"


def test_a_requirement_names_the_options_its_assumption_can_move(client):
    requirement = by_id(client, 0)["req_01"]
    assert requirement["assumption"]["assumption_id"] == "asm_blue_1_k2"
    # k2 is shared: rows with the same index_k share the grounding claim (SCHEMA.md §1).
    assert [s["strategy_id"] for s in requirement["affected_strategies"]] == [
        "str_blue_1",
        "str_blue_3",
    ]
    assert all(s["name"] and s["status"] for s in requirement["affected_strategies"])


def test_extension_layers_attach_assets_disciplines_and_the_routing_authority(client):
    requirement = by_id(client, 0)["req_01"]
    assert requirement["candidate_assets"], "collection_assets extension not attached"
    assert requirement["disciplines"] == sorted(set(requirement["disciplines"]))
    for asset in requirement["candidate_assets"]:
        assert asset["name"] and asset["owner_org"]
        assert 0.0 <= asset["p_success"] <= 1.0
    authority = requirement["routing_authority"]
    assert authority["recommendation_type"] == "requirement_submit"
    assert authority["tier_id"] and authority["approver_role"]


def test_the_open_requirement_set_shrinks_when_one_is_answered(client):
    open_at = {
        batch: [r["req_id"] for r in requirements(client, batch) if r["jipcl_rank"]]
        for batch in (1, 2)
    }
    assert "req_01" in open_at[1] and "req_01" not in open_at[2]
