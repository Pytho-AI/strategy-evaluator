"""Identity, branding and batch metadata."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..adapter import BATCHES, DatasetAdapter
from ..branding import MARKING, PRODUCT_NAME
from ..contracts import (
    BatchMeta,
    DatasetIdentityView,
    HealthResponse,
    MetaResponse,
    ScenarioMeta,
    WorldsMeta,
)
from ..scenarios import ScenarioRegistry
from .common import get_adapter, get_registry

DATASET_NAME = "strategy-evaluation-dataset-pytho"

WORLDS_NOTE = (
    "blue_worlds is the number of theta-assignments over the Blue actor's assumptions. "
    "The data card's '66 worlds' is distinct_world_labels: the union of payoffs.world "
    "label strings across all four (game, actor) pairs, where the three K=1 actors share "
    "the labels '0' and '1'. Summing the per-actor world sets instead gives 70."
)

router = APIRouter()


def identity_view(adapter: DatasetAdapter) -> DatasetIdentityView:
    adapter.check()
    identity = adapter.identity
    return DatasetIdentityView(
        archive_sha256=identity.archive_sha256,
        git_head=identity.git_head,
        key=identity.key,
    )


@router.get("/api/health", response_model=HealthResponse)
def health(adapter: DatasetAdapter = Depends(get_adapter)) -> HealthResponse:
    snapshot = adapter.snapshot(0)
    return HealthResponse(
        ok=True, dataset=identity_view(adapter), load_ms=snapshot.load_ms
    )


@router.get("/api/meta", response_model=MetaResponse)
def meta(
    adapter: DatasetAdapter = Depends(get_adapter),
    registry: ScenarioRegistry = Depends(get_registry),
) -> MetaResponse:
    snapshots = [adapter.snapshot(b) for b in BATCHES]
    blue_worlds, distinct_labels = adapter.world_counts(snapshots[-1])
    return MetaResponse(
        product_name=PRODUCT_NAME,
        dataset_name=DATASET_NAME,
        marking=MARKING,
        dataset=identity_view(adapter),
        scenarios=[ScenarioMeta(**row) for row in registry.describe()],
        default_scenario=registry.default_id(),
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
