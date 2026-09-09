"""Claim review: accept or reject a proposed claim and recompute what it changed.

Accepting bumps ``graph_version``, re-evaluates through ``eval.engine.recompute``, reconciles
the collection requirements, and answers with the difference between the two evaluations plus
the tracked planning objects the new evidence touches.

A contradictory accepted claim never silently replaces approved dataset evidence: both stay
visible and flagged as contradicting each other, and the response names the claim the
evaluator's as-of selection rule actually chose.
"""
from __future__ import annotations

from datetime import date

from ..adapter import DatasetAdapter, eval_module
from ..derive import Index
from ..errors import DatasetError, UnknownId
from . import collection, overlay, planning
from .store import Workspace

REQUIRED_FIELDS = ("subject_id", "predicate", "valid_from", "asserted_at", "confidence_icd203")
EDITABLE_FIELDS = (
    "subject_id", "predicate", "object_id", "value", "value_type", "unit", "valid_from",
    "valid_to", "asserted_at", "estimative", "likelihood_icd203", "confidence_icd203",
)


class ReviewRejected(DatasetError):
    code = "invalid_request"
    http_status = 422


class AlreadyDecided(DatasetError):
    code = "already_decided"
    http_status = 409


def derived_confidence(claim: dict) -> float | None:
    """eval.value.derived_confidence — the dataset's own formula, never re-implemented here."""
    if not claim.get("confidence_icd203"):
        return None
    return eval_module("value").derived_confidence(
        claim.get("estimative", False), claim.get("likelihood_icd203"),
        claim["confidence_icd203"],
    )


def _validate(claim: dict, index: Index, predicates: dict) -> dict:
    missing = [f for f in REQUIRED_FIELDS if claim.get(f) in (None, "")]
    if claim.get("value") is None and claim.get("object_id") is None:
        missing.append("value")
    if missing:
        raise ReviewRejected(
            "this proposed claim cannot be accepted as it stands: the report does not state "
            f"{', '.join(sorted(set(missing)))}. Supply the missing fields in `revision`, or "
            "reject the claim. Nothing is filled in for you.",
            {"missing": sorted(set(missing)), "flags": claim.get("flags", [])},
        )
    predicate = claim["predicate"]
    if predicate not in predicates:
        raise ReviewRejected(
            f"predicate {predicate!r} is not in the controlled vocabulary.",
            {"predicate": predicate, "allowed": sorted(predicates)},
        )
    value_type, unit, allowed, _ = predicates[predicate]
    if allowed is not None and claim.get("value") not in allowed:
        raise ReviewRejected(
            f"{predicate} takes one of {', '.join(allowed)}; got {claim.get('value')!r}.",
            {"predicate": predicate, "value": claim.get("value"), "allowed": allowed},
        )
    if value_type == "entity" and not claim.get("object_id"):
        raise ReviewRejected(
            f"{predicate} is a relation: it needs a resolved object_id.",
            {"predicate": predicate},
        )
    if index.entities.get(claim["subject_id"]) is None:
        raise UnknownId(
            f"no entity {claim['subject_id']!r} in this batch.",
            {"subject_id": claim["subject_id"]},
        )
    if claim.get("object_id") and index.entities.get(claim["object_id"]) is None:
        raise UnknownId(
            f"no entity {claim['object_id']!r} in this batch.",
            {"object_id": claim["object_id"]},
        )
    return dict(claim, value_type=value_type, unit=unit, status="approved",
                confidence=derived_confidence(claim))


def _contradicted(claim: dict, index: Index) -> list[str]:
    """Approved claims this one disagrees with over an overlapping valid-time window."""
    out = []
    for other in index.rows("claims"):
        if other["status"] != "approved":
            continue
        if (other["subject_id"], other["predicate"]) != (claim["subject_id"], claim["predicate"]):
            continue
        if index.claim_value(other) == _value_of(claim):
            continue
        if _overlaps(claim, other):
            out.append(other["claim_id"])
    return sorted(out)


def _value_of(claim: dict) -> object:
    return claim["object_id"] if claim.get("value_type") == "entity" else claim.get("value")


def _overlaps(a: dict, b: dict) -> bool:
    a_from = date.fromisoformat(a["valid_from"])
    b_from = date.fromisoformat(b["valid_from"])
    a_to = date.fromisoformat(a["valid_to"]) if a.get("valid_to") else None
    b_to = date.fromisoformat(b["valid_to"]) if b.get("valid_to") else None
    return (a_to is None or a_to >= b_from) and (b_to is None or b_to >= a_from)


def decide(
    adapter: DatasetAdapter,
    workspace: Workspace,
    *,
    batch: int,
    claim_id: str,
    decision: str,
    actor: str,
    reason: str | None,
    revision: dict | None,
) -> dict:
    record = workspace.claim(claim_id)
    if record is None:
        raise UnknownId(
            f"no proposed claim {claim_id!r} in workspace {workspace.workspace_id!r}.",
            {"claim_id": claim_id, "workspace": workspace.workspace_id},
        )
    if record["status"] != "proposed":
        raise AlreadyDecided(
            f"claim {claim_id} was already {record['status']}. Review decisions are kept, "
            "not overwritten.",
            {"claim_id": claim_id, "status": record["status"]},
        )
    if decision not in ("accept", "reject"):
        raise ReviewRejected(
            "decision must be 'accept' or 'reject'.", {"decision": decision}
        )
    revision = {k: v for k, v in (revision or {}).items() if k in EDITABLE_FIELDS}
    before = overlay.evaluate(adapter, batch, workspace.workspace_id)

    if decision == "reject":
        workspace.set_claim(claim_id, status="rejected")
        review_decision = workspace.add_decision(
            target_type="proposed_claim", target_id=claim_id, decision="reject",
            actor=actor, reason=reason, revision=revision,
        )
        workspace.log(actor, "claim_rejected", "proposed_claim", claim_id, {"reason": reason})
        after = overlay.evaluate(adapter, batch, workspace.workspace_id)
        return {
            "claim": workspace.claim(claim_id), "decision": review_decision,
            "before": before, "after": after, "contradicts": [], "chosen_claim_id": None,
            "requirements_changed": [], "planning_flags": [],
        }

    from .ingest import _vocabulary

    predicates, _ = _vocabulary()
    merged = _validate(dict(record["claim"], **revision), before.index, predicates)
    contradicts = _contradicted(merged, before.index)
    contradiction_reason = (
        f"accepted claim {claim_id} reports {merged['predicate']} = {_value_of(merged)} for "
        f"{merged['subject_id']} over a valid-time window that overlaps approved "
        f"{', '.join(contradicts)}; both remain visible and the as-of selection rule decides "
        "which is current"
    ) if contradicts else None

    version = workspace.bump_graph_version()
    workspace.set_claim(
        claim_id, status="approved", data=merged, accepted_graph_version=version,
        contradicts=contradicts, contradicts_reason=contradiction_reason,
    )
    review_decision = workspace.add_decision(
        target_type="proposed_claim", target_id=claim_id, decision="accept", actor=actor,
        reason=reason, revision=revision,
    )
    workspace.log(actor, "claim_accepted", "proposed_claim", claim_id, {
        "graph_version": version, "contradicts": contradicts, "revision": revision,
    })

    mid = overlay.evaluate(adapter, batch, workspace.workspace_id)
    requirements_changed = collection.reconcile(workspace, mid.index, actor)
    after = overlay.evaluate(adapter, batch, workspace.workspace_id)
    current = after.index.current_claim(merged["subject_id"], merged["predicate"])
    return {
        "claim": workspace.claim(claim_id),
        "decision": review_decision,
        "before": before,
        "after": after,
        "contradicts": contradicts,
        "contradiction_reason": contradiction_reason,
        "chosen_claim_id": current["claim_id"] if current else None,
        "requirements_changed": requirements_changed,
        "planning_flags": planning.flags(after.index, workspace, [claim_id]),
    }
