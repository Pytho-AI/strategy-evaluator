"""The dataset is a frozen contract. Nothing the app does may write to it."""
from __future__ import annotations

from pathlib import Path

from conftest import DATASET_DIR, hash_tree

from app.backend.adapter import DatasetAdapter


def test_serving_every_batch_leaves_dataset_byte_identical(client, dataset_hashes_before):
    for batch in (0, 1, 2, 3):
        assert client.get("/api/snapshot", params={"batch": batch}).status_code == 200
    client.get("/api/meta")
    client.get("/api/injects")
    client.get("/api/health")
    assert hash_tree(DATASET_DIR) == dataset_hashes_before


def test_snapshot_tables_are_copies_not_the_files(tmp_path: Path):
    """Mutating what the adapter hands out cannot reach dataset/."""
    adapter = DatasetAdapter()
    before = hash_tree(DATASET_DIR)
    snapshot = adapter.snapshot(1)
    snapshot.table("strategies")[0]["value"] = 42.0
    assert hash_tree(DATASET_DIR) == before
