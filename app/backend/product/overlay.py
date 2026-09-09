"""The evaluation overlay: the batch's dataset claims plus the workspace's accepted claims,
put through the same ``eval.engine.recompute`` the replay path uses.

The overlay rule
----------------
``as_of`` is the batch's ``as_of``, or the latest ``asserted_at`` among the workspace's
accepted claims when that is later. The evaluator only ever selects a claim it already knows
about (``ClaimSet.all(known_at=as_of)``), so a report dated after the batch would otherwise be
invisible; moving the evaluation date forward is what makes newly reported evidence count, and
it moves the risk horizon windows with it. The dataset's own ``as_of`` is still reported as
``batch_as_of``.

With no accepted claims and no product requirements the overlay is not applied at all and the
read endpoints answer exactly as they did before.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date

from ..adapter import BatchSnapshot, DatasetAdapter, eval_module
from ..derive import Index
from .store import Workspace

# What a product report contributes to the ``sources`` table. Reliability and credibility are
# rated by a reviewer, not by the document: they stay null until a review supplies them.
PRODUCT_DOC_TYPE = "ingested_report"


@dataclass(frozen=True)
class Overlay:
    """One evaluated view of (batch, workspace)."""

    index: Index
    applied: bool
    workspace: str
    graph_version: int
    batch_as_of: str
    product_claim_ids: list[str]

    def envelope(self) -> dict:
        """The overlay half of the response envelope. All null when it was not applied."""
        if not self.applied:
            return {}
        return {
            "overlay_applied": True,
            "workspace": self.workspace,
            "graph_version": self.graph_version,
            "product_claim_ids": self.product_claim_ids,
            "batch_as_of": self.batch_as_of,
        }


_CACHE: dict[tuple, Overlay] = {}


def clear_cache() -> None:
    _CACHE.clear()


def evaluate(adapter: DatasetAdapter, batch: int, workspace_id: str) -> Overlay:
    """The batch as the workspace sees it, cached on (dataset, batch, workspace, versions)."""
    workspace = Workspace(workspace_id)
    key = (
        adapter.identity.key, batch, workspace_id,
        workspace.graph_version, workspace.state_version,
    )
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    overlay = _build(adapter, batch, workspace)
    _CACHE[key] = overlay
    return overlay


def _build(adapter: DatasetAdapter, batch: int, workspace: Workspace) -> Overlay:
    accepted = workspace.accepted_claims()
    requirements = workspace.requirements()
    if not accepted and not requirements:
        index = adapter.index(batch)
        return Overlay(
            index=index, applied=False, workspace=workspace.workspace_id,
            graph_version=workspace.graph_version, batch_as_of=index.snapshot.as_of,
            product_claim_ids=[],
        )

    started = time.perf_counter()
    snapshot = adapter.snapshot(batch)
    # The batch's own date comes off the cached snapshot: the overlay never reopens an inject
    # manifest, so nothing on the ingestion path touches one.
    batch_as_of = snapshot.as_of
    tables = snapshot.tables
    as_of = overlay_as_of(batch_as_of, accepted)

    claims = tables["claims"] + [record["claim"] for record in accepted]
    reports = {r["report_id"]: r for r in workspace.reports()}
    cited = {record["claim"]["source_id"] for record in accepted}
    tables["sources"] = tables["sources"] + [
        _source_row(report, batch) for report in reports.values()
        if report["source_id"] in cited
    ]
    tables["collection_requirements"] = tables["collection_requirements"] + [
        dict(record) for record in requirements
    ]

    recomputed = eval_module("engine").recompute(tables, as_of, batch, claims=claims)
    evaluated = BatchSnapshot(
        batch=batch,
        as_of=as_of.isoformat(),
        load_ms=round((time.perf_counter() - started) * 1000.0, 3),
        _tables=recomputed,
    )
    index = Index(evaluated, adapter.dataset_dir)
    for report in reports.values():
        index.attach_text(report["source_id"], report["text"])
    for record in accepted:
        for other in record["contradicts"]:
            index.register_contradiction(record["claim"]["claim_id"], other)
    return Overlay(
        index=index, applied=True, workspace=workspace.workspace_id,
        graph_version=workspace.graph_version, batch_as_of=batch_as_of,
        product_claim_ids=[record["claim"]["claim_id"] for record in accepted],
    )


def overlay_as_of(batch_as_of: str, accepted: list[dict]) -> date:
    """The batch date, or the latest accepted assertion when the reporting is more recent."""
    dates = [date.fromisoformat(batch_as_of)]
    for record in accepted:
        claim = record["claim"]
        stamp = claim.get("asserted_at") or claim.get("valid_from")
        if stamp:
            dates.append(date.fromisoformat(stamp))
    return max(dates)


def _source_row(report: dict, batch: int) -> dict:
    return {
        "source_id": report["source_id"],
        "title": report["filename"],
        "path": f"workspace://{report['report_id']}",
        "doc_type": PRODUCT_DOC_TYPE,
        "author_org": report["actor"],
        "reliability": None,
        "credibility": None,
        "published_at": report["report_date"] or report["uploaded_at"][:10],
        "batch": batch,
        "perturbations": [],
        "real_world": False,
        "public_reference": None,
        "text_sha256": report["sha256"],
    }
