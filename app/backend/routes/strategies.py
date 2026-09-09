"""Strategy comparison: the scenario's friendly options, side by side."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..contracts import StrategiesResponse, StrategyDetailResponse
from ..derive import caution
from ..errors import UnknownId
from ..scenarios import ScenarioRegistry
from ..views import blue_strategy_ids, strategy_detail
from .common import (
    BATCH_QUERY,
    SCENARIO_QUERY,
    WORKSPACE_QUERY,
    envelope,
    get_registry,
    view,
)

router = APIRouter()


@router.get("/api/strategies", response_model=StrategiesResponse)
def strategies(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> StrategiesResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    index = overlay.index
    entry = registry.entry(registry.resolve(scenario))
    return StrategiesResponse(
        **envelope(overlay, started),
        caution=caution(),
        ranking=index.ranking(entry.game_id, entry.actor_id),
        strategies=[
            strategy_detail(index, sid)
            for sid in blue_strategy_ids(index, entry.game_id, entry.actor_id)
        ],
    )


@router.get("/api/strategies/{strategy_id}", response_model=StrategyDetailResponse)
def strategy(
    strategy_id: str,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> StrategyDetailResponse:
    started = time.perf_counter()
    overlay = view(registry, batch, workspace, scenario)
    index = overlay.index
    entry = registry.entry(registry.resolve(scenario))
    ids = blue_strategy_ids(index, entry.game_id, entry.actor_id)
    if strategy_id not in ids:
        raise UnknownId(
            f"no {entry.actor_id} strategy {strategy_id!r} in batch {batch}. "
            "GET /api/strategies lists the options this scenario has.",
            {"strategy_id": strategy_id, "batch": batch, "scenario": entry.id},
        )
    return StrategyDetailResponse(
        **envelope(overlay, started),
        caution=caution(),
        ranking=index.ranking(entry.game_id, entry.actor_id),
        strategy=strategy_detail(index, strategy_id),
    )
