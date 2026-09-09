"""The inject timeline: the three manifests, and what one batch changed."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Path

from ..adapter import BATCHES, DatasetAdapter
from ..branding import MARKING
from ..contracts import DiffResponse, InjectManifestView, InjectsResponse
from ..views import diff
from .common import elapsed_ms, get_adapter

router = APIRouter()


@router.get("/api/injects", response_model=InjectsResponse)
def injects(adapter: DatasetAdapter = Depends(get_adapter)) -> InjectsResponse:
    adapter.check()
    return InjectsResponse(
        injects=[
            InjectManifestView(
                batch=m["batch"],
                as_of=m["as_of"],
                docs=m["docs"],
                change_events=m["change_events"],
                expected_effects=m["expected_effects"],
            )
            for m in adapter.manifests()
        ]
    )


@router.get("/api/injects/{batch}/diff", response_model=DiffResponse)
def inject_diff(
    batch: int = Path(
        ..., ge=min(BATCHES) + 1, le=max(BATCHES), description="inject batch 1, 2 or 3"
    ),
    adapter: DatasetAdapter = Depends(get_adapter),
) -> DiffResponse:
    """Computed from the two loaded snapshots. The manifest is the test oracle, not an input."""
    started = time.perf_counter()
    before, after = adapter.index(batch - 1), adapter.index(batch)
    return DiffResponse(
        batch=batch,
        marking=MARKING,
        as_of_before=before.snapshot.as_of,
        as_of_after=after.snapshot.as_of,
        response_ms=elapsed_ms(started),
        **diff(before, after),
    )
