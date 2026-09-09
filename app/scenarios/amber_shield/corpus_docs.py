"""The rendered AMBER SHIELD corpus: document metadata, hashes and span lookup.

UNCLASSIFIED - SYNTHETIC. The documents under `corpus/` are the authored artefacts; this module
is the index over them. Nothing here writes to disk: the files are checked in and are the source
of truth for `sources.text_sha256` and for every claim span, so a build cannot drift from the text
a reader sees. `app/tests/scenarios/test_corpus.py` re-derives both from the files.

Document types follow `dataset/schema/SCHEMA.md` §3 `DocType`. The four `guidance` products (the
operation order and the three products it descends from) are exempt from invariant 3's "every
document yields at least one claim" rule; every intelligence-bearing document below carries at
least one claim.
"""
from __future__ import annotations

import hashlib
from datetime import date
from functools import lru_cache
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"

#: (source_id, doc_type, filename, title, published_at, author_org, reliability, credibility)
#: Reliability A-F and credibility 1-6 are the Admiralty/NATO source-evaluation codes
#: (SCHEMA.md §3). They are properties of the source, not of the claim: the claim carries its own
#: ICD 203 likelihood and confidence.
DOCUMENTS: list[tuple[str, str, str, str, date, str, str, str]] = [
    ("src_opord_26_004", "guidance", "opord_26_004.md",
     "United States European Command operation order 26-004, Operation Amber Shield",
     date(2026, 9, 9), "the Commander, United States European Command", "A", "1"),
    ("src_gd_nds", "guidance", "guidance_nds.md",
     "National Defense Strategy, fictional extract",
     date(2026, 1, 2), "the Secretary of War", "A", "1"),
    ("src_gd_nms", "guidance", "guidance_nms.md",
     "National Military Strategy, fictional extract",
     date(2026, 1, 14), "the Chairman of the Joint Chiefs of Staff", "A", "1"),
    ("src_gd_oplan_bal", "guidance", "guidance_oplan_2026_bal.md",
     "Supreme Allied Commander Europe operation plan 2026 Baltic, fictional extract",
     date(2026, 2, 20), "the Supreme Allied Commander Europe", "A", "1"),

    ("src_as_consensus", "assessment", "assessment_alliance_consensus.md",
     "Alliance political consensus for the restoration of Estonian and Latvian territory",
     date(2026, 9, 7), "the United States European Command intelligence directorate", "A", "2"),
    ("src_mt_movement", "message_traffic", "message_traffic_movement_and_network.md",
     "Movement and network readiness, daily message traffic",
     date(2026, 9, 8), "the 21st Theater Sustainment Command movement control centre", "B", "2"),
    ("src_re_kalibr", "reference_entry", "reference_entry_kalibr.md",
     "Russian long-range strike systems bearing on the Baltic Region",
     date(2026, 9, 4), "the United States European Command intelligence directorate", "B", "2"),
    ("src_st_reception", "sitrep", "sitrep_reception_sustainment.md",
     "Reception and sustainment situation report",
     date(2026, 9, 9), "the 21st Theater Sustainment Command", "B", "3"),
    ("src_as_baltic", "assessment", "assessment_baltic_sea_lane.md",
     "Throughput of the Baltic sea line of communication under the mine and coastal-missile threat",
     date(2026, 9, 8), "the Combined Task Force Baltic intelligence cell", "C", "3"),
    ("src_st_iskander", "sitrep", "sitrep_iskander_dispersal.md",
     "Geospatial intelligence situation report, Kaliningrad Oblast",
     date(2026, 9, 9), "the theater geospatial intelligence cell", "A", "2"),
    ("src_st_grodno", "sitrep", "sitrep_grodno_staging.md",
     "Imagery intelligence situation report, Grodno area",
     date(2026, 9, 8), "the theater imagery intelligence cell", "B", "2"),
    ("src_st_rail", "sitrep", "sitrep_rail_loading_moscow.md",
     "Imagery intelligence situation report, Moscow military district",
     date(2026, 9, 9), "the theater imagery intelligence cell", "B", "2"),
    ("src_st_baltiysk", "sitrep", "sitrep_baltiysk_sortie.md",
     "Signals intelligence situation report, Baltiysk",
     date(2026, 9, 8), "the theater signals intelligence cell", "B", "2"),
    ("src_st_rezekne", "sitrep", "sitrep_rezekne_minefield.md",
     "Human intelligence situation report, eastern Latvia",
     date(2026, 9, 8), "the Latvian liaison detachment", "C", "3"),
    ("src_nw_cable", "news", "news_estlink_vessel.md",
     "Vessel loitering over the Estlink 2 cable route, Gulf of Finland",
     date(2026, 9, 8), "open-source shipping and coastguard reporting", "C", "4"),
]

BY_ID = {d[0]: d for d in DOCUMENTS}


@lru_cache(maxsize=None)
def text(source_id: str) -> str:
    """The rendered document text, exactly as a reader (and invariant 02) sees it."""
    return (CORPUS_DIR / BY_ID[source_id][2]).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def sha256(source_id: str) -> str:
    return hashlib.sha256(text(source_id).encode("utf-8")).hexdigest()


def span(source_id: str, snippet: str) -> tuple[int, int]:
    """Character offsets of `snippet` in the document. The snippet must occur exactly once, so a
    reworded document fails the build instead of silently repointing a claim at the wrong text."""
    body = text(source_id)
    n = body.count(snippet)
    if n != 1:
        raise ValueError(f"{source_id}: snippet occurs {n} times, expected once: {snippet[:60]!r}")
    start = body.index(snippet)
    return start, start + len(snippet)


def sources() -> list[dict]:
    """`sources` rows. `path` is relative to `build.ROOT` (the scenario package directory)."""
    return [dict(source_id=sid, doc_type=doc_type, title=title, published_at=published.isoformat(),
                 author_org=org, reliability=rel, credibility=cred, real_world=False,
                 public_reference=None, path=f"corpus/{filename}", batch=0,
                 text_sha256=sha256(sid), perturbations=[])
            for sid, doc_type, filename, title, published, org, rel, cred in DOCUMENTS]


#: guidance_id -> source_id, for the JSPS products that are rendered in the corpus.
GUIDANCE_SOURCE = {
    "gd_nds": "src_gd_nds",
    "gd_nms": "src_gd_nms",
    "gd_oplan_2026_bal": "src_gd_oplan_bal",
    "gd_opord_26_004": "src_opord_26_004",
}
