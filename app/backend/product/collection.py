"""Product-owned collection requirements: draft, route, status, satisfaction and reopening.

Dataset requirements (``req_01``..``req_07``) stay read-only replay rows. Product ones are
``preq_0001``.. and carry ``owner: "product"``. A requirement closes only on reviewed
evidence: an *accepted* claim on its (subject, predicate) that meets its gap. A document
arriving — even one whose proposed claims match the gap exactly — never closes it.
"""
from __future__ import annotations

from datetime import date

from ..derive import Index
from ..errors import DatasetError, UnknownId
from .store import Workspace, now

QUEUES = ("JIOC", "JCMB")
OPEN_STATUSES = ("research", "validation", "submission")
CLOSED_STATUSES = ("satisfaction", "closed")
GAP_TYPES = ("missing", "stale", "low_confidence", "contradiction")


class InvalidRequest(DatasetError):
    code = "invalid_request"
    http_status = 422


def valid_queue(queue: str) -> bool:
    """JIOC, JCMB, or a named unit's J-2 (JP 2-01 Ch. III §13: an internal queue assignment)."""
    return queue in QUEUES or queue.strip().endswith("J-2")


def _valid_at(claim: dict, as_of: date) -> bool:
    asserted = date.fromisoformat(claim.get("asserted_at") or claim["valid_from"])
    valid_from = date.fromisoformat(claim["valid_from"])
    valid_to = date.fromisoformat(claim["valid_to"]) if claim.get("valid_to") else None
    return asserted <= as_of and valid_from <= as_of and (valid_to is None or valid_to >= as_of)


# ---------------------------------------------------------------- drafting
def create_draft(
    workspace: Workspace,
    index: Index,
    *,
    strategy_question: str | None,
    pir_id: str | None,
    assumption_id: str | None,
    subject_id: str | None,
    predicate: str | None,
    gap_type: str,
    required_evidence: str,
    gap_reason: str,
    proposed_owner: str,
    ltiov: str,
    sir: str,
    indicators: list[str],
    actor: str,
) -> tuple[dict, dict | None]:
    """A draft requirement, or the open one that already covers this gap.

    Returns ``(requirement, duplicate_decision)``; the decision is set when an open
    requirement for the same (subject, predicate, gap_type) already exists.
    """
    if not (strategy_question or pir_id):
        raise InvalidRequest(
            "a draft needs an explicit strategy question or a PIR id: pass "
            "strategy_question or pir_id.",
            {"missing": ["strategy_question", "pir_id"]},
        )
    if gap_type not in GAP_TYPES:
        raise InvalidRequest(
            f"gap_type must be one of {', '.join(GAP_TYPES)}.", {"gap_type": gap_type}
        )
    assumption = None
    if assumption_id:
        assumption = index.assumptions.get(assumption_id)
        if assumption is None:
            raise UnknownId(
                f"no assumption {assumption_id!r} in this batch.",
                {"assumption_id": assumption_id},
            )
        subject_id = subject_id or assumption["subject_id"]
        predicate = predicate or assumption["predicate"]
    if not (subject_id and predicate):
        raise InvalidRequest(
            "a draft needs a gap: pass subject_id and predicate, or an assumption_id to "
            "take them from.",
            {"missing": ["subject_id", "predicate"]},
        )
    if pir_id and index.by("pirs", "pir_id").get(pir_id) is None:
        raise UnknownId(f"no PIR {pir_id!r} in this batch.", {"pir_id": pir_id})
    if index.entities.get(subject_id) is None:
        raise UnknownId(f"no entity {subject_id!r} in this batch.", {"subject_id": subject_id})

    key = (subject_id, predicate, gap_type)
    for existing in workspace.requirements():
        if existing["status"] in CLOSED_STATUSES:
            continue
        if (existing["subject_id"], existing["predicate"], existing["gap_type"]) == key:
            decision = workspace.add_decision(
                target_type="collection_requirement", target_id=existing["req_id"],
                decision="duplicate_of", actor=actor,
                reason=(
                    f"a draft for {subject_id} {predicate} ({gap_type}) is already open as "
                    f"{existing['req_id']}"
                ),
            )
            workspace.log(actor, "requirement_deduplicated", "collection_requirement",
                          existing["req_id"], {"gap": list(key)})
            return existing, decision

    record = {
        "req_id": "", "owner": "product", "status": "research",
        "pir_id": pir_id or "", "eei": required_evidence, "indicators": list(indicators),
        "sir": sir, "gap_type": gap_type, "subject_id": subject_id, "predicate": predicate,
        "assumption_id": assumption_id, "rfi_disposition": "gap_confirmed",
        "routing": "unrouted", "ltiov": ltiov,
        # The scenario date this requirement is raised against, so the evaluator ranks it in
        # the batch it was drafted in; the wall-clock time is kept separately.
        "created_at": index.as_of.isoformat(), "created_actual_at": now(),
        "created_by": actor, "answered_by_source_id": None, "priority": None,
        "jipcl_rank": None, "strategy_question": strategy_question,
        "strategy_id": assumption["strategy_id"] if assumption else None,
        "gap_reason": gap_reason, "proposed_owner": proposed_owner,
        "required_evidence": required_evidence, "authority_tier_id": None,
        "closure_basis": None, "satisfied_by_claim_id": None, "reopen_to": None,
        "status_history": [],
    }
    record = workspace.add_requirement(record)
    record = _record_status(workspace, record, "research", actor, "draft created")
    workspace.log(actor, "requirement_drafted", "collection_requirement", record["req_id"],
                  {"gap": list(key), "pir_id": pir_id, "assumption_id": assumption_id})
    return record, None


def _record_status(
    workspace: Workspace, record: dict, status: str, actor: str, reason: str
) -> dict:
    record = dict(record)
    record["status_history"] = record["status_history"] + [
        {"status": status, "actor": actor, "at": now(), "reason": reason}
    ]
    record["status"] = status
    return workspace.save_requirement(record)


def product_requirement(workspace: Workspace, req_id: str) -> dict:
    record = workspace.requirement(req_id)
    if record is None:
        raise UnknownId(
            f"no product collection requirement {req_id!r} in this workspace. Dataset "
            "requirements (req_01..) are read-only replay rows and cannot be routed here.",
            {"req_id": req_id},
        )
    return record


def route(
    workspace: Workspace, index: Index, req_id: str, *, queue: str, actor: str, reason: str | None
) -> dict:
    """Assign the requirement to an internal queue. Nothing is sent anywhere."""
    if not valid_queue(queue):
        raise InvalidRequest(
            f"queue must be JIOC, JCMB or '<unit> J-2'; got {queue!r}.", {"queue": queue}
        )
    record = product_requirement(workspace, req_id)
    tier = _authority_tier(index)
    record = dict(record, routing=queue, authority_tier_id=tier)
    record = _record_status(
        workspace, record, "submission", actor,
        reason or f"routed to {queue}",
    )
    workspace.log(actor, "requirement_routed", "collection_requirement", req_id,
                  {"queue": queue, "authority_tier_id": tier})
    return record


def _authority_tier(index: Index) -> str | None:
    """The tier that approves a requirement submission, from the `authority` extension."""
    rule = next(
        (r for r in index.rows("recommendation_authority")
         if r["recommendation_type"] == "requirement_submit"),
        None,
    )
    return rule["tier_id"] if rule else None


def set_status(
    workspace: Workspace, req_id: str, *, status: str, actor: str, reason: str | None
) -> dict:
    record = product_requirement(workspace, req_id)
    if status in CLOSED_STATUSES:
        raise InvalidRequest(
            f"{status!r} is set by the satisfaction rule, not by hand: a requirement closes "
            "only when an accepted claim on its (subject, predicate) meets its gap.",
            {"req_id": req_id, "status": status},
        )
    if status not in OPEN_STATUSES:
        raise InvalidRequest(
            f"status must be one of {', '.join(OPEN_STATUSES)}.",
            {"req_id": req_id, "status": status},
        )
    record = _record_status(workspace, record, status, actor, reason or "status set by review")
    workspace.log(actor, "requirement_status_set", "collection_requirement", req_id,
                  {"status": status, "reason": reason})
    return record


# ---------------------------------------------------------------- satisfaction
def meets_gap(record: dict, claim: dict, index: Index, as_of: date) -> tuple[bool, str | None]:
    """Does this accepted claim satisfy the requirement's gap? (SCHEMA.md §3 GapType.)"""
    if (claim["subject_id"], claim["predicate"]) != (record["subject_id"], record["predicate"]):
        return False, None
    if not _valid_at(claim, as_of):
        return False, None
    gap = record["gap_type"]
    if gap in ("missing", "stale"):
        return True, f"an accepted claim on ({record['subject_id']}, {record['predicate']}) is valid at {as_of}"
    if gap == "low_confidence":
        if claim.get("confidence_icd203") in ("moderate", "high"):
            return True, (
                f"the accepted claim states confidence {claim['confidence_icd203']}, "
                "which is at least moderate"
            )
        return False, None
    if gap == "contradiction":
        current = index.current_claim(record["subject_id"], record["predicate"])
        if current is not None and current["claim_id"] == claim["claim_id"]:
            return True, (
                f"the accepted claim {claim['claim_id']} supersedes the contradicted value: "
                "the as-of rule selects it as current"
            )
        if current is not None and index.claim_value(current) == index.claim_value(claim):
            return True, (
                f"the accepted claim corroborates the approved value carried by "
                f"{current['claim_id']}"
            )
        return False, None
    return False, None


def reconcile(workspace: Workspace, index: Index, actor: str = "system") -> list[dict]:
    """Close every product requirement its accepted evidence now meets; reopen the rest.

    Runs after each review decision, and is the only path that writes `satisfaction`.
    """
    accepted = [record["claim"] for record in workspace.accepted_claims()]
    as_of = index.as_of
    changed: list[dict] = []
    for record in workspace.requirements():
        if record["status"] in CLOSED_STATUSES:
            updated = _maybe_reopen(workspace, record, accepted, index, as_of, actor)
        else:
            updated = _maybe_satisfy(workspace, record, accepted, index, as_of, actor)
        if updated is not None:
            changed.append(updated)
    return changed


def _maybe_satisfy(
    workspace: Workspace, record: dict, accepted: list[dict], index: Index,
    as_of: date, actor: str,
) -> dict | None:
    for claim in accepted:
        ok, basis = meets_gap(record, claim, index, as_of)
        if not ok:
            continue
        record = dict(
            record, closure_basis="reviewed_evidence",
            satisfied_by_claim_id=claim["claim_id"],
            answered_by_source_id=claim["source_id"], reopen_to=record["status"],
        )
        record = _record_status(
            workspace, record, "satisfaction", actor,
            f"satisfied by accepted claim {claim['claim_id']}: {basis}",
        )
        workspace.log(actor, "requirement_satisfied", "collection_requirement",
                      record["req_id"], {"claim_id": claim["claim_id"], "basis": basis})
        return record
    return None


def _maybe_reopen(
    workspace: Workspace, record: dict, accepted: list[dict], index: Index,
    as_of: date, actor: str,
) -> dict | None:
    claim_id = record.get("satisfied_by_claim_id")
    if not claim_id:
        return None  # closed by something other than this rule; leave it alone
    satisfying = next((c for c in accepted if c["claim_id"] == claim_id), None)
    reason = None
    if satisfying is None:
        reason = f"the satisfying claim {claim_id} is no longer accepted"
    elif not _valid_at(satisfying, as_of):
        reason = (
            f"the satisfying claim {claim_id} expired: valid_to "
            f"{satisfying.get('valid_to')} is before the as-of date {as_of}"
        )
    else:
        later = _contradicting_successor(satisfying, accepted, index)
        if later is not None:
            reason = (
                f"a later accepted claim {later['claim_id']} contradicts {claim_id} on "
                f"({record['subject_id']}, {record['predicate']})"
            )
    if reason is None:
        return None
    record = dict(
        record, closure_basis=None, satisfied_by_claim_id=None, answered_by_source_id=None
    )
    record = _record_status(
        workspace, record, record.get("reopen_to") or "research", actor, f"reopened: {reason}"
    )
    workspace.log(actor, "requirement_reopened", "collection_requirement", record["req_id"],
                  {"reason": reason})
    return record


def _contradicting_successor(claim: dict, accepted: list[dict], index: Index) -> dict | None:
    stamp = claim.get("asserted_at") or claim["valid_from"]
    for other in accepted:
        if other["claim_id"] == claim["claim_id"]:
            continue
        if (other["subject_id"], other["predicate"]) != (claim["subject_id"], claim["predicate"]):
            continue
        other_stamp = other.get("asserted_at") or other["valid_from"]
        if other_stamp > stamp and index.claim_value(other) != index.claim_value(claim):
            return other
    return None
