"""Build gen/styles/acronyms.yml from the Part I (abbreviations and acronyms) glossaries of the
five doctrine PDFs in ../doctrine/. Only acronyms that appear in those glossaries (plus the ICD 203
terms reproduced in JRAM) are permitted in rendered products (v2 §1A.4, invariant 20).

Run:  cd dataset && python -m gen.styles.build_acronyms
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # repo root
DOCTRINE = ROOT / "doctrine"
OUT = HERE / "acronyms.yml"

DOCS = {
    "JRAM": ("CJCSM_3105_01C.pdf", "PART I – ABBREVIATIONS AND ACRONYMS", "PART II – DEFINITIONS"),
    "JSPS": ("CJCSI_3100_01F.pdf", "ABBREVIATIONS AND ACRONYMS", None),
    "JP 5-0": ("18-F-1152_JP_5-0.pdf", "PART I—ABBREVIATIONS, ACRONYMS, AND INITIALISMS", "PART II—TERMS AND DEFINITIONS"),
    "JP 2-01": ("JP2_01.pdf", "PART I—ABBREVIATIONS AND ACRONYMS", "PART II—TERMS AND DEFINITIONS"),
    "JP 3-60": ("JP_3-60.pdf", "PART I—SHORTENED WORD FORMS", "PART II—TERMS AND DEFINITIONS"),
}

# ICD 203 (12 Jun 2023) terms reproduced in JRAM Fig. 19 / Encl. C §4; ICD 203 itself is not in hand.
ICD203_EXTRA = {
    "ICD": "Intelligence Community Directive",
    "IC": "Intelligence Community",
}

# Page-furniture lines that must never be parsed as acronyms.
FURNITURE = re.compile(r"^(UNCLASSIFIED|GL-\d+|Glossary|JP \d-\d+|CJCSM 3105\.01C|CJCSI 3100\.01F|\d+ \w+ \d{4}|=====PAGE \d+=====|Items marked.*|Unless otherwise.*|\(ABBREVIATIONS.*|\(?INTENTIONALLY BLANK\)?|Inner Back Cover|\(BACK COVER\))$")

ACRO = re.compile(r"^[A-Z][A-Za-z0-9&/()\-\.]{0,13}( [A-Z]{1,2})?\*?$")
LOWER_RUN = re.compile(r"[a-z]{3,}")
MIXED_OK = {"A-Space", "SecWar", "SecDef", "DoW", "DoDI", "DoD", "DoDD", "DoDM"}


def looks_like_acronym(tok: str) -> bool:
    tok = tok.strip()
    if not tok or FURNITURE.match(tok):
        return False
    if " " in tok and not re.match(r"^\S+ [A-Z]{1,2}$", tok):  # allow e.g. "GCP A"
        return False
    if not ACRO.match(tok):
        return False
    if tok.rstrip("*") in MIXED_OK:
        return True
    if LOWER_RUN.search(tok):  # e.g. "Risk-to-Force" is an expansion, not an acronym
        return False
    # single capital letters (JRAM: C, P), or >=2 capitals, or a digit (C2, J-5)
    caps = sum(1 for c in tok if c.isupper())
    return len(tok.rstrip("*")) == 1 or caps >= 2 or any(ch.isdigit() for ch in tok)


def page_text(pdf: Path) -> list[str]:
    import pymupdf  # PyMuPDF

    doc = pymupdf.open(str(pdf))
    lines: list[str] = []
    for i, p in enumerate(doc):
        lines.append(f"=====PAGE {i + 1}=====")
        lines.extend(p.get_text().split("\n"))
    return lines


def slice_glossary(lines: list[str], start_marker: str, end_marker: str | None) -> list[str]:
    # take the LAST occurrence of the start marker (the TOC also mentions it)
    starts = [i for i, l in enumerate(lines) if l.strip().startswith(start_marker)]
    if not starts:
        raise SystemExit(f"start marker not found: {start_marker}")
    s = starts[-1] + 1
    e = len(lines)
    if end_marker:
        ends = [i for i, l in enumerate(lines) if l.strip().startswith(end_marker) and i > s]
        if ends:
            e = ends[0]
    return lines[s:e]


def parse(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []

    def flush():
        nonlocal cur, buf
        if cur and buf:
            exp = " ".join(x.strip() for x in buf if x.strip())
            exp = re.sub(r"\s+", " ", exp).strip()
            out[cur.rstrip("*")] = exp
        cur, buf = None, []

    for raw in lines:
        l = raw.rstrip()
        if not l.strip():
            continue
        if FURNITURE.match(l.strip()):
            continue
        if looks_like_acronym(l) and not l.startswith(" "):
            flush()
            cur = l.strip()
        else:
            if cur is not None:
                buf.append(l)
    flush()
    return out


def main() -> int:
    merged: dict[str, dict] = {}
    for short, (fname, start, end) in DOCS.items():
        pdf = DOCTRINE / fname
        if not pdf.exists():
            print(f"missing {pdf}", file=sys.stderr)
            return 1
        lines = page_text(pdf)
        entries = parse(slice_glossary(lines, start, end))
        print(f"{short}: {len(entries)} acronyms")
        for k, v in entries.items():
            rec = merged.setdefault(k, {"expansion": v, "expansions": [], "sources": []})
            if v.lower() not in [x.lower() for x in rec["expansions"]]:
                rec["expansions"].append(v)
            if short not in rec["sources"]:
                rec["sources"].append(short)
    for k, v in ICD203_EXTRA.items():
        rec = merged.setdefault(k, {"expansion": v, "expansions": [v], "sources": []})
        if "ICD 203" not in rec["sources"]:
            rec["sources"].append("ICD 203")
    data = {
        "_about": "Acronyms permitted in rendered products. Extracted from the Part I glossaries of the five doctrine PDFs plus ICD 203 terms reproduced in JRAM Fig. 19. Regenerate with `python -m gen.styles.build_acronyms`.",
        "acronyms": dict(sorted(merged.items())),
    }
    OUT.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200))
    print(f"wrote {OUT} ({len(merged)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
