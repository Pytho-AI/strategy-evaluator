"""POST /api/reports: formats, exact spans, deduplication, and what the extractor may read."""
from __future__ import annotations

import ast
import builtins
import json
from pathlib import Path

import pytest
from conftest import DATASET_DIR, REPO_ROOT, hash_tree
from reports_fixture import AUTHORED, DORNE_360, TEXTS

from app.backend.product import extract as rules

INGEST_PACKAGE = REPO_ROOT / "app" / "backend" / "product"
FORBIDDEN = ("truth/claims.jsonl", "truth/facts.jsonl", "injects/batch_")


def ingest(client, workspace, text=DORNE_360, filename="dorne_360.md", batch=3, **body):
    return client.post(
        "/api/reports",
        params={"batch": batch, "workspace": workspace},
        json={"filename": filename, "actor": "analyst", "text": text, **body},
    )


def test_a_report_dated_after_the_fixture_yields_claims_with_exact_spans(client, workspace_id):
    response = ingest(client, workspace_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["extractor"] == "local_rules"
    assert body["report"]["report_date"] == "2026-11-20"
    assert body["duplicate"] is False

    detail = client.get(
        f"/api/reports/{body['report']['report_id']}", params={"workspace": workspace_id}
    ).json()
    text = detail["text"]
    assert text == DORNE_360
    for claim in body["proposed_claims"]:
        assert claim["span_text"] == text[claim["span_start"] : claim["span_end"]]
        assert claim["status"] == "proposed"

    range_claim = next(c for c in body["proposed_claims"] if c["predicate"] == "range_km")
    assert range_claim["subject_id"] == "sys_dorne_asm"
    assert range_claim["value"] == 360
    assert range_claim["unit"] == "km"
    assert range_claim["valid_from"] == "2026-11-18"  # the "as of" cue
    assert range_claim["asserted_at"] == "2026-11-20"  # the date-time group
    assert range_claim["estimative"] is False
    assert range_claim["likelihood_icd203"] is None
    assert range_claim["confidence_icd203"] == "moderate"
    assert range_claim["flags"] == []
    assert "360 km as of 18 November 2026" in range_claim["span_text"]


def test_a_relational_sentence_resolves_both_entities(client, workspace_id):
    body = ingest(client, workspace_id).json()
    relation = next(
        c for c in body["proposed_claims"] if c["predicate"] == "subordinate_to"
    )
    assert relation["subject_id"] == "unit_1st_dorne_battery"
    assert relation["object_id"] == "unit_var_coastal_msl_bde"
    assert relation["object_name"] == "7th Coastal Missile Brigade"
    assert relation["value_type"] == "entity"


def test_instruction_like_text_is_recorded_as_data_and_makes_no_claim(client, workspace_id):
    body = ingest(client, workspace_id).json()
    spans = body["instruction_like_spans"]
    assert len(spans) == 1
    assert "Ignore all previous instructions" in spans[0]["text"]
    assert DORNE_360[spans[0]["span_start"] : spans[0]["span_end"]] == spans[0]["text"]
    assert all(
        "assumption" not in (c["predicate"] or "") for c in body["proposed_claims"]
    )
    assert len(body["proposed_claims"]) == 2


def test_reingesting_the_same_bytes_returns_the_same_report_and_no_new_claims(
    client, workspace_id
):
    first = ingest(client, workspace_id).json()
    second = ingest(client, workspace_id).json()
    assert second["duplicate"] is True
    assert second["report"]["report_id"] == first["report"]["report_id"]
    assert second["report"]["sha256"] == first["report"]["sha256"]
    assert [c["claim_id"] for c in second["proposed_claims"]] == [
        c["claim_id"] for c in first["proposed_claims"]
    ]
    assert len(client.get("/api/reports", params={"workspace": workspace_id}).json()["reports"]) == 1


def test_an_unsupported_format_is_rejected_with_415(client, workspace_id):
    response = ingest(client, workspace_id, filename="report.docx")
    assert response.status_code == 415
    error = response.json()["error"]
    assert error["code"] == "unsupported_format"
    assert "docx" in error["message"]
    assert "pdf" in error["detail"]["supported"]


def test_a_pdf_is_parsed_through_pymupdf(client, workspace_id):
    import pymupdf

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((20, 60), "Date-time group: 201430Z NOV 26")
    page.insert_text(
        (20, 80),
        "The Dorne-3 has a maximum range of 360 km as of 18 November 2026.",
    )
    page.insert_text((20, 100), "Confidence is high.")
    payload = document.tobytes()
    document.close()

    response = client.post(
        "/api/reports",
        params={"batch": 3, "workspace": workspace_id, "filename": "brief.pdf"},
        content=payload,
        headers={"content-type": "application/pdf", "x-actor": "analyst"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["report"]["format"] == "pdf"
    assert any(c["predicate"] == "range_km" for c in body["proposed_claims"])


def test_a_csv_upload_is_accepted(client, workspace_id):
    csv = (
        "subject,statement\n"
        "kestrel,The Kestrel Strait sea lane carries 61 transits per day as of 20 November 2026.\n"
    )
    response = ingest(client, workspace_id, text=csv, filename="lane.csv")
    assert response.status_code == 200
    assert response.json()["report"]["format"] == "csv"
    assert any(
        c["predicate"] == "throughput_per_day" for c in response.json()["proposed_claims"]
    )


def test_an_unknown_report_id_is_404(client, workspace_id):
    response = client.get("/api/reports/rpt_9999", params={"workspace": workspace_id})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"


def test_a_configured_model_extractor_fails_loudly_instead_of_falling_back(
    client, workspace_id, monkeypatch
):
    monkeypatch.setenv("INGEST_MODEL", "some-model")
    response = ingest(client, workspace_id)
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "extractor_unavailable"
    assert "local_rules" in response.json()["error"]["message"]


# ---------------------------------------------------------------- what ingestion may read
def test_ingestion_never_opens_ground_truth_claims_facts_or_inject_manifests(
    client, workspace_id, monkeypatch
):
    """The dataset is already loaded when a report arrives; ingestion must add no reads of the
    answer key. Any open() of a forbidden path during the request fails the test."""
    client.get("/api/snapshot", params={"batch": 3})  # warm the batch the route reads
    opened: list[str] = []
    real_open, real_path_open = builtins.open, Path.open

    def guard(path: str) -> None:
        text = str(path)
        if any(part in text for part in FORBIDDEN):
            opened.append(text)
            raise AssertionError(f"ingestion opened a forbidden dataset path: {text}")

    def open_guard(file, *args, **kwargs):
        guard(file)
        return real_open(file, *args, **kwargs)

    def path_open_guard(self, *args, **kwargs):
        guard(self)
        return real_path_open(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", open_guard)
    monkeypatch.setattr(Path, "open", path_open_guard)
    response = ingest(client, workspace_id)
    assert response.status_code == 200
    assert opened == []


def test_the_ingestion_package_source_never_names_the_forbidden_files():
    """No code in app/backend/product names the answer key. Prose that says so is exempt:
    docstrings and comments are stripped before the check."""
    forbidden = ("claims.jsonl", "facts.jsonl", "manifest.json", "expected_effects")
    for path in sorted(INGEST_PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            )
        }
        literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value not in docstrings
        ]
        names = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
        for text in literals + names:
            for name in forbidden:
                assert name not in text, f"{path.name} names {name} in code"


def test_the_extractor_itself_reads_no_file_at_all(monkeypatch):
    """extract.extract() is a pure function: entities and vocabularies come in as arguments."""
    entities = [
        {"entity_id": "sys_dorne_asm", "entity_type": "system",
         "canonical_name": "Dorne-3 coastal anti-ship missile", "aliases": ["Dorne-3"]},
    ]

    def refuse(*args, **kwargs):
        raise AssertionError("the extractor opened a file")

    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    result = rules.extract(
        DORNE_360, entities,
        predicates={"range_km": ("number", "km", None, "")},
        icd203_terms={"likely": ["likely"]},
        source_id="psrc_0001",
    )
    assert [c["claim"]["value"] for c in result["claims"]] == [360]


# ---------------------------------------------------------------- measured accuracy
def test_measured_extraction_accuracy_on_the_authored_fixture_reports(client, workspace_id, capsys):
    """Precision/recall of proposed claims against what the fixtures were written to say.

    This is an extraction measurement on four hand-written reports; it is not a scoring-parity
    result and it is not a benchmark. The numbers are printed with -s.
    """
    entities = json.loads(
        json.dumps([  # a plain copy of the entities the route passes the extractor
            row for row in _entities()
        ])
    )
    predicates, terms = _vocab()
    true_positive = false_positive = false_negative = 0
    for name, text in TEXTS.items():
        result = rules.extract(
            text, entities, predicates=predicates, icd203_terms=terms, source_id="psrc_0001"
        )
        got = [
            (
                claim["claim"]["subject_id"],
                claim["claim"]["predicate"],
                claim["claim"].get("object_id") or claim["claim"]["value"],
            )
            for claim in result["claims"]
        ]
        want = AUTHORED[name]
        true_positive += len([g for g in got if g in want])
        false_positive += len([g for g in got if g not in want])
        false_negative += len([w for w in want if w not in got])
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    print(
        f"\nextraction on {len(TEXTS)} authored reports: "
        f"tp={true_positive} fp={false_positive} fn={false_negative} "
        f"precision={precision:.2f} recall={recall:.2f}"
    )
    # The numbers recorded in app/backend/README.md. They are a floor, not a target: raise
    # them here when the extractor improves, never lower them to make a change pass.
    assert (true_positive, false_positive, false_negative) == (9, 1, 2)
    assert precision == pytest.approx(0.9)
    assert recall == pytest.approx(9 / 11)


def _entities() -> list[dict]:
    from app.backend.adapter import DatasetAdapter

    return DatasetAdapter().snapshot(3).raw["entities"]


def _vocab() -> tuple[dict, dict]:
    from app.backend.product.ingest import _vocabulary

    return _vocabulary()


def test_the_dataset_is_untouched_by_a_full_ingest_and_review_pass(
    client, workspace_id, dataset_hashes_before
):
    before = hash_tree(DATASET_DIR)
    body = ingest(client, workspace_id).json()
    claim_id = body["proposed_claims"][0]["claim_id"]
    client.post(
        f"/api/claims/proposed/{claim_id}/decision",
        params={"batch": 3, "workspace": workspace_id},
        json={"decision": "accept", "actor": "reviewer", "reason": "corroborated"},
    )
    assert hash_tree(DATASET_DIR) == before
