"""What every router needs: the adapter dependency, batch/workspace/scenario parameters,
the envelope."""
from __future__ import annotations

import time

from fastapi import Query, Request

from ..adapter import BATCHES, DatasetAdapter
from ..branding import MARKING
from ..product.overlay import Overlay, evaluate
from ..product.store import DEFAULT_WORKSPACE
from ..scenarios import ScenarioRegistry

BATCH_QUERY = Query(
    0,
    ge=min(BATCHES),
    le=max(BATCHES),
    description="inject batch: 0 (T0), 1, 2, or 3",
)

WORKSPACE_QUERY = Query(
    DEFAULT_WORKSPACE,
    min_length=1,
    max_length=64,
    pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    description=(
        "product workspace whose accepted claims overlay this batch. An empty workspace "
        "changes nothing: the response is the replay response."
    ),
)

SCENARIO_QUERY = Query(
    None,
    description=(
        "which scenario to serve. Omitted resolves to the registry default "
        "(amber_shield when its package loads, else meridian). An unknown id is 422 and "
        "names the valid ids; GET /api/meta lists them."
    ),
)


def get_adapter(request: Request) -> DatasetAdapter:
    """The adapter the app was constructed with: the frozen ``dataset/`` checkout."""
    return request.app.state.adapter


def get_registry(request: Request) -> ScenarioRegistry:
    return request.app.state.scenarios


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)


def scenario_adapter(
    registry: ScenarioRegistry, scenario: str | None
) -> tuple[str, DatasetAdapter]:
    """(scenario id, its adapter). 422 for an unknown id, 503 for one that will not load."""
    scenario_id = registry.resolve(scenario)
    return scenario_id, registry.adapter(scenario_id)


def view(
    registry: ScenarioRegistry, batch: int, workspace: str, scenario: str | None
) -> Overlay:
    """The batch of one scenario as this workspace sees it.

    ``product/overlay.py`` documents the as-of rule; the overlay cache is keyed on
    (scenario id, scenario identity, batch, workspace, graph_version, state_version).
    """
    scenario_id, adapter = scenario_adapter(registry, scenario)
    registry.check_batch(scenario_id, batch)
    adapter.check()
    return evaluate(adapter, batch, workspace, scenario_id)


def envelope(overlay: Overlay, started: float) -> dict:
    index = overlay.index
    return {
        "batch": index.batch,
        "as_of": index.snapshot.as_of,
        "marking": MARKING,
        "load_ms": index.snapshot.load_ms,
        "response_ms": elapsed_ms(started),
        **overlay.envelope(),
    }
