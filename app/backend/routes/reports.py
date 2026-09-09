"""New reporting: ingest a document, list what was ingested, review a proposed claim."""
from __future__ import annotations

import base64
import binascii
import time

from fastapi import APIRouter, Depends, Query, Request

from ..adapter import DatasetAdapter
from ..contracts import (
    ClaimDecisionRequest,
    ClaimDecisionResponse,
    ChangeSetView,
    DecisionView,
    ReportDetailResponse,
    ReportIngestRequest,
    ReportIngestResponse,
    ReportsResponse,
)
from ..errors import UnknownId
from ..product import ingest as ingest_module
from ..product import review as review_module
from ..product.ingest import UnsupportedFormat
from ..product.store import Workspace
from ..views import (
    diff,
    instruction_span_views,
    planning_flag_views,
    proposed_claim_view,
    report_view,
    requirement_by_id,
)
from .common import BATCH_QUERY, WORKSPACE_QUERY, elapsed_ms, get_adapter, view

router = APIRouter()


async def _payload(request: Request, filename: str | None) -> tuple[bytes, str, str | None, str]:
    """(bytes, filename, content type, actor) from a JSON body or a raw upload."""
    content_type = request.headers.get("content-type", "")
    body = await request.body()
    if content_type.split(";")[0].strip() == "application/json":
        parsed = ReportIngestRequest.model_validate_json(body)
        if parsed.content_base64 is not None:
            try:
                payload = base64.b64decode(parsed.content_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise UnsupportedFormat(
                    f"content_base64 is not valid base64: {exc}", {"filename": parsed.filename}
                ) from exc
        elif parsed.text is not None:
            payload = parsed.text.encode("utf-8")
        else:
            raise UnsupportedFormat(
                "send the report as `text` (text, markdown, CSV) or `content_base64` (PDF).",
                {"filename": parsed.filename},
            )
        return payload, parsed.filename, parsed.content_type or content_type, parsed.actor
    if not filename:
        raise UnsupportedFormat(
            "a raw upload needs ?filename= so the parser can be chosen from its extension.",
            {"content_type": content_type},
        )
    return body, filename, content_type, request.headers.get("x-actor", "operator")


@router.post("/api/reports", response_model=ReportIngestResponse)
async def create_report(
    request: Request,
    filename: str | None = Query(None, description="required for a raw (non-JSON) upload"),
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ReportIngestResponse:
    started = time.perf_counter()
    payload, name, content_type, actor = await _payload(request, filename)
    adapter.check()
    store = Workspace(workspace)
    result = ingest_module.ingest(
        adapter, store, payload=payload, filename=name, content_type=content_type,
        actor=actor, batch=batch,
    )
    index = view(adapter, batch, workspace).index
    text = result["report"]["text"]
    return ReportIngestResponse(
        workspace=workspace,
        report=report_view(result["report"]),
        duplicate=result["duplicate"],
        extractor=result["extractor"],
        proposed_claims=[proposed_claim_view(index, c, text) for c in result["claims"]],
        instruction_like_spans=instruction_span_views(result["instruction_like_spans"]),
        response_ms=elapsed_ms(started),
    )


@router.get("/api/reports", response_model=ReportsResponse)
def reports(
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ReportsResponse:
    adapter.check()
    store = Workspace(workspace)
    return ReportsResponse(
        workspace=workspace, reports=[report_view(r) for r in store.reports()]
    )


@router.get("/api/reports/{report_id}", response_model=ReportDetailResponse)
def report(
    report_id: str,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ReportDetailResponse:
    store = Workspace(workspace)
    record = store.report(report_id)
    if record is None:
        raise UnknownId(
            f"no report {report_id!r} in workspace {workspace!r}.",
            {"report_id": report_id, "workspace": workspace},
        )
    index = view(adapter, batch, workspace).index
    claims = store.claims(report_id=report_id)
    return ReportDetailResponse(
        workspace=workspace,
        report=report_view(record),
        text=record["text"],
        proposed_claims=[proposed_claim_view(index, c, record["text"]) for c in claims],
    )


@router.post(
    "/api/claims/proposed/{claim_id}/decision", response_model=ClaimDecisionResponse
)
def decide_claim(
    claim_id: str,
    body: ClaimDecisionRequest,
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    adapter: DatasetAdapter = Depends(get_adapter),
) -> ClaimDecisionResponse:
    """Accept or reject one proposed claim, and answer with everything it changed."""
    started = time.perf_counter()
    adapter.check()
    store = Workspace(workspace)
    result = review_module.decide(
        adapter, store, batch=batch, claim_id=claim_id, decision=body.decision,
        actor=body.actor, reason=body.reason, revision=body.revision,
    )
    after = result["after"]
    return ClaimDecisionResponse(
        workspace=workspace,
        batch=batch,
        as_of=after.index.snapshot.as_of,
        graph_version=store.graph_version,
        claim=proposed_claim_view(
            after.index, result["claim"], store.report(result["claim"]["report_id"])["text"]
        ),
        decision=DecisionView(**result["decision"]),
        changes=ChangeSetView(**diff(result["before"].index, after.index)),
        contradicts=result["contradicts"],
        contradiction_reason=result.get("contradiction_reason"),
        chosen_claim_id=result["chosen_claim_id"],
        requirements_changed=[
            requirement_by_id(after.index, r["req_id"])
            for r in result["requirements_changed"]
        ],
        planning_flags=planning_flag_views(result["planning_flags"]),
        response_ms=elapsed_ms(started),
    )
