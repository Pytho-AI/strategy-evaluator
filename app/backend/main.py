"""FastAPI app for the Strategy Option Evaluation workbench (P0 read API)."""
from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .adapter import BATCHES, DatasetAdapter, VALIDITY_TESTS, BatchSnapshot
from .branding import MARKING, PRODUCT_NAME
from .contracts import (
    AssumptionView,
    BatchMeta,
    ClaimDetailResponse,
    CollectionRequirementView,
    DatasetIdentityView,
    ErrorResponse,
    HealthResponse,
    InjectManifestView,
    InjectsResponse,
    MetaResponse,
    ProblemSetAssessmentView,
    RankingView,
    SnapshotResponse,
    SourceView,
    StrategyDetailResponse,
    StrategyObjectiveView,
    StrategyView,
    ValidityTestView,
    WorldsMeta,
)
from .errors import DatasetError, UnknownId

DATASET_NAME = "strategy-evaluation-dataset-pytho"

WORLDS_NOTE = (
    "blue_worlds is the number of theta-assignments over the Blue actor's assumptions. "
    "The data card's '66 worlds' is distinct_world_labels: the union of payoffs.world "
    "label strings across all four (game, actor) pairs, where the three K=1 actors share "
    "the labels '0' and '1'. Summing the per-actor world sets instead gives 70."
)

BATCH_QUERY = Query(
    0,
    ge=min(BATCHES),
    le=max(BATCHES),
    description="inject batch: 0 (T0), 1, 2, or 3",
)


def create_app(adapter: DatasetAdapter | None = None) -> FastAPI:
    if adapter is None:
        configured = os.environ.get("STRATEGY_DATASET_DIR")
        adapter = DatasetAdapter(Path(configured)) if configured else DatasetAdapter()

    app = FastAPI(
        title=f"{PRODUCT_NAME} — Strategy Option Evaluation API",
        description=(
            f"Read-only replay over {DATASET_NAME}. {MARKING}. "
            "Every computed value comes from dataset.load()/eval.engine."
        ),
        version="0.1.0",
    )
    app.state.adapter = adapter

    def get_adapter() -> DatasetAdapter:
        return app.state.adapter

    @app.exception_handler(DatasetError)
    async def _dataset_error(_: Request, exc: DatasetError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=ErrorResponse.model_validate(
                {"error": {"code": exc.code, "message": exc.message, "detail": exc.detail}}
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def _bad_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse.model_validate(
                {
                    "error": {
                        "code": "invalid_request",
                        "message": (
                            "batch must be an integer 0, 1, 2 or 3."
                            if any("batch" in str(e.get("loc", ())) for e in exc.errors())
                            else "request parameters failed validation."
                        ),
                        "detail": {"errors": _jsonable_errors(exc)},
                    }
                }
            ).model_dump(),
        )

    @app.get("/api/health", response_model=HealthResponse)
    def health(adapter: DatasetAdapter = Depends(get_adapter)) -> HealthResponse:
        snapshot = adapter.snapshot(0)
        return HealthResponse(
            ok=True,
            dataset=_identity_view(adapter),
            load_ms=snapshot.load_ms,
        )

    @app.get("/api/meta", response_model=MetaResponse)
    def meta(adapter: DatasetAdapter = Depends(get_adapter)) -> MetaResponse:
        snapshots = [adapter.snapshot(b) for b in BATCHES]
        blue_worlds, distinct_labels = adapter.world_counts(snapshots[-1])
        return MetaResponse(
            product_name=PRODUCT_NAME,
            dataset_name=DATASET_NAME,
            marking=MARKING,
            dataset=_identity_view(adapter),
            batches=[
                BatchMeta(batch=s.batch, as_of=s.as_of, table_counts=s.table_counts)
                for s in snapshots
            ],
            worlds=WorldsMeta(
                blue_worlds=blue_worlds,
                distinct_world_labels=distinct_labels,
                note=WORLDS_NOTE,
            ),
        )

    @app.get("/api/injects", response_model=InjectsResponse)
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

    @app.get("/api/snapshot", response_model=SnapshotResponse)
    def snapshot(
        batch: int = BATCH_QUERY,
        adapter: DatasetAdapter = Depends(get_adapter),
    ) -> SnapshotResponse:
        started = time.perf_counter()
        return _snapshot_response(adapter, adapter.snapshot(batch), started)

    @app.get("/api/strategies/{strategy_id}", response_model=StrategyDetailResponse)
    def strategy(
        strategy_id: str,
        batch: int = BATCH_QUERY,
        adapter: DatasetAdapter = Depends(get_adapter),
    ) -> StrategyDetailResponse:
        started = time.perf_counter()
        snap = adapter.snapshot(batch)
        row = snap.find("strategies", "strategy_id", strategy_id)
        if row is None:
            raise UnknownId(
                f"no strategy {strategy_id!r} in batch {batch}. "
                "GET /api/snapshot lists the strategy ids this dataset has.",
                {"strategy_id": strategy_id, "batch": batch},
            )
        return StrategyDetailResponse(
            batch=snap.batch,
            as_of=snap.as_of,
            marking=MARKING,
            load_ms=snap.load_ms,
            response_ms=_elapsed_ms(started),
            strategy=_strategy_view(row),
            assumptions=[
                _assumption_view(a)
                for a in snap.rows_where("assumptions", "strategy_id", strategy_id)
            ],
            objectives=[
                StrategyObjectiveView(objective_id=o["objective_id"], weight=o["weight"])
                for o in snap.rows_where(
                    "strategy_objectives", "strategy_id", strategy_id
                )
            ],
        )

    @app.get("/api/claims/{claim_id}", response_model=ClaimDetailResponse)
    def claim(
        claim_id: str,
        batch: int = BATCH_QUERY,
        adapter: DatasetAdapter = Depends(get_adapter),
    ) -> ClaimDetailResponse:
        started = time.perf_counter()
        snap = adapter.snapshot(batch)
        row = snap.find("claims", "claim_id", claim_id)
        if row is None:
            raise UnknownId(
                f"no claim {claim_id!r} in batch {batch}.",
                {"claim_id": claim_id, "batch": batch},
            )
        source = snap.find("sources", "source_id", row["source_id"])
        return ClaimDetailResponse(
            batch=snap.batch,
            as_of=snap.as_of,
            marking=MARKING,
            load_ms=snap.load_ms,
            response_ms=_elapsed_ms(started),
            claim=row,
            source=(
                SourceView(
                    source_id=source["source_id"],
                    title=source["title"],
                    path=source["path"],
                )
                if source
                else None
            ),
        )

    return app


def _identity_view(adapter: DatasetAdapter) -> DatasetIdentityView:
    adapter.check()
    identity = adapter.identity
    return DatasetIdentityView(
        archive_sha256=identity.archive_sha256,
        git_head=identity.git_head,
        key=identity.key,
    )


def _jsonable_errors(exc: RequestValidationError) -> list[dict]:
    out = []
    for error in exc.errors():
        out.append(
            {
                "loc": [str(part) for part in error.get("loc", ())],
                "msg": str(error.get("msg", "")),
                "type": str(error.get("type", "")),
            }
        )
    return out


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def _strategy_view(s: dict) -> StrategyView:
    return StrategyView(
        strategy_id=s["strategy_id"],
        game_id=s["game_id"],
        actor_id=s["actor_id"],
        name=s["name"],
        status=s["status"],
        value=s["value"],
        adversary_range=s["value_ci"],
        robustness=s["robustness"],
        validity=[
            ValidityTestView(
                test=name,
                passed=s["validity"][name]["pass"],
                evidence=s["validity"][name]["evidence"],
            )
            for name in VALIDITY_TESTS
        ],
    )


def _assumption_view(a: dict) -> AssumptionView:
    return AssumptionView(
        assumption_id=a["assumption_id"],
        strategy_id=a["strategy_id"],
        index_k=a["index_k"],
        statement=a["statement"],
        status=a["status"],
        p_holds=a["p_holds"],
        sensitivity=a["sensitivity"],
        evpi=a["evpi"],
    )


def _snapshot_response(
    adapter: DatasetAdapter, snap: BatchSnapshot, started: float
) -> SnapshotResponse:
    strategies = snap.table("strategies")
    actors = sorted({(s["game_id"], s["actor_id"]) for s in strategies})
    return SnapshotResponse(
        batch=snap.batch,
        as_of=snap.as_of,
        marking=MARKING,
        load_ms=snap.load_ms,
        response_ms=_elapsed_ms(started),
        strategies=[_strategy_view(s) for s in strategies],
        rankings=[
            RankingView(
                game_id=game_id,
                actor_id=actor_id,
                strategy_ids=adapter.ranking(snap, game_id, actor_id),
            )
            for game_id, actor_id in actors
        ],
        assumptions=[_assumption_view(a) for a in snap.table("assumptions")],
        problem_set_assessments=[
            ProblemSetAssessmentView(
                problem_set_id=p["problem_set_id"],
                jsps_horizon=p["jsps_horizon"],
                max_risk_level=p["max_risk_level"],
                he_ids=p["he_ids"],
                aggregated_statement_text=p["aggregated_statement_text"],
            )
            for p in snap.table("problem_set_assessments")
        ],
        collection_requirements=[
            CollectionRequirementView(
                req_id=r["req_id"],
                status=r["status"],
                priority=r["priority"],
                jipcl_rank=r["jipcl_rank"],
            )
            for r in snap.table("collection_requirements")
        ],
    )


app = create_app()
