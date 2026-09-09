"""The corpus is real text, and every claim points into it.

Invariant 02 (spans lie inside their source and mention the subject or the value) is checked in
`test_schema.py` by the dataset's own validator. These tests cover what the invariant cannot: that
the checked-in files are the files the `sources` rows describe, and that the corpus is a plausible
intelligence picture rather than one document with everything in it.
"""
from __future__ import annotations

import hashlib

INTELLIGENCE_BEARING = {"reference_entry", "sitrep", "news", "message_traffic", "tabular", "assessment"}


def test_every_source_points_at_a_checked_in_file(computed, scenario_root):
    for s in computed["sources"]:
        path = scenario_root / s["path"]
        assert path.is_file(), s["path"]
        assert s["path"].startswith("corpus/")


def test_text_sha256_is_the_hash_of_the_rendered_text(computed, scenario_root):
    for s in computed["sources"]:
        text = (scenario_root / s["path"]).read_text(encoding="utf-8")
        assert s["text_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest(), s["source_id"]


def test_every_claim_span_reproduces_the_snippet_it_was_authored_from(computed, corpus, rows):
    """The span is derived by searching the document, so a reworded document must fail the build
    rather than silently repoint a claim. Here we walk the other way: the stored offsets must cut
    exactly the authored snippet out of the file."""
    spans = {c["claim_id"]: (c["source_id"], c["span_start"], c["span_end"]) for c in computed["claims"]}
    assert len(spans) == len(rows.CLAIM_SPECS)
    for spec in rows.CLAIM_SPECS:
        key, source_id, snippet = spec[0], spec[1], spec[2]
        src, start, end = spans[rows.claim_id(key)]
        assert src == source_id
        assert corpus.text(source_id)[start:end] == snippet, key


def test_the_corpus_is_a_mixed_picture_not_one_document(computed):
    by_type: dict[str, int] = {}
    for s in computed["sources"]:
        by_type[s["doc_type"]] = by_type.get(s["doc_type"], 0) + 1
    assert by_type["guidance"] == 4, "the operation order plus the three products it descends from"
    intel = sum(n for t, n in by_type.items() if t in INTELLIGENCE_BEARING)
    assert intel >= 10, by_type
    assert len(by_type) >= 5, f"only {sorted(by_type)} document types"


def test_source_reliability_and_credibility_are_graded_not_uniform(computed):
    intel = [s for s in computed["sources"] if s["doc_type"] in INTELLIGENCE_BEARING]
    assert {s["reliability"] for s in intel} >= {"A", "B", "C"}
    assert len({s["credibility"] for s in intel}) >= 3
    for s in computed["sources"]:
        assert s["reliability"] in set("ABCDEF")
        assert s["credibility"] in set("123456")


def test_likelihood_and_confidence_are_kept_as_separate_fields(computed):
    for c in computed["claims"]:
        assert c["confidence_icd203"] in {"low", "moderate", "high"}
        if c["estimative"]:
            assert c["likelihood_icd203"] is not None, c["claim_id"]
            assert c["likelihood_surface_term"], f"{c['claim_id']} has no surface term"
        else:
            assert c["likelihood_icd203"] is None, c["claim_id"]
    # both fields vary: the confidence is not a restatement of the likelihood
    estimative = [c for c in computed["claims"] if c["estimative"]]
    assert len({c["likelihood_icd203"] for c in estimative}) >= 3
    assert len({c["confidence_icd203"] for c in estimative}) == 3


def test_claims_are_bitemporal(computed, S):
    """Transaction time is when the document said it; valid time is the window the assertion
    covers. They are different columns and they carry different dates."""
    sources = {s["source_id"]: s for s in computed["sources"]}
    for c in computed["claims"]:
        assert c["asserted_at"] == sources[c["source_id"]]["published_at"], c["claim_id"]
        assert c["valid_from"] <= S.AS_OF.isoformat(), c["claim_id"]
        if c["valid_to"] is not None:
            assert c["valid_to"] > c["valid_from"], c["claim_id"]
    assert any(c["valid_from"] != c["asserted_at"] for c in computed["claims"])
    assert any(c["valid_to"] is not None for c in computed["claims"]), "no claim ever expires"


def test_the_rendered_guidance_products_are_wired_to_the_guidance_chain(computed):
    by_id = {g["guidance_id"]: g for g in computed["guidance"]}
    for gid in ("gd_nds", "gd_nms", "gd_oplan_2026_bal", "gd_opord_26_004"):
        assert by_id[gid]["source_id"], gid
    sources = {s["source_id"]: s for s in computed["sources"]}
    for g in computed["guidance"]:
        if g["source_id"]:
            assert sources[g["source_id"]]["doc_type"] == "guidance"


def test_the_ui_intelligence_screen_reports_are_in_the_corpus(computed, scenario_root):
    """The six reports the Intelligence screen lists are real documents with real claims."""
    text = "\n".join((scenario_root / s["path"]).read_text(encoding="utf-8") for s in computed["sources"])
    for phrase in ("Rail loading", "Moscow military district", "152nd Guards Missile Brigade",
                   "Chernyakhovsk", "Baltiysk", "Minefield emplacement", "Rezekne",
                   "Grodno staging area", "Estlink 2"):
        assert phrase in text, phrase
