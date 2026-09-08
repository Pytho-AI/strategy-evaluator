"""Verify every quotation in doctrine/EXTRACTS.md appears verbatim in the cited PDF's text layer.
Figure-image extracts (marked '(figure image, transcribed)') are reported but not text-checked.
Run: cd dataset && python -m gen.check_extracts
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parent
ROOT = DATASET.parent
DOCS = {
    "JRAM": "CJCSM_3105_01C.pdf",
    "JP 5-0": "18-F-1152_JP_5-0.pdf",
    "JSPS": "CJCSI_3100_01F.pdf",
    "JP 2-01": "JP2_01.pdf",
    "JP 3-60": "JP_3-60.pdf",
}
_cache: dict[str, str] = {}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def doc_text(short: str) -> str:
    if short not in _cache:
        import pymupdf
        d = pymupdf.open(str(ROOT / "doctrine" / DOCS[short]))
        _cache[short] = norm("".join(p.get_text() for p in d))
    return _cache[short]


def parse(md: str):
    cur = None
    for line in md.split("\n"):
        m = re.match(r"^### (\S+) — (.+?) \[(JRAM|JP 5-0|JSPS|JP 2-01|JP 3-60)\] (.+)$", line)
        if m:
            cur = {"id": m.group(1), "doc": m.group(3), "figure": "figure image" in line, "quotes": []}
            yield_cur = cur
            yield cur
            continue
        if cur is not None and line.startswith("> "):
            cur["quotes"].append(line[2:].strip())


def main() -> int:
    md = (DATASET / "doctrine" / "EXTRACTS.md").read_text(encoding="utf-8")
    entries = list(parse(md))
    bad, n_checked, n_fig = [], 0, 0
    for e in entries:
        for q in e["quotes"]:
            words = len(q.split())
            if words > 40:
                bad.append(f"{e['id']}: {words} words (> 40)")
            if e["figure"]:
                n_fig += 1
                continue
            n_checked += 1
            if norm(q) not in doc_text(e["doc"]):
                bad.append(f"{e['id']} [{e['doc']}]: not found verbatim: {q[:70]!r}")
    print(f"{len(entries)} extracts, {n_checked} quotations text-checked, {n_fig} transcribed from figures")
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
