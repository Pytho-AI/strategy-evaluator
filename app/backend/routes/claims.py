"""The evidence view: claims with full provenance, filters, and one claim's trace."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query

from ..adapter import DatasetAdapter
from ..contracts import ClaimDetailResponse, ClaimsResponse
from ..errors import UnknownId
from ..views import claim_trace, claim_view, filter_claims
from .common import BATCH_QUERY, WORKSPACE_QUERY, envelope, get_adapter, view

router = APIRouter()


@router.get("/api/claims", response_model=ClaimsResponse)
def claims(
    batch: int = BATCH_QUERY,
    entity: str | None = Query(None, description="subject or object entity id"),
    source: str | None = Query(None, description="source id"),
    status: str | None = Query(None, description="proposed, approved, rejected, superseded"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
    relationship: str | None = Query(None, description="dependency kind the claim takes part in"),
    assumption: str | None = Query(None, description="assumption id the claim grounds"),
    harmful_event: str | None = Query(None, description="harmful event id the claim drives"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ClaimsResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    index = overlay.index
    rows = filter_claims(
        index,
        entity=entity,
        source=source,
        status=status,
        min_confidence=min_confidence,
        relationship=relationship,
        assumption=assumption,
        harmful_event=harmful_event,
    )
    return ClaimsResponse(
        **envelope(overlay, started),
        total=len(rows),
        limit=limit,
        offset=offset,
        claims=[claim_view(index, c) for c in rows[offset : offset + limit]],
    )


@router.get("/api/claims/{claim_id}", response_model=ClaimDetailResponse)
def claim(
    claim_id: str,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ClaimDetailResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    index = overlay.index
    row = index.claims.get(claim_id)
    if row is None:
        raise UnknownId(
            f"no claim {claim_id!r} in batch {batch}.",
            {"claim_id": claim_id, "batch": batch},
        )
    return ClaimDetailResponse(
        **envelope(overlay, started),
        claim=claim_view(index, row),
        trace=claim_trace(index, row),
    )
