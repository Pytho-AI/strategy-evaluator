"""Typed API responses. Every value is copied straight out of the loaded dataset."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatasetIdentityView(BaseModel):
    """What the batch cache is keyed on."""

    archive_sha256: str | None = Field(description="SHA-256 of the frozen dataset archive")
    git_head: str | None = Field(description="git HEAD of the dataset checkout, if any")
    key: str = Field(description="cache key component: <archive sha>:<git head>")


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    ok: bool
    dataset: DatasetIdentityView
    load_ms: float = Field(
        description="milliseconds of the load that filled the batch-0 cache entry"
    )


class BatchMeta(BaseModel):
    batch: int
    as_of: str
    table_counts: dict[str, int]


class WorldsMeta(BaseModel):
    blue_worlds: int = Field(
        description="theta-assignments over the Blue actor's K assumptions"
    )
    distinct_world_labels: int = Field(
        description="distinct payoffs.world label strings across every actor"
    )
    note: str


class MetaResponse(BaseModel):
    product_name: str
    dataset_name: str
    marking: str
    dataset: DatasetIdentityView
    batches: list[BatchMeta]
    worlds: WorldsMeta


class InjectManifestView(BaseModel):
    batch: int
    as_of: str
    docs: list[str]
    change_events: list[dict[str, Any]]
    expected_effects: dict[str, Any]


class InjectsResponse(BaseModel):
    injects: list[InjectManifestView]


class ValidityTestView(BaseModel):
    test: str
    passed: bool
    evidence: str


class StrategyView(BaseModel):
    strategy_id: str
    game_id: str
    actor_id: str
    name: str
    status: str
    value: float
    adversary_range: list[float] = Field(
        description=(
            "dataset value_ci: min/max expected value across adversary COAs. "
            "Not a statistical confidence interval."
        )
    )
    robustness: float
    validity: list[ValidityTestView]


class RankingView(BaseModel):
    game_id: str
    actor_id: str
    strategy_ids: list[str] = Field(description="valid strategies, best value first")


class AssumptionView(BaseModel):
    assumption_id: str
    strategy_id: str
    index_k: int
    statement: str
    status: str
    p_holds: float
    sensitivity: float | None
    evpi: float | None


class ProblemSetAssessmentView(BaseModel):
    problem_set_id: str
    jsps_horizon: str
    max_risk_level: str
    he_ids: list[str]
    aggregated_statement_text: str


class CollectionRequirementView(BaseModel):
    req_id: str
    status: str
    priority: float | None
    jipcl_rank: int | None


class StrategyObjectiveView(BaseModel):
    objective_id: str
    weight: float = Field(description="w_k: the strategy's weight on this objective")


class SourceView(BaseModel):
    source_id: str
    title: str
    path: str = Field(description="path under dataset/ the claim was extracted from")


class StrategyDetailResponse(BaseModel):
    batch: int
    as_of: str
    marking: str
    load_ms: float = Field(description="milliseconds of the load that filled the cache")
    response_ms: float = Field(description="milliseconds spent serving this request")
    strategy: StrategyView
    assumptions: list[AssumptionView]
    objectives: list[StrategyObjectiveView]


class ClaimDetailResponse(BaseModel):
    batch: int
    as_of: str
    marking: str
    load_ms: float = Field(description="milliseconds of the load that filled the cache")
    response_ms: float = Field(description="milliseconds spent serving this request")
    claim: dict[str, Any] = Field(description="the claim row as loaded; typed in P1")
    source: SourceView | None


class SnapshotResponse(BaseModel):
    batch: int
    as_of: str
    marking: str
    load_ms: float = Field(description="milliseconds of the load that filled the cache")
    response_ms: float = Field(description="milliseconds spent serving this request")
    strategies: list[StrategyView]
    rankings: list[RankingView]
    assumptions: list[AssumptionView]
    problem_set_assessments: list[ProblemSetAssessmentView]
    collection_requirements: list[CollectionRequirementView]
