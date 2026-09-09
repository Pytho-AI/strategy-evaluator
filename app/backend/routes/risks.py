"""The risk view: problem sets, harmful events, drivers and the escalation cascade."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..adapter import DatasetAdapter
from ..contracts import RisksResponse
from ..views import _escalation_edge, harmful_event_views, problem_set_views
from .common import BATCH_QUERY, WORKSPACE_QUERY, envelope, get_adapter, view

router = APIRouter()


@router.get("/api/risks", response_model=RisksResponse)
def risks(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> RisksResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    index = overlay.index
    return RisksResponse(
        **envelope(overlay, started),
        problem_sets=problem_set_views(index),
        harmful_events=harmful_event_views(index),
        escalation_edges=[
            _escalation_edge(index, e) for e in index.rows("escalation_edges")
        ],
    )
