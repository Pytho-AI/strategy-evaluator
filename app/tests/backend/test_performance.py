"""Load budget: the whole point of the replay is that a batch switch feels instant."""
from __future__ import annotations

import time

from app.backend.adapter import DatasetAdapter


def test_cold_load_of_batch_3_is_under_two_seconds():
    adapter = DatasetAdapter()  # empty cache
    started = time.perf_counter()
    snapshot = adapter.snapshot(3)
    elapsed = time.perf_counter() - started
    assert snapshot.tables["strategies"], "batch 3 loaded no strategies"
    assert elapsed < 2.0, f"cold load of batch 3 took {elapsed:.3f}s"


def test_cached_batch_is_faster_than_the_cold_load():
    adapter = DatasetAdapter()
    adapter.snapshot(3)
    started = time.perf_counter()
    adapter.snapshot(3)
    assert time.perf_counter() - started < 0.05
