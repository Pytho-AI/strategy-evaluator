"""Strategy comparison: the three Blue options of the Meridian game, side by side."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from ..adapter import BLUE_ACTOR_ID, BLUE_GAME_ID, DatasetAdapter
from ..contracts import StrategiesResponse, StrategyDetailResponse
from ..derive import caution
from ..errors import UnknownId
from ..views import blue_strategy_ids, strategy_detail
from .common import BATCH_QUERY, WORKSPACE_QUERY, envelope, get_adapter, view

router = APIRouter()


@router.get("/api/strategies", response_model=StrategiesResponse)
def strategies(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> StrategiesResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    index = overlay.index
    return StrategiesResponse(
        **envelope(overlay, started),
        caution=caution(),
        ranking=index.ranking(BLUE_GAME_ID, BLUE_ACTOR_ID),
        strategies=[strategy_detail(index, sid) for sid in blue_strategy_ids(index)],
    )


@router.get("/api/strategies/{strategy_id}", response_model=StrategyDetailResponse)
def strategy(
    strategy_id: str,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> StrategyDetailResponse:
    started = time.perf_counter()
    overlay = view(adapter, batch, workspace)
    index = overlay.index
    if strategy_id not in blue_strategy_ids(index):
        raise UnknownId(
            f"no Blue strategy {strategy_id!r} in batch {batch}. "
            "GET /api/strategies lists the options this dataset has.",
            {"strategy_id": strategy_id, "batch": batch},
        )
    return StrategyDetailResponse(
        **envelope(overlay, started),
        caution=caution(),
        ranking=index.ranking(BLUE_GAME_ID, BLUE_ACTOR_ID),
        strategy=strategy_detail(index, strategy_id),
    )
