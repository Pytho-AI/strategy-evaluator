"""Tracked planning objects: assumptions, constraints and restraints.

An assumption is a planning proposition grounded in claims; it is not the claim. The frozen
schema carries assumptions with a grounding (subject, predicate) but carries constraints and
restraints only as strings on ``strategies``. Those get product-owned sidecar records with
``source_links: []``, ``validity: null``, ``confidence: null`` and
``review_status: "unreviewed"`` — their provenance is stated as absent, never invented.
"""
from __future__ import annotations

from ..adapter import BLUE_GAME_ID
from ..derive import Index
from ..errors import UnknownId
from .store import Workspace, now

REVIEW_STATUSES = ("unreviewed", "reviewed", "needs_review", "invalidated")
UNREVIEWED = "unreviewed"


def _span(index: Index, claim: dict) -> dict:
    source = index.sources.get(claim["source_id"])
    return {
        "claim_id": claim["claim_id"],
        "source_id": claim["source_id"],
        "source_title": source["title"] if source else None,
        "span_start": claim["span_start"],
        "span_end": claim["span_end"],
        "span_text": index.span_text(claim),
    }


def seeded(index: Index) -> list[dict]:
    """Every tracked object the dataset supports, before any product review is merged in."""
    out: list[dict] = []
    strategies = [s for s in index.rows("strategies") if s["game_id"] == BLUE_GAME_ID]
    ids = {s["strategy_id"] for s in strategies}
    for assumption in index.rows("assumptions"):
        if assumption["strategy_id"] not in ids:
            continue
        claim = index.current_claim(assumption["subject_id"], assumption["predicate"])
        out.append({
            "object_id": assumption["assumption_id"],
            "kind": "assumption",
            "strategy_id": assumption["strategy_id"],
            "text": assumption["statement"],
            "subject_id": assumption["subject_id"],
            "predicate": assumption["predicate"],
            "status": assumption["status"],
            "source_links": [_span(index, claim)] if claim else [],
            "validity": (
                {"valid_from": claim["valid_from"], "valid_to": claim.get("valid_to")}
                if claim else None
            ),
            "confidence": (
                {
                    "confidence_icd203": claim["confidence_icd203"],
                    "confidence": claim["confidence"],
                }
                if claim else None
            ),
            "review_status": UNREVIEWED,
            "provenance": "dataset" if claim else "ungrounded at this as-of date",
            "review": None,
        })
    for strategy in sorted(strategies, key=lambda s: s["strategy_id"]):
        for kind, prefix, field in (
            ("constraint", "pcon", "constraints"), ("restraint", "pres", "restraints")
        ):
            for position, text in enumerate(strategy.get(field) or []):
                out.append({
                    "object_id": f"{prefix}_{strategy['strategy_id']}_{position}",
                    "kind": kind,
                    "strategy_id": strategy["strategy_id"],
                    "text": text,
                    "subject_id": None,
                    "predicate": None,
                    "status": None,
                    "source_links": [],
                    "validity": None,
                    "confidence": None,
                    "review_status": UNREVIEWED,
                    "provenance": (
                        "absent: the frozen schema carries this "
                        f"{kind} as text on {strategy['strategy_id']} with no source span, "
                        "validity window or confidence"
                    ),
                    "review": None,
                })
    return out


def objects(index: Index, workspace: Workspace) -> list[dict]:
    """Seeded objects with the workspace's reviews merged in."""
    reviews = workspace.planning_objects()
    out = []
    for record in seeded(index):
        review = reviews.get(record["object_id"])
        if review is not None:
            record = dict(
                record,
                review_status=review["review_status"],
                source_links=review["source_links"] or record["source_links"],
                validity=review["validity"] or record["validity"],
                review=review,
            )
        out.append(record)
    return out


def review(
    index: Index,
    workspace: Workspace,
    object_id: str,
    *,
    review_status: str,
    source_links: list[dict] | None,
    validity: dict | None,
    actor: str,
    reason: str | None,
) -> dict:
    if review_status not in REVIEW_STATUSES:
        raise UnknownId(
            f"review_status must be one of {', '.join(REVIEW_STATUSES)}.",
            {"review_status": review_status},
        )
    known = {record["object_id"]: record for record in seeded(index)}
    if object_id not in known:
        raise UnknownId(
            f"no tracked planning object {object_id!r} in this batch.",
            {"object_id": object_id},
        )
    existing = workspace.planning_object(object_id) or {"history": []}
    entry = {
        "review_status": review_status, "actor": actor, "at": now(), "reason": reason,
        "source_links": source_links or [], "validity": validity,
    }
    record = {
        "object_id": object_id,
        "review_status": review_status,
        "source_links": source_links or existing.get("source_links") or [],
        "validity": validity if validity is not None else existing.get("validity"),
        "reviewed_by": actor,
        "reviewed_at": entry["at"],
        "reason": reason,
        "history": existing["history"] + [entry],
    }
    workspace.save_planning_object(object_id, record)
    workspace.add_decision(
        target_type="planning_object", target_id=object_id, decision=review_status,
        actor=actor, reason=reason,
    )
    workspace.log(actor, "planning_reviewed", "planning_object", object_id,
                  {"review_status": review_status})
    return dict(known[object_id], review_status=review_status, review=record,
                source_links=record["source_links"] or known[object_id]["source_links"],
                validity=record["validity"] or known[object_id]["validity"])


def flags(index: Index, workspace: Workspace, claim_ids: list[str] | None = None) -> list[dict]:
    """Tracked objects the latest accepted evidence touches, and the options that depend on them.

    An assumption is flagged when the accepted claim shares its (subject, predicate) — that is
    the grounding the evaluator itself uses. A constraint or restraint is flagged when a
    reviewer has linked the changed claim to it; unreviewed sidecars have no links, so they
    are never flagged on a guess.
    """
    accepted = workspace.accepted_claims()
    if claim_ids is None:
        version = workspace.graph_version
        accepted = [r for r in accepted if r["accepted_graph_version"] == version]
    else:
        accepted = [r for r in accepted if r["claim"]["claim_id"] in set(claim_ids)]
    if not accepted:
        return []
    keys = {(r["claim"]["subject_id"], r["claim"]["predicate"]): r["claim"] for r in accepted}
    changed_ids = {r["claim"]["claim_id"] for r in accepted}

    requires = [
        edge for edge in index.rows("dependencies")
        if edge["kind"] == "requires" and edge["to_type"] == "strategy"
    ]
    out = []
    for record in objects(index, workspace):
        claim = keys.get((record["subject_id"], record["predicate"]))
        linked = [
            link for link in record["source_links"] if link.get("claim_id") in changed_ids
        ]
        if claim is None and not linked:
            continue
        options = {record["strategy_id"]} | {
            edge["to_id"] for edge in requires if edge["from_id"] == record["object_id"]
        }
        out.append({
            "object_id": record["object_id"],
            "kind": record["kind"],
            "text": record["text"],
            "review_status": record["review_status"],
            "reason": (
                f"the accepted claim {claim['claim_id']} reports "
                f"({record['subject_id']}, {record['predicate']}), which grounds this assumption"
                if claim is not None else
                f"a reviewer linked {', '.join(sorted(l['claim_id'] for l in linked))} to this "
                f"{record['kind']}"
            ),
            "claim_ids": sorted(
                ({claim["claim_id"]} if claim is not None else set())
                | {link["claim_id"] for link in linked}
            ),
            "dependent_options": sorted(o for o in options if o in index.strategies),
        })
    return out
