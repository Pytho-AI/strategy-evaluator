"""The collection view and the product's own draft / route / status workflow.

Dataset requirements (``req_01``..) are read-only replay rows; product ones (``preq_0001``..)
carry ``owner: "product"`` and close only on reviewed evidence.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..adapter import DatasetAdapter
from ..contracts import (
    CollectionDraftRequest,
    CollectionDraftResponse,
    CollectionResponse,
    DecisionView,
    RequirementStatusRequest,
    RequirementUpdateResponse,
    RouteRequest,
)
from ..product import collection as workflow
from ..product.store import Workspace
from ..views import requirement_by_id, requirement_views
from .common import BATCH_QUERY, WORKSPACE_QUERY, elapsed_ms, envelope, get_adapter, view

router = APIRouter()


@router.get("/api/collection", response_model=CollectionResponse)
def collection(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> CollectionResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    return CollectionResponse(
        **envelope(overlay, started), requirements=requirement_views(overlay.index)
    )


def _requirement_response(adapter, batch, workspace, req_id, started):
    overlay = view(adapter, batch, workspace)
    return RequirementUpdateResponse(
        workspace=workspace,
        batch=batch,
        requirement=requirement_by_id(overlay.index, req_id),
        response_ms=elapsed_ms(started),
    )


@router.post("/api/collection/drafts", response_model=CollectionDraftResponse)
def create_draft(
    body: CollectionDraftRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> CollectionDraftResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    store = Workspace(workspace)
    record, duplicate = workflow.create_draft(
        store, overlay.index, strategy_question=body.strategy_question, pir_id=body.pir_id,
        assumption_id=body.assumption_id, subject_id=body.subject_id,
        predicate=body.predicate, gap_type=body.gap_type,
        required_evidence=body.required_evidence, gap_reason=body.gap_reason,
        proposed_owner=body.proposed_owner, ltiov=body.ltiov, sir=body.sir,
        indicators=body.indicators, actor=body.actor,
    )
    after = view(adapter, batch, workspace)
    return CollectionDraftResponse(
        workspace=workspace,
        batch=batch,
        requirement=requirement_by_id(after.index, record["req_id"]),
        duplicate_of=record["req_id"] if duplicate else None,
        decision=DecisionView(**duplicate) if duplicate else None,
        response_ms=elapsed_ms(started),
    )


@router.post("/api/collection/{req_id}/route", response_model=RequirementUpdateResponse)
def route_requirement(
    req_id: str,
    body: RouteRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> RequirementUpdateResponse:
    """Assign the requirement to an internal queue. Nothing is sent to an external recipient."""
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    workflow.route(
        Workspace(workspace), overlay.index, req_id, queue=body.queue, actor=body.actor,
        reason=body.reason,
    )
    return _requirement_response(adapter, batch, workspace, req_id, started)


@router.post("/api/collection/{req_id}/status", response_model=RequirementUpdateResponse)
def set_requirement_status(
    req_id: str,
    body: RequirementStatusRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> RequirementUpdateResponse:
    started = time.perf_counter()
    adapter.check()
    workflow.set_status(
        Workspace(workspace), req_id, status=body.status, actor=body.actor, reason=body.reason
    )
    return _requirement_response(adapter, batch, workspace, req_id, started)
