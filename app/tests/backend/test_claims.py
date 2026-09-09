"""GET /api/claims: provenance, filters, flags and the trace an operator follows."""
from __future__ import annotations

import json

import pytest
from support import DATASET_DIR

# One T0 claim, one inject claim, one proposed inject claim.
PROVENANCE_CLAIMS = ("clm_0001", "clm_0844", "clm_0862")
CLAIM_FIELDS = (
    "subject_id", "predicate", "object_id", "value", "value_type", "unit",
    "valid_from", "valid_to", "asserted_at", "estimative", "likelihood_icd203",
    "likelihood_surface_term", "confidence_icd203", "confidence", "status",
    "supersedes_claim_id", "truth_claim_id", "span_start", "span_end", "source_id",
)
SOURCE_FIELDS = (
    "title", "path", "doc_type", "author_org", "reliability", "credibility",
    "published_at", "batch",
)


def _truth(name: str, key: str) -> dict[str, dict]:
    rows = [
        json.loads(line)
        for line in (DATASET_DIR / "truth" / f"{name}.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    return {row[key]: row for row in rows}


@pytest.fixture(scope="module")
def truth_claims() -> dict[str, dict]:
    return _truth("claims", "claim_id")


@pytest.fixture(scope="module")
def truth_sources() -> dict[str, dict]:
    return _truth("sources", "source_id")


@pytest.mark.parametrize("claim_id", PROVENANCE_CLAIMS)
def test_provenance_matches_the_truth_files_field_by_field(
    client, truth_claims, truth_sources, claim_id
):
    body = client.get(f"/api/claims/{claim_id}", params={"batch": 3}).json()
    claim = body["claim"]
    expected = truth_claims[claim_id]
    for field in CLAIM_FIELDS:
        assert claim[field] == expected.get(field), field
    source = truth_sources[expected["source_id"]]
    for field in SOURCE_FIELDS:
        assert claim["source"][field] == source[field], field
    assert claim["source"]["source_id"] == expected["source_id"]


@pytest.mark.parametrize("claim_id", PROVENANCE_CLAIMS)
def test_the_span_is_the_exact_slice_of_the_source_document(
    client, truth_claims, truth_sources, claim_id
):
    expected = truth_claims[claim_id]
    path = DATASET_DIR / truth_sources[expected["source_id"]]["path"]
    excerpt = path.read_text(encoding="utf-8")[
        expected["span_start"] : expected["span_end"]
    ]
    claim = client.get(f"/api/claims/{claim_id}", params={"batch": 3}).json()["claim"]
    assert claim["span_text"] == excerpt
    assert len(excerpt) == claim["span_end"] - claim["span_start"]


def test_likelihood_and_confidence_stay_distinct(client):
    claim = client.get("/api/claims/clm_0856", params={"batch": 3}).json()["claim"]
    assert claim["likelihood_icd203"] == "roughly_even_chance"
    assert claim["confidence_icd203"] in {"low", "moderate", "high"}
    assert 0.0 <= claim["confidence"] <= 1.0
    assert "not a probability that the claim is true" in claim["confidence_basis"]


def test_the_batch_3_contradiction_is_flagged_on_both_sides(client):
    proposed = client.get("/api/claims/clm_0862", params={"batch": 3}).json()["claim"]
    assert proposed["status"] == "proposed"
    assert proposed["source"]["reliability"] == "D"
    assert proposed["flags"]["contradiction"] is True
    assert proposed["flags"]["contradicts_claim_ids"]
    for approved_id in proposed["flags"]["contradicts_claim_ids"]:
        approved = client.get(f"/api/claims/{approved_id}", params={"batch": 3}).json()
        assert approved["claim"]["status"] == "approved", "an approved claim is not replaced"
        assert approved["claim"]["flags"]["contradiction"] is True


def test_the_contradiction_does_not_exist_before_its_batch(client):
    assert client.get("/api/claims/clm_0862", params={"batch": 2}).status_code == 404
    claim = client.get("/api/claims/clm_0741", params={"batch": 2}).json()["claim"]
    assert claim["flags"]["contradiction"] is False


def test_superseded_and_stale_claims_are_marked(client):
    superseded = client.get("/api/claims/clm_0003", params={"batch": 1}).json()["claim"]
    assert superseded["flags"]["superseded"] is True
    assert superseded["flags"]["superseded_by_claim_id"] == "clm_0844"
    stale = client.get("/api/claims/clm_0812", params={"batch": 0}).json()["claim"]
    assert stale["valid_to"] < "2026-09-08"
    assert stale["flags"]["stale"] is True


def test_a_superseded_claim_is_shown_as_superseded_in_its_trace(client):
    trace = client.get("/api/claims/clm_0003", params={"batch": 1}).json()["trace"]
    assert trace["claim_node"]["status"] == "superseded"
    assert trace["claim_node"]["id"] == "clm_0003"
    live = client.get("/api/claims/clm_0844", params={"batch": 1}).json()["trace"]
    assert live["claim_node"]["status"] == "approved"


@pytest.mark.parametrize(
    "batch,claim_id,assumption_id,strategy_id",
    (
        (1, "clm_0844", "asm_blue_1_k0", "str_blue_1"),
        (2, "clm_0850", "asm_blue_1_k2", "str_blue_1"),
        (3, "clm_0856", "asm_blue_2_k4", "str_blue_2"),
    ),
)
def test_inject_evidence_traces_to_the_assumption_and_option_it_moves(
    client, batch, claim_id, assumption_id, strategy_id
):
    """Current evidence is selected by (subject, predicate) at as_of, not by a frozen edge."""
    body = client.get(f"/api/claims/{claim_id}", params={"batch": batch}).json()
    trace = body["trace"]
    path = next(
        p
        for p in trace["paths"]
        if [n["id"] for n in p["nodes"][2:]] == [assumption_id, strategy_id]
    )
    assert [n["type"] for n in path["nodes"]] == [
        "source", "claim", "assumption", "strategy",
    ]
    assert path["nodes"][0]["id"] == body["claim"]["source_id"]
    assert [e["basis"] for e in path["edges"]] == ["current_evidence", "dependency_edge"]
    assert [e["kind"] for e in path["edges"]] == ["grounds", "requires"]
    assert all(e["mechanism"] for e in path["edges"])


def test_a_driver_claim_traces_to_the_harmful_event_and_its_cascade(client):
    trace = client.get("/api/claims/clm_0856", params={"batch": 3}).json()["trace"]
    drives = [e for e in trace["edges"] if e["kind"] == "drives"]
    assert {e["to_id"] for e in drives} == {"he_05", "he_06"}
    assert all(e["basis"] == "current_evidence" for e in drives)
    assert any("P_raw" in e["mechanism"] for e in drives)
    assert any(
        [n["id"] for n in p["nodes"][2:]] == ["he_05", "he_04"] for p in trace["paths"]
    )


@pytest.mark.parametrize(
    "params,check",
    (
        ({"entity": "ent_varenia"}, lambda c: "ent_varenia" in (c["subject_id"], c["object_id"])),
        ({"source": "src_0091"}, lambda c: c["source_id"] == "src_0091"),
        ({"status": "proposed"}, lambda c: c["status"] == "proposed"),
        ({"min_confidence": 0.9}, lambda c: c["confidence"] >= 0.9),
    ),
)
def test_filters_return_only_matching_rows(client, params, check):
    body = client.get("/api/claims", params={"batch": 3, "limit": 1000, **params}).json()
    assert body["claims"], f"no rows for {params}"
    assert all(check(c) for c in body["claims"])
    assert body["total"] == len(body["claims"])


def test_the_relationship_filter_selects_claims_in_that_edge_kind(client, adapter):
    index = adapter.index(3)
    expected = {
        node
        for edge in index.rows("dependencies")
        if edge["kind"] == "grounds"
        for node, node_type in (
            (edge["from_id"], edge["from_type"]),
            (edge["to_id"], edge["to_type"]),
        )
        if node_type == "claim"
    }
    body = client.get(
        "/api/claims", params={"batch": 3, "limit": 1000, "relationship": "grounds"}
    ).json()
    assert {c["claim_id"] for c in body["claims"]} == expected


def test_the_assumption_and_harmful_event_filters_narrow_to_that_node(client):
    grounding = client.get(
        "/api/claims", params={"batch": 3, "assumption": "asm_blue_1_k0"}
    ).json()
    assert [c["claim_id"] for c in grounding["claims"]] == ["clm_0831"]
    driving = client.get(
        "/api/claims", params={"batch": 3, "harmful_event": "he_05", "limit": 1000}
    ).json()
    assert driving["claims"] and driving["total"] < 864


def test_pagination_walks_the_filtered_rows_without_gaps(client):
    everything = client.get("/api/claims", params={"batch": 0, "limit": 1000}).json()
    assert everything["total"] == len(everything["claims"])
    first = client.get("/api/claims", params={"batch": 0, "limit": 10}).json()
    second = client.get(
        "/api/claims", params={"batch": 0, "limit": 10, "offset": 10}
    ).json()
    assert first["total"] == second["total"] == everything["total"]
    assert [c["claim_id"] for c in first["claims"]] == [
        c["claim_id"] for c in everything["claims"][:10]
    ]
    assert [c["claim_id"] for c in second["claims"]] == [
        c["claim_id"] for c in everything["claims"][10:20]
    ]
    beyond = client.get("/api/claims", params={"batch": 0, "offset": 10_000}).json()
    assert beyond["claims"] == [] and beyond["total"] == everything["total"]


def test_the_claim_count_grows_with_each_batch(client):
    counts = [
        client.get("/api/claims", params={"batch": b, "limit": 1}).json()["total"]
        for b in (0, 1, 2, 3)
    ]
    assert counts == sorted(counts) and counts[0] < counts[-1]


def test_an_unknown_claim_id_is_a_404(client):
    response = client.get("/api/claims/clm_9999", params={"batch": 3})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unknown_id"
