"""Tracked planning objects and the workspace itself."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..contracts import (
    AuditEntryView,
    PlanningResponse,
    PlanningReviewRequest,
    PlanningReviewResponse,
    WorkspaceResetRequest,
    WorkspaceResponse,
)
from ..product import overlay as overlay_module
from ..product import planning as planning_module
from ..product.store import Workspace
from ..scenarios import ScenarioRegistry
from ..views import planning_flag_views, planning_object_view
from .common import (
    BATCH_QUERY,
    SCENARIO_QUERY,
    WORKSPACE_QUERY,
    elapsed_ms,
    envelope,
    get_registry,
    view,
)

router = APIRouter()


@router.get("/api/planning", response_model=PlanningResponse)
def planning(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> PlanningResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    store = Workspace(workspace)
    return PlanningResponse(
        **envelope(overlay, started),
        objects=[
            planning_object_view(record)
            for record in planning_module.objects(overlay.index, store)
        ],
        flags=planning_flag_views(planning_module.flags(overlay.index, store)),
    )


@router.post("/api/planning/{object_id}/review", response_model=PlanningReviewResponse)
def review_planning_object(
    object_id: str,
    body: PlanningReviewRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> PlanningReviewResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    record = planning_module.review(
        overlay.index, Workspace(workspace), object_id,
        review_status=body.review_status,
        source_links=[link.model_dump() for link in body.source_links or []] or None,
        validity=body.validity.model_dump() if body.validity else None,
        actor=body.actor, reason=body.reason,
    )
    return PlanningReviewResponse(
        workspace=workspace, object=planning_object_view(record),
        response_ms=elapsed_ms(started),
    )


@router.get("/api/workspace", response_model=WorkspaceResponse)
def workspace_state(workspace: str = WORKSPACE_QUERY) -> WorkspaceResponse:
    store = Workspace(workspace)
    return WorkspaceResponse(
        **store.summary(),
        audit=[AuditEntryView(**entry) for entry in store.audit_log()],
    )


@router.post("/api/workspace/reset", response_model=WorkspaceResponse)
def reset_workspace(
    body: WorkspaceResetRequest | None = None,
    workspace: str = WORKSPACE_QUERY,
) -> WorkspaceResponse:
    """Clear one workspace. The dataset and every other workspace are untouched."""
    store = Workspace(workspace)
    store.reset()
    overlay_module.clear_cache()
    store.log((body.actor if body else "operator"), "workspace_reset", "workspace", workspace)
    return WorkspaceResponse(
        **store.summary(),
        audit=[AuditEntryView(**entry) for entry in store.audit_log()],
    )
