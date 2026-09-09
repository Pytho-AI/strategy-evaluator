"""The inject manifests are the oracle. No expected outcome is typed into product code."""
from __future__ import annotations

import pytest

BLUE = ("meridian", "ent_blue")


def snapshot(client, batch: int) -> dict:
    return client.get("/api/snapshot", params={"batch": batch}).json()


def blue_ranking(body: dict) -> list[str]:
    return next(
        r["strategy_ids"]
        for r in body["rankings"]
        if (r["game_id"], r["actor_id"]) == BLUE
    )


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_strategy_values_and_statuses_match_the_manifest(client, manifests, batch):
    before = {s["strategy_id"]: s for s in snapshot(client, batch - 1)["strategies"]}
    after = {s["strategy_id"]: s for s in snapshot(client, batch)["strategies"]}
    for row in manifests[batch]["expected_effects"]["strategies_restated"]:
        sid = row["strategy_id"]
        assert before[sid]["value"] == pytest.approx(row["value_before"], abs=1e-9)
        assert after[sid]["value"] == pytest.approx(row["value_after"], abs=1e-9)
        assert before[sid]["status"] == row["status_before"]
        assert after[sid]["status"] == row["status_after"]


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_ranking_matches_the_manifest(client, manifests, batch):
    effects = manifests[batch]["expected_effects"]
    assert blue_ranking(snapshot(client, batch - 1)) == effects["ranking_before"]
    assert blue_ranking(snapshot(client, batch)) == effects["ranking_after"]


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_validity_changes_match_the_manifest(client, manifests, batch):
    def tests(body: dict) -> dict:
        return {
            s["strategy_id"]: {t["test"]: t["passed"] for t in s["validity"]}
            for s in body["strategies"]
        }

    before, after = tests(snapshot(client, batch - 1)), tests(snapshot(client, batch))
    for row in manifests[batch]["expected_effects"]["validity_changed"]:
        sid, name = row["strategy_id"], row["test"]
        assert before[sid][name] is row["before"]
        assert after[sid][name] is row["after"]


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_assumption_status_changes_match_the_manifest(client, manifests, batch):
    def statuses(body: dict) -> dict:
        return {a["assumption_id"]: a["status"] for a in body["assumptions"]}

    before, after = statuses(snapshot(client, batch - 1)), statuses(snapshot(client, batch))
    changed = manifests[batch]["expected_effects"]["assumptions_changed"]
    for row in changed:
        assert before[row["assumption_id"]] == row["from"]
        assert after[row["assumption_id"]] == row["to"]
    listed = {row["assumption_id"] for row in changed}
    unlisted = [a for a in before if a not in listed and before[a] != after[a]]
    assert unlisted == []


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_problem_set_moves_match_the_manifest(client, manifests, batch):
    def levels(body: dict) -> dict:
        return {
            (p["problem_set_id"], p["jsps_horizon"]): p["max_risk_level"]
            for p in body["problem_set_assessments"]
        }

    before, after = levels(snapshot(client, batch - 1)), levels(snapshot(client, batch))
    moved = manifests[batch]["expected_effects"]["problem_sets_moved"]
    for row in moved:
        key = (row["problem_set_id"], row["jsps_horizon"])
        assert before[key] == row["level_before"]
        assert after[key] == row["level_after"]
    listed = {(row["problem_set_id"], row["jsps_horizon"]) for row in moved}
    assert [k for k in before if k not in listed and before[k] != after[k]] == []


@pytest.mark.parametrize("batch", (1, 2, 3))
def test_collection_status_and_jipcl_rank_match_the_manifest(client, manifests, batch):
    def reqs(body: dict) -> dict:
        return {r["req_id"]: r for r in body["collection_requirements"]}

    before, after = reqs(snapshot(client, batch - 1)), reqs(snapshot(client, batch))
    effects = manifests[batch]["expected_effects"]
    for row in effects["jipcl_changed"]:
        rid = row["req_id"]
        assert (before[rid]["jipcl_rank"] if rid in before else None) == row["rank_before"]
        assert (after[rid]["jipcl_rank"] if rid in after else None) == row["rank_after"]
        if rid in before:
            assert before[rid]["status"] == row["status_before"]
        assert after[rid]["status"] == row["status_after"]
    for rid in effects["requirements_closed"]:
        assert after[rid]["status"] == "satisfaction"


def test_batch_1_invalidates_str_blue_1_on_the_acceptable_test(client, manifests):
    body = snapshot(client, 1)
    strategy = next(s for s in body["strategies"] if s["strategy_id"] == "str_blue_1")
    assert strategy["status"] == "invalid"
    failed = [t["test"] for t in strategy["validity"] if not t["passed"]]
    assert failed == ["acceptable"]
    assert blue_ranking(body) == manifests[1]["expected_effects"]["ranking_after"]
    assert "str_blue_1" not in blue_ranking(body)


def test_batch_2_satisfies_req_01_and_revalidates_str_blue_1(client, manifests):
    body = snapshot(client, 2)
    req_01 = next(r for r in body["collection_requirements"] if r["req_id"] == "req_01")
    assert "req_01" in manifests[2]["expected_effects"]["requirements_closed"]
    assert req_01["status"] == "satisfaction"
    assert req_01["jipcl_rank"] is None
    strategy = next(s for s in body["strategies"] if s["strategy_id"] == "str_blue_1")
    assert strategy["status"] == "valid"
    assert all(t["passed"] for t in strategy["validity"])


def test_batch_3_violates_the_k4_assumption(client, manifests):
    changed = manifests[3]["expected_effects"]["assumptions_changed"]
    violated = [row["assumption_id"] for row in changed if row["to"] == "violated"]
    assert violated, "batch 3 manifest no longer records a violated assumption"
    body = snapshot(client, 3)
    statuses = {a["assumption_id"]: a for a in body["assumptions"]}
    for assumption_id in violated:
        assert statuses[assumption_id]["status"] == "violated"
        assert statuses[assumption_id]["index_k"] == 4
