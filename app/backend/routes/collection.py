"""The collection view and the product's own draft / route / status workflow.

Dataset requirements (``req_01``..) are read-only replay rows; product ones (``preq_0001``..)
carry ``owner: "product"`` and close only on reviewed evidence.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

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
from ..scenarios import ScenarioRegistry
from ..views import requirement_by_id, requirement_views
from .common import (
    BATCH_QUERY,
    SCENARIO_QUERY,
    WORKSPACE_QUERY,
    elapsed_ms,
    envelope,
    get_registry,
    scenario_adapter,
    view,
)

router = APIRouter()


@router.get("/api/collection", response_model=CollectionResponse)
def collection(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> CollectionResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    return CollectionResponse(
        **envelope(overlay, started), requirements=requirement_views(overlay.index)
    )


def _requirement_response(registry, batch, workspace, scenario, req_id, started):
    overlay = view(registry, batch, workspace, scenario)
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
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> CollectionDraftResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    store = Workspace(workspace)
    record, duplicate = workflow.create_draft(
        store, overlay.index, strategy_question=body.strategy_question, pir_id=body.pir_id,
        assumption_id=body.assumption_id, subject_id=body.subject_id,
        predicate=body.predicate, gap_type=body.gap_type,
        required_evidence=body.required_evidence, gap_reason=body.gap_reason,
        proposed_owner=body.proposed_owner, ltiov=body.ltiov, sir=body.sir,
        indicators=body.indicators, actor=body.actor,
    )
    after = view(registry, batch, workspace, scenario)
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
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> RequirementUpdateResponse:
    """Assign the requirement to an internal queue. Nothing is sent to an external recipient."""
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    workflow.route(
        Workspace(workspace), overlay.index, req_id, queue=body.queue, actor=body.actor,
        reason=body.reason,
    )
    return _requirement_response(registry, batch, workspace, scenario, req_id, started)


@router.post("/api/collection/{req_id}/status", response_model=RequirementUpdateResponse)
def set_requirement_status(
    req_id: str,
    body: RequirementStatusRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> RequirementUpdateResponse:
    started = time.perf_counter()
    scenario_adapter(registry, scenario)[1].check()
    workflow.set_status(
        Workspace(workspace), req_id, status=body.status, actor=body.actor, reason=body.reason
    )
    return _requirement_response(registry, batch, workspace, scenario, req_id, started)
