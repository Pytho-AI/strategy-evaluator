"""What every router needs: the adapter dependency, batch/workspace parameters, the envelope."""
from __future__ import annotations

import time

from fastapi import Query, Request

from ..adapter import BATCHES, DatasetAdapter
from ..branding import MARKING
from ..product.overlay import Overlay, evaluate
from ..product.store import DEFAULT_WORKSPACE

BATCH_QUERY = Query(
    0,
    ge=min(BATCHES),
    le=max(BATCHES),
    description="inject batch: 0 (T0), 1, 2, or 3",
)

WORKSPACE_QUERY = Query(
    DEFAULT_WORKSPACE,
    min_length=1,
    max_length=64,
    pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    description=(
        "product workspace whose accepted claims overlay this batch. An empty workspace "
        "changes nothing: the response is the replay response."
    ),
)


def get_adapter(request: Request) -> DatasetAdapter:
    return request.app.state.adapter


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def view(adapter: DatasetAdapter, batch: int, workspace: str) -> Overlay:
    """The batch as this workspace sees it (``product/overlay.py`` documents the as-of rule)."""
    adapter.check()
    return evaluate(adapter, batch, workspace)


def envelope(overlay: Overlay, started: float) -> dict:
    index = overlay.index
    return {
        "batch": index.batch,
        "as_of": index.snapshot.as_of,
        "marking": MARKING,
        "load_ms": index.snapshot.load_ms,
        "response_ms": elapsed_ms(started),
        **overlay.envelope(),
    }
