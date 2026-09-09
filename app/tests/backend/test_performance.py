"""Load budget: the whole point of the replay is that a batch switch feels instant."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.backend.adapter import DatasetAdapter
from app.backend.main import create_app

# The five views the workbench holds open at once.
WARM_SET = (
    "/api/snapshot?batch=3",
    "/api/strategies?batch=3",
    "/api/claims?batch=3",
    "/api/risks?batch=3",
    "/api/collection?batch=3",
)

COLD_URLS = WARM_SET + (
    "/api/health",
    "/api/meta",
    "/api/injects",
    "/api/injects/3/diff",
    "/api/strategies/str_blue_1?batch=3",
    "/api/claims/clm_0862?batch=3",
)


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


@pytest.mark.parametrize("url", COLD_URLS)
def test_each_endpoint_answers_in_under_two_seconds_from_cold(url):
    client = TestClient(create_app(DatasetAdapter()))  # empty cache per endpoint
    started = time.perf_counter()
    response = client.get(url)
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < 2.0, f"cold {url} took {elapsed:.3f}s"


def test_the_whole_warm_view_set_answers_in_under_one_second(client):
    for url in WARM_SET:
        assert client.get(url).status_code == 200  # prime the cache
    started = time.perf_counter()
    for url in WARM_SET:
        assert client.get(url).status_code == 200
    elapsed = time.perf_counter() - started
    assert elapsed < 1.0, f"warm snapshot+strategies+claims+risks+collection took {elapsed:.3f}s"
