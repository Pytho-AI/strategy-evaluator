"""The first screen: one snapshot of the selected batch, with the decision overview."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..contracts import (
    CollectionRequirementView,
    ProblemSetAssessmentView,
    RankingView,
    SnapshotResponse,
)
from ..scenarios import ScenarioRegistry
from ..views import assumption_view, decision_overview, strategy_view
from .common import (
    BATCH_QUERY,
    SCENARIO_QUERY,
    WORKSPACE_QUERY,
    envelope,
    get_registry,
    view,
)

router = APIRouter()


@router.get("/api/snapshot", response_model=SnapshotResponse)
def snapshot(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> SnapshotResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    index = overlay.index
    strategies = index.rows("strategies")
    actors = sorted({(s["game_id"], s["actor_id"]) for s in strategies})
    return SnapshotResponse(
        **envelope(overlay, started),
        decision_overview=decision_overview(index),
        strategies=[strategy_view(s) for s in strategies],
        rankings=[
            RankingView(
                game_id=game_id,
                actor_id=actor_id,
                strategy_ids=index.ranking(game_id, actor_id),
            )
            for game_id, actor_id in actors
        ],
        assumptions=[assumption_view(index, a) for a in index.rows("assumptions")],
        problem_set_assessments=[
            ProblemSetAssessmentView(
                problem_set_id=p["problem_set_id"],
                jsps_horizon=p["jsps_horizon"],
                max_risk_level=p["max_risk_level"],
                he_ids=p["he_ids"],
                aggregated_statement_text=p["aggregated_statement_text"],
            )
            for p in index.rows("problem_set_assessments")
        ],
        collection_requirements=[
            CollectionRequirementView(
                req_id=r["req_id"],
                status=r["status"],
                priority=r["priority"],
                jipcl_rank=r["jipcl_rank"],
            )
            for r in index.rows("collection_requirements")
        ],
    )
