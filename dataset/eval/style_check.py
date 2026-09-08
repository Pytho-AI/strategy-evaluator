"""Formatting guardrails (v2 §1A) as invariants 11-20 on any rendered text. Returns violations
with line numbers. Pure functions; no I/O except the convenience `check_file`.

Codes: 11 markings, 12 likelihood+confidence in one sentence, 13 mixed ICD/JRAM scales,
14 risk statement slot order, 15 COA statement assumptions, 16 invalid COA in comparison,
17 App. F caution, 20 acronyms (20a not permitted, 20b not spelled out at first use, 20c no
glossary), plus 1A.2 paragraph scheme (02), 1A.3 dates (03), 1A.5 synonyms (05), 1A.15 length (15L).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

CAVEAT = "SYNTHETIC DATA — FOR EXERCISE AND DEVELOPMENT USE ONLY. NOT A REAL ASSESSMENT."
MARK = "UNCLASSIFIED"

# Other marking / control strings that must never appear (case-insensitive where sensible).
MARKING_DENYLIST = re.compile(
    r"(TOP SECRET|\bSECRET\b|CONFIDENTIAL|NOFORN|\bFOUO\b|\bCUI\b|\bORCON\b|\bREL TO\b|\bSCI\b|\bSAP\b|//|\(TS\)|\(S\)|\(U\)|\(C\)\s*[A-Z]|CLASSIFIED BY|DECLASSIFY ON)",
)

ICD_TERMS = [
    "almost no chance", "remote chance", "very unlikely", "highly improbable", "roughly even chance", "roughly even odds",
    "very likely", "highly probable", "almost certainly", "almost certain", "nearly certain", "unlikely", "likely",
]
ICD_ONLY_MARKERS = re.compile(r"\b(almost no chance|remote chance|roughly even chance|roughly even odds|almost certain(?:ly)?|nearly certain|highly (?:im)?probable)\b", re.I)
ICD_ASSESS = re.compile(r"\b(assess(?:es|ed)?|judge(?:s|d)?|estimate(?:s|d)?)\b[^.]*\b(almost no chance|very unlikely|unlikely|roughly even chance|likely|very likely|almost certain(?:ly)?)\b", re.I)
LIKELIHOOD_ANY = re.compile(r"\b(almost no chance|remote chance|very unlikely|highly improbable|unlikely|improbable|roughly even chance|roughly even odds|likely|probable|very likely|highly probable|almost certain(?:ly)?|nearly certain)\b", re.I)
CONFIDENCE_TERM = re.compile(r"\b((low|moderate|high)[- ]confidence|confidence (?:is|level(?: is)?|of)?\s*(low|moderate|high))\b", re.I)
JRAM_MARKERS = re.compile(r'("(?:Very Unlikely|Unlikely|Likely|Very Likely)" probability|probability level|trending (?:up|down)|risk level|Military Strategic Risk|Risk-to-Mission|Risk-to-Force)')
HEDGE_SYNONYMS = re.compile(r"\b(probable|probably|improbable|improbably|may well|might|could|possibly|possible that|chances are)\b", re.I)
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
DTG = re.compile(r"\b\d{6}Z [A-Z]{3} \d{2}\b")
BULLET = re.compile(r"^\s*([•\-\*]|•)\s+")
CAUTION = "This numeric method is not the result of a rigorous mathematical analysis; comparing courses of action by criterion is more accurate than comparing total values."
ACRONYM_TOKEN = re.compile(r"(?<![\w/])([A-Z][A-Za-z0-9&/\-\.\(\)]*[A-Z0-9\)])(?![\w/])")
ROMAN = re.compile(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X)$")
DTG_MONTHS = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
UNIT_SYMBOLS = {"MW"}

INTEL_PRODUCTS = {"assessment", "reference_entry"}
RISK_PRODUCTS = {"risk_context", "assessment"}
DIRECTIVE_PRODUCTS = {"risk_context", "collection_plan", "coa_statement", "reference_entry", "guidance", "assessment"}
LENGTH_LIMITS = {"message_traffic": 120, "reference_entry": 400, "risk_context": 350}


@dataclass
class Violation:
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"L{self.line} [{self.code}] {self.message}"


def _lines(text: str) -> list[str]:
    return text.split("\n")


def _body_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Lines between the markings, excluding the acronym glossary section."""
    out = []
    in_gloss = False
    last = len(lines) - 1
    while last > 0 and not lines[last].strip():
        last -= 1
    for i, l in enumerate(lines):
        if i < 2 or i >= last:
            continue
        if l.strip().lower().startswith("acronyms used"):
            in_gloss = True
        if in_gloss:
            continue
        out.append((i + 1, l))
    return out


def sentences(line: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]


def check_markings(lines: list[str]) -> list[Violation]:
    v = []
    if not lines or lines[0].strip() != MARK:
        v.append(Violation(1, "11", "first line must be UNCLASSIFIED"))
    if len(lines) < 2 or lines[1].strip() != CAVEAT:
        v.append(Violation(2, "11", "second line must be the synthetic caveat"))
    last = len(lines) - 1
    while last > 0 and not lines[last].strip():
        last -= 1
    if lines[last].strip() != MARK:
        v.append(Violation(last + 1, "11", "last line must be UNCLASSIFIED"))
    for i, l in enumerate(lines):
        if i in (0, 1, last):
            continue
        if MARKING_DENYLIST.search(l):
            v.append(Violation(i + 1, "11", f"marking/control string present: {MARKING_DENYLIST.search(l).group(0)!r}"))
        if MARK in l:
            v.append(Violation(i + 1, "11", "UNCLASSIFIED may appear only on the first and last line"))
    return v


def check_likelihood_confidence(body: list[tuple[int, str]]) -> list[Violation]:
    v = []
    for n, l in body:
        for s in sentences(l):
            if LIKELIHOOD_ANY.search(s) and CONFIDENCE_TERM.search(s):
                v.append(Violation(n, "12", f"likelihood and confidence in one sentence: {s.strip()[:90]!r}"))
    return v


def check_mixed_scale(body: list[tuple[int, str]]) -> list[Violation]:
    text = "\n".join(l for _, l in body)
    icd = bool(ICD_ONLY_MARKERS.search(text) or ICD_ASSESS.search(text))
    jram = bool(JRAM_MARKERS.search(text))
    if icd and jram:
        n = next((n for n, l in body if ICD_ONLY_MARKERS.search(l) or ICD_ASSESS.search(l)), body[0][0] if body else 1)
        return [Violation(n, "13", "product mixes ICD 203 likelihood vocabulary with JRAM probability/risk vocabulary")]
    return []


def check_synonyms(body: list[tuple[int, str]], doc_type: str) -> list[Violation]:
    if doc_type not in INTEL_PRODUCTS:
        return []
    v = []
    for n, l in body:
        m = HEDGE_SYNONYMS.search(l)
        if m:
            v.append(Violation(n, "05", f"non-ICD likelihood synonym {m.group(0)!r}"))
    return v


def check_risk_statements(body: list[tuple[int, str]]) -> list[Violation]:
    from eval.jram import RISK_STATEMENT_RE, OPPORTUNITY_STATEMENT_RE

    v = []
    for n, l in body:
        s = l.strip()
        if s.startswith('There is a "'):
            if not (RISK_STATEMENT_RE.match(s) or OPPORTUNITY_STATEMENT_RE.match(s)):
                v.append(Violation(n, "14", "risk/opportunity statement does not follow the Fig. 11/12 slot order"))
            elif len(s.split()) > 90 and RISK_STATEMENT_RE.match(s):
                v.append(Violation(n, "15L", f"risk statement has {len(s.split())} words (> 90)"))
    return v


def check_dates(body: list[tuple[int, str]], doc_type: str) -> list[Violation]:
    v = []
    if doc_type == "tabular":
        return v
    for n, l in body:
        if ISO_DATE.search(l):
            v.append(Violation(n, "03", "ISO date in prose; use DD Month YYYY (DTG for message traffic)"))
    if doc_type in {"message_traffic", "sitrep"} and not any(DTG.search(l) for _, l in body):
        v.append(Violation(3, "03", "message traffic / situation report lacks a DDHHMMZ MON YY date-time group"))
    return v


def check_paragraph_scheme(body: list[tuple[int, str]], doc_type: str) -> list[Violation]:
    if doc_type not in DIRECTIVE_PRODUCTS:
        return []
    return [Violation(n, "02", "bullet character in a directive-style product") for n, l in body if BULLET.match(l)]


def check_length(body: list[tuple[int, str]], doc_type: str) -> list[Violation]:
    lim = LENGTH_LIMITS.get(doc_type)
    if lim is None:
        return []
    words = sum(len(l.split()) for _, l in body)
    return [Violation(3, "15L", f"{doc_type} has {words} words (> {lim})")] if words > lim else []


def check_acronyms(lines: list[str], body: list[tuple[int, str]], acronyms: dict[str, list[str]]) -> list[Violation]:
    v = []
    text_before: list[str] = []
    seen: dict[str, int] = {}
    for n, l in body:
        for m in ACRONYM_TOKEN.finditer(l):
            tok = m.group(1)
            if tok.endswith(")") and "(" not in tok:
                tok = tok[:-1]
            core = tok[:-1] if tok.endswith("s") and tok[:-1] in acronyms else tok
            if ROMAN.match(core) or core.isdigit() or core in UNIT_SYMBOLS or (core in DTG_MONTHS and DTG.search(l)):
                continue
            if re.search(r"[a-z]{3,}", core) and core not in acronyms:
                continue
            caps = sum(1 for c in core if c.isupper())
            if caps < 2 and core not in acronyms:
                continue
            if core not in acronyms:
                v.append(Violation(n, "20a", f"acronym not in the doctrine glossaries: {core!r}"))
                continue
            if core not in seen:
                seen[core] = n
                prior = "\n".join(text_before + [l[: m.start()]])
                exps = acronyms[core] if isinstance(acronyms[core], list) else [acronyms[core]]
                if not any(e.lower() in prior.lower() for e in exps):
                    v.append(Violation(n, "20b", f"{core!r} used before being spelled out ({exps[0]!r})"))
        text_before.append(l)
    if seen:
        gl = [i for i, l in enumerate(lines) if l.strip().lower().startswith("acronyms used")]
        if not gl:
            v.append(Violation(len(lines), "20c", "product uses acronyms but ends without an 'Acronyms used' glossary"))
        else:
            tail = "\n".join(lines[gl[0]:])
            missing = [a for a in seen if not re.search(rf"(?<![\w/]){re.escape(a)}(?![\w/])", tail)]
            if missing:
                v.append(Violation(gl[0] + 1, "20c", f"glossary lacks: {missing}"))
    return v


def check_comparison(lines: list[str], invalid_names: Iterable[str] = ()) -> list[Violation]:
    v = []
    hdr = [i for i, l in enumerate(lines) if re.search(r"\|\s*Criterion\s*\|\s*Weight\s*\|", l)]
    for i in hdr:
        tail = "\n".join(lines[i:])
        if CAUTION not in tail:
            v.append(Violation(i + 1, "17", "comparison table not followed by the App. F caution sentence"))
        block_end = next((j for j in range(i + 1, len(lines)) if not lines[j].strip().startswith("|")), len(lines))
        block = "\n".join(lines[i:block_end])
        for name in invalid_names:
            if name in block:
                v.append(Violation(i + 1, "16", f"invalid COA {name!r} present in comparison table"))
    return v


def check_coa_statement(text: str, assumption_ids: Iterable[str]) -> list[Violation]:
    return [Violation(1, "15", f"COA statement does not list assumption {a}") for a in assumption_ids if a not in text]


def check_text(text: str, doc_type: str, acronyms: dict[str, list[str]], invalid_names: Iterable[str] = (),
               assumption_ids: Iterable[str] = ()) -> list[Violation]:
    lines = _lines(text)
    body = _body_lines(lines)
    v: list[Violation] = []
    v += check_markings(lines)
    v += check_likelihood_confidence(body)
    v += check_mixed_scale(body)
    v += check_synonyms(body, doc_type)
    v += check_risk_statements(body)
    v += check_dates(body, doc_type)
    v += check_paragraph_scheme(body, doc_type)
    v += check_length(body, doc_type)
    v += check_acronyms(lines, body, acronyms)
    v += check_comparison(lines, invalid_names)
    if doc_type == "coa_statement":
        v += check_coa_statement(text, assumption_ids)
    return sorted(v, key=lambda x: (x.line, x.code))


def load_acronyms(path: Optional[Path] = None) -> dict[str, list[str]]:
    """acronym -> list of accepted expansions (one per source glossary that defines it)."""
    import yaml

    p = path or Path(__file__).resolve().parents[1] / "gen" / "styles" / "acronyms.yml"
    data = yaml.safe_load(p.read_text())["acronyms"]
    return {k: list(v.get("expansions") or [v["expansion"]]) for k, v in data.items()}


def check_file(path: Path, doc_type: str, acronyms: Optional[dict[str, list[str]]] = None, **kw) -> list[Violation]:
    return check_text(Path(path).read_text(encoding="utf-8"), doc_type, acronyms or load_acronyms(), **kw)


def check_corpus(dataset_dir: Path, sources: list[dict], acronyms: Optional[dict[str, list[str]]] = None,
                 invalid_names: Iterable[str] = (), assumption_ids_by_source: Optional[dict[str, list[str]]] = None) -> dict[str, list[Violation]]:
    acr = acronyms or load_acronyms()
    out = {}
    for s in sources:
        p = Path(dataset_dir) / s["path"]
        out[s["source_id"]] = check_file(p, s["doc_type"], acr, invalid_names=invalid_names,
                                         assumption_ids=(assumption_ids_by_source or {}).get(s["source_id"], []))
    return out
