"""Adapter behaviour that is not visible through the HTTP layer."""
from __future__ import annotations

from app.backend.adapter import DatasetAdapter


def test_cache_key_is_dataset_identity_plus_batch(adapter: DatasetAdapter):
    for batch in (0, 1, 2, 3):
        adapter.snapshot(batch)
    keys = set(adapter._cache)
    assert keys == {(adapter.identity.key, batch) for batch in (0, 1, 2, 3)}
    assert adapter.identity.archive_sha256 in adapter.identity.key
    assert len({identity for identity, _ in keys}) == 1


def test_cached_snapshots_are_returned_unchanged(adapter: DatasetAdapter):
    first = adapter.snapshot(3)
    second = adapter.snapshot(3)
    assert first is second


def test_mutating_a_returned_table_cannot_reach_the_cache(adapter: DatasetAdapter):
    """R4: callers own what they are handed; the cache keeps its own copy."""
    handed_out = adapter.snapshot(1).table("strategies")
    fresh = DatasetAdapter().snapshot(1).table("strategies")
    assert handed_out == fresh

    handed_out[0]["value"] = 42.0
    handed_out[0]["validity"]["acceptable"]["pass"] = True
    handed_out.append({"strategy_id": "str_injected"})

    assert adapter.snapshot(1).table("strategies") == fresh
    assert adapter.snapshot(1).table("strategies") is not handed_out


def test_mutating_the_tables_mapping_cannot_reach_the_cache(adapter: DatasetAdapter):
    tables = adapter.snapshot(2).tables
    counts = adapter.snapshot(2).table_counts
    tables.pop("strategies")
    tables["assumptions"][0]["p_holds"] = 0.0
    assert adapter.snapshot(2).table_counts == counts
    assert adapter.snapshot(2).table("assumptions") == DatasetAdapter().snapshot(2).table(
        "assumptions"
    )


def test_a_different_dataset_identity_gets_its_own_cache_entry(adapter: DatasetAdapter):
    other = DatasetAdapter()
    other._identity = adapter.identity.__class__(
        archive_sha256="0" * 64, git_head=None, key="0" * 64 + ":no-git"
    )
    other.snapshot(0)
    assert set(other._cache) == {("0" * 64 + ":no-git", 0)}
    assert set(other._cache) != set(adapter._cache)


def test_blue_ranking_comes_from_the_reference_engine(adapter: DatasetAdapter):
    snapshot = adapter.snapshot(0)
    valid = [
        s["strategy_id"]
        for s in snapshot.table("strategies")
        if s["actor_id"] == "ent_blue" and s["status"] == "valid"
    ]
    assert sorted(adapter.blue_ranking(snapshot)) == sorted(valid)
