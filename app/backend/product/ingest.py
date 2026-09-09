"""Report ingestion: decode a supported format, store the original and its hash, and run the
local rules extractor.

The offline path imports no model SDK and needs no credentials. ``INGEST_MODEL`` selects a
model-backed extractor that this build does not implement; it fails loudly rather than
falling back to the rules extractor under a different name.
"""
from __future__ import annotations

import hashlib
import os

from ..adapter import DatasetAdapter
from ..errors import DatasetError
from . import extract as rules
from .store import Workspace

LOCAL_EXTRACTOR = "local_rules"

# extension -> the format name stored on the report
FORMATS: dict[str, str] = {
    ".txt": "text", ".text": "text", ".md": "markdown", ".markdown": "markdown",
    ".csv": "csv", ".pdf": "pdf",
}
CONTENT_TYPES: dict[str, str] = {
    "text/plain": "text", "text/markdown": "markdown", "text/csv": "csv",
    "application/csv": "csv", "application/pdf": "pdf",
}


class UnsupportedFormat(DatasetError):
    code = "unsupported_format"
    http_status = 415


class ExtractorUnavailable(DatasetError):
    code = "extractor_unavailable"
    http_status = 501


def resolve_format(filename: str, content_type: str | None) -> str:
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    fmt = FORMATS.get(suffix) or CONTENT_TYPES.get((content_type or "").split(";")[0].strip())
    if fmt is None:
        raise UnsupportedFormat(
            f"unsupported report format for {filename!r} "
            f"(content type {content_type or 'none'}). "
            f"Supported: {', '.join(sorted(set(FORMATS.values())))} "
            f"— file extensions {', '.join(sorted(FORMATS))}.",
            {"filename": filename, "content_type": content_type,
             "supported": sorted(set(FORMATS.values()))},
        )
    return fmt


def decode(payload: bytes, fmt: str) -> str:
    """The report's text. PDFs go through pymupdf; everything else is UTF-8 text."""
    if fmt == "pdf":
        import pymupdf  # local import: only the PDF path needs it

        with pymupdf.open(stream=payload, filetype="pdf") as document:
            return "\n".join(page.get_text() for page in document)
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedFormat(
            f"the uploaded {fmt} report is not valid UTF-8 text: {exc}",
            {"format": fmt},
        ) from exc


def extractor_name() -> str:
    configured = os.environ.get("INGEST_MODEL")
    if configured:
        raise ExtractorUnavailable(
            f"INGEST_MODEL={configured!r} selects a model-backed extractor, which this build "
            "does not implement. Unset INGEST_MODEL to use the offline "
            f"{LOCAL_EXTRACTOR!r} extractor.",
            {"ingest_model": configured},
        )
    return LOCAL_EXTRACTOR


def ingest(
    adapter: DatasetAdapter,
    workspace: Workspace,
    *,
    payload: bytes,
    filename: str,
    content_type: str | None,
    actor: str,
    batch: int,
) -> dict:
    """Store the report and its proposed claims. Re-ingesting the same bytes is a no-op."""
    name = extractor_name()
    fmt = resolve_format(filename, content_type)
    digest = hashlib.sha256(payload).hexdigest()

    existing = workspace.report_by_sha(digest)
    if existing is not None:
        workspace.log(actor, "report_reingested", "report", existing["report_id"],
                      {"sha256": digest, "filename": filename})
        return {
            "report": existing, "duplicate": True,
            "claims": workspace.claims(report_id=existing["report_id"]),
            "instruction_like_spans": [], "extractor": name,
        }

    text = decode(payload, fmt)
    predicates, terms = _vocabulary()
    entities = adapter.snapshot(batch).raw["entities"]
    stated = rules.report_date(text)
    report = workspace.add_report(
        sha256=digest, filename=filename, fmt=fmt, text=text, actor=actor,
        report_date=stated, extractor=name,
    )
    result = rules.extract(
        text, entities, predicates=predicates, icd203_terms=terms,
        source_id=report["source_id"], stated_date=stated,
    )
    claims = workspace.add_claims(report["report_id"], result["claims"])
    workspace.log(actor, "report_ingested", "report", report["report_id"], {
        "sha256": digest, "format": fmt, "extractor": name,
        "proposed_claims": [c["claim_id"] for c in claims],
        "instruction_like_sentences": len(result["instruction_like_spans"]),
    })
    return {
        "report": report, "duplicate": False, "claims": claims,
        "instruction_like_spans": result["instruction_like_spans"], "extractor": name,
    }


def _vocabulary() -> tuple[dict, dict]:
    """The controlled vocabularies: static scenario definitions, never ground truth."""
    import importlib
    import sys

    from dataset.loader import DATASET_DIR

    package_dir = str(DATASET_DIR)
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)
    vocab = importlib.import_module("gen.vocab")
    return vocab.PREDICATES, vocab.ICD203_TERMS
