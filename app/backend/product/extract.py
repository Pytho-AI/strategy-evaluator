"""The local rules extractor: report text in, proposed claims with exact spans out.

Pure functions. This module opens no file, imports nothing from ``dataset/truth`` and needs
no credentials or network. Its only scenario input is the ``entities`` table and the
controlled vocabularies in ``gen/vocab.py`` (predicates, ICD 203 terms, posture states),
which the caller passes in.

Nothing is invented. A field the text does not state is left ``None`` and named in
``flags`` for the reviewer; instruction-like sentences are recorded as data and never
produce a claim.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable

NM_TO_KM = 1.852

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}
MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

DTG = re.compile(r"\b(\d{2})(\d{2})(\d{2})Z\s+([A-Za-z]{3})\s+(\d{2})\b")
LONG_DATE = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\b", re.IGNORECASE
)
AS_OF = re.compile(r"\bas of\s+(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\b", re.IGNORECASE)
VALID_UNTIL = re.compile(
    r"\bvalid (?:until|through)\s+(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\b",
    re.IGNORECASE,
)
CONFIDENCE = re.compile(
    r"\bconfidence(?:\s+in\s+this\s+judgment)?\s+is\s+(low|moderate|high)\b", re.IGNORECASE
)
INSTRUCTION_LIKE = re.compile(
    r"\b(ignore (?:all |any )?(?:previous|prior|above) instructions"
    r"|disregard (?:the above|previous|all prior)"
    r"|you (?:must|should) (?:now )?(?:accept|approve|mark|set|treat)"
    r"|mark (?:every|all) (?:assumption|claim)"
    r"|set (?:every|all) (?:assumption|claim)"
    r"|system\s*:|as an ai\b)",
    re.IGNORECASE,
)

# Sentence boundary: a run of characters on one line ending at . ! ? or the line end.
SENTENCE = re.compile(r".+?[.!?](?=\s|$)|.+", re.MULTILINE)


def sentences(text: str) -> list[tuple[int, int]]:
    """[start, end) of every sentence, in document order. Offsets index ``text`` exactly."""
    out: list[tuple[int, int]] = []
    for line in re.finditer(r"[^\n]+", text):
        base = line.start()
        for match in SENTENCE.finditer(line.group()):
            fragment = match.group()
            if not fragment.strip():
                continue
            lead = len(fragment) - len(fragment.lstrip())
            trail = len(fragment) - len(fragment.rstrip())
            out.append((base + match.start() + lead, base + match.end() - trail))
    return out


# ---------------------------------------------------------------- entity resolution
def alias_index(entities: Iterable[dict]) -> dict[str, list[str]]:
    """lower-cased surface form -> the entity ids that use it (canonical name and aliases)."""
    index: dict[str, list[str]] = {}
    for entity in entities:
        surfaces = [entity["canonical_name"], *(entity.get("aliases") or [])]
        for surface in surfaces:
            if not surface:
                continue
            index.setdefault(surface.strip().lower(), []).append(entity["entity_id"])
    return {surface: sorted(set(ids)) for surface, ids in index.items()}


def entity_mentions(sentence: str, index: dict[str, list[str]], types: dict[str, str]) -> list[dict]:
    """Longest-match, case-insensitive entity mentions, left to right, non-overlapping."""
    lower = sentence.lower()
    found: list[dict] = []
    for surface in sorted(index, key=len, reverse=True):
        start = 0
        while True:
            at = lower.find(surface, start)
            if at < 0:
                break
            start = at + 1
            if at and (lower[at - 1].isalnum() or lower[at - 1] in "-_"):
                continue
            end = at + len(surface)
            if end < len(lower) and (lower[end].isalnum() or lower[end] in "-_"):
                continue
            if any(at < m["end"] and end > m["start"] for m in found):
                continue
            ids = index[surface]
            found.append(
                {
                    "start": at, "end": end, "surface": sentence[at:end], "entity_ids": ids,
                    # A reporting role ('the theater J-2') is the author of a sentence, not
                    # its subject, so it is never chosen as one while another mention exists.
                    "reporting_role": all(types.get(i) == "organization_role" for i in ids),
                }
            )
    return sorted(found, key=lambda m: m["start"])


# ---------------------------------------------------------------- predicate matchers
def _number(raw: str) -> float:
    value = float(raw.replace(",", ""))
    return int(value) if value.is_integer() else value


def _km(match: re.Match) -> tuple[Any, list[str], str | None]:
    value, unit = _number(match.group(1)), match.group(2).lower()
    if unit in ("nautical miles", "nautical mile", "nm"):
        converted = round(value * NM_TO_KM, 3)
        return converted, [], (
            f"converted {value} nautical miles to {converted} km at 1 nm = {NM_TO_KM} km"
        )
    return value, [], None


def _percent(match: re.Match) -> tuple[Any, list[str], str | None]:
    return round(_number(match.group(1)) / 100.0, 6), [], (
        f"read {match.group(1)} percent as the fraction "
        f"{round(_number(match.group(1)) / 100.0, 6)}"
    )


def _plain(match: re.Match) -> tuple[Any, list[str], str | None]:
    return _number(match.group(1)), [], None


def _word(match: re.Match) -> tuple[Any, list[str], str | None]:
    return match.group(1).lower().replace(" ", "_"), [], None


def _true(match: re.Match) -> tuple[Any, list[str], str | None]:
    return True, [], None


def _false(match: re.Match) -> tuple[Any, list[str], str | None]:
    return False, [], None


def _aligned(match: re.Match) -> tuple[Any, list[str], str | None]:
    side = match.group(1).lower()
    return ("blue_aligned" if side == "blue" else "red_aligned"), [], None


NUMBER = r"(\d[\d,]*(?:\.\d+)?)"

# (predicate, pattern, reader, a word the sentence must also contain or None)
MATCHERS: list[tuple[str, re.Pattern, Any, str | None]] = [
    ("range_km", re.compile(
        r"\b(?:maximum |effective |max )?range of " + NUMBER +
        r"\s*(km|kilometres|kilometers|nautical miles|nautical mile|nm)\b", re.IGNORECASE), _km, None),
    ("range_km", re.compile(
        NUMBER + r"\s*(km|kilometres|kilometers|nautical miles|nautical mile|nm)\b"
        r"(?:\s+(?:maximum|effective))?\s+range\b", re.IGNORECASE), _km, None),
    ("readiness", re.compile(
        r"\breadiness (?:of|at|is|stands at) " + NUMBER + r"\s*(?:percent|%)", re.IGNORECASE),
        _percent, None),
    ("readiness", re.compile(
        NUMBER + r"\s*(?:percent|%)\s+readiness", re.IGNORECASE), _percent, None),
    ("throughput_per_day", re.compile(
        NUMBER + r"\s*transits per day", re.IGNORECASE), _plain, None),
    ("munitions_stock_days", re.compile(
        NUMBER + r"\s*days of supply", re.IGNORECASE), _plain, None),
    ("mobilization_days", re.compile(
        r"\b(?:requires|needs|takes)\s+" + NUMBER + r"\s*days to mobilize", re.IGNORECASE),
        _plain, None),
    ("mobilization_days", re.compile(
        NUMBER + r"\s*days to mobilize", re.IGNORECASE), _plain, None),
    ("mobilized_brigades", re.compile(
        r"\bmobiliz(?:ed|es)\s+" + NUMBER + r"\s*brigades?", re.IGNORECASE), _plain, None),
    ("mobilized_brigades", re.compile(
        NUMBER + r"\s*brigades?\s+(?:are|is|remain)\s+mobilized", re.IGNORECASE), _plain, None),
    ("capacity_mw", re.compile(
        NUMBER + r"\s*(?:megawatts|megawatt|MW)\b"), _plain, None),
    ("displaced_persons", re.compile(
        NUMBER + r"\s*(?:internally )?displaced persons", re.IGNORECASE), _plain, None),
    ("outage_hours", re.compile(
        NUMBER + r"\s*(?:cumulative )?outage hours", re.IGNORECASE), _plain, None),
    ("outage_hours", re.compile(
        r"\boutages? of " + NUMBER + r"\s*hours", re.IGNORECASE), _plain, None),
    ("count", re.compile(
        r"\bholds " + NUMBER + r"\s*(?:launchers|systems|platforms|vehicles)", re.IGNORECASE),
        _plain, None),
    ("count", re.compile(
        NUMBER + r"\s*(?:launchers|systems|platforms)\b", re.IGNORECASE), _plain, None),
    ("status", re.compile(r"\b(operational|degraded|inoperative)\b", re.IGNORECASE), _word, None),
    ("cyber_capacity", re.compile(
        r"\b(limited|moderate|extensive)\b", re.IGNORECASE), _word, "cyber"),
    ("intent", re.compile(
        r"\b(coercive|defensive|opportunistic|benign)\b", re.IGNORECASE), _word, "intent"),
    ("posture_state", re.compile(
        r"\b(hardened|postured to react|postured_to_react|mitigated|vulnerable|"
        r"out of position|out_of_position|unmitigated)\b", re.IGNORECASE), _word, None),
    ("alignment", re.compile(
        r"\b(blue_aligned|red_aligned|neutral)\b", re.IGNORECASE), _word, None),
    ("alignment", re.compile(r"\baligned with (Blue|Red)\b", re.IGNORECASE), _aligned, None),
    ("basing_access", re.compile(
        r"\bgrants (?:Blue )?basing access", re.IGNORECASE), _true, None),
    ("basing_access", re.compile(
        r"\b(?:denies|withholds|does not grant) (?:Blue )?basing access", re.IGNORECASE),
        _false, None),
]

# relational predicate -> the phrases that introduce the object entity
RELATIONS: dict[str, tuple[str, ...]] = {
    "located_at": ("located at", "operates from", "is deployed at"),
    "operated_by": ("operated by", "is operated by"),
    "subordinate_to": ("subordinate to", "is subordinate to"),
    "supplies": ("supplies",),
    "controls": ("controls",),
    "hosts": ("hosts",),
}


def _icd_terms(vocab_terms: dict[str, list[str]]) -> list[tuple[str, str]]:
    """(surface term, ICD 203 key) longest first, so 'very likely' beats 'likely'."""
    pairs = [(surface, key) for key, surfaces in vocab_terms.items() for surface in surfaces]
    return sorted(pairs, key=lambda p: len(p[0]), reverse=True)


def _date_from(match: re.Match, months: dict[str, int]) -> str:
    day, month, year = match.group(1), match.group(2).lower(), match.group(3)
    return date(int(year), months[month], int(day)).isoformat()


def report_date(text: str) -> str | None:
    """The report's own stated date: its date-time group, else its first long date."""
    dtg = DTG.search(text)
    if dtg:
        month = MONTH_ABBR.get(dtg.group(4).lower())
        if month:
            return date(2000 + int(dtg.group(5)), month, int(dtg.group(1))).isoformat()
    long_date = LONG_DATE.search(text)
    if long_date:
        return _date_from(long_date, MONTHS)
    return None


# ---------------------------------------------------------------- extraction
def extract(
    text: str,
    entities: Iterable[dict],
    *,
    predicates: dict[str, tuple],
    icd203_terms: dict[str, list[str]],
    source_id: str,
    stated_date: str | None = None,
) -> dict:
    """Proposed claims with exact spans, plus what the extractor could not settle.

    Returns ``{"claims": [{"claim": {...}, "flags": [...], "notes": [...]}],
    "instruction_like_spans": [...], "report_date": "..."}``.
    """
    entities = list(entities)
    index = alias_index(entities)
    types = {e["entity_id"]: e["entity_type"] for e in entities}
    terms = _icd_terms(icd203_terms)
    stated = stated_date or report_date(text)
    proposals: list[dict] = []
    instruction_spans: list[dict] = []
    pending: list[dict] = []  # the previous sentence's claims, awaiting a confidence sentence

    for start, end in sentences(text):
        sentence = text[start:end]
        if INSTRUCTION_LIKE.search(sentence):
            instruction_spans.append(
                {"span_start": start, "span_end": end, "text": sentence}
            )
            continue
        confidence = CONFIDENCE.search(sentence)
        found = _sentence_claims(
            sentence, start, index, types, terms, predicates, source_id, stated,
            has_confidence_sentence=bool(confidence),
        )
        if confidence and not found:
            for claim in pending:
                claim["claim"]["confidence_icd203"] = confidence.group(1).lower()
                claim["flags"] = [f for f in claim["flags"] if f != "confidence_missing"]
                claim["notes"].append(
                    f"confidence read from a separate sentence: {sentence.strip()}"
                )
            pending = []
            continue
        proposals.extend(found)
        # A confidence sentence qualifies the claim sentence it follows (ICD 203 1A.6), not
        # every claim since the last one. A sentence with no claim (a paragraph number, a
        # header line) leaves the pending sentence alone.
        if found:
            pending = list(found)
    return {
        "claims": proposals,
        "instruction_like_spans": instruction_spans,
        "report_date": stated,
    }


def _sentence_claims(
    sentence: str,
    offset: int,
    index: dict[str, list[str]],
    types: dict[str, str],
    terms: list[tuple[str, str]],
    predicates: dict[str, tuple],
    source_id: str,
    stated: str | None,
    *,
    has_confidence_sentence: bool,
) -> list[dict]:
    mentions = entity_mentions(sentence, index, types)
    if not mentions:
        return []
    lower = sentence.lower()

    likelihood = next(((s, k) for s, k in terms if re.search(rf"\b{re.escape(s)}\b", lower)), None)
    asserted, valid_from, valid_to, time_flags, time_notes = _times(sentence, stated)

    out: list[dict] = []
    for predicate, phrases in RELATIONS.items():
        for phrase in phrases:
            at = lower.find(f" {phrase} ")
            if at < 0:
                continue
            subject = _nearest_before(mentions, at + 1)
            obj = next((m for m in mentions if m["start"] >= at + len(phrase) + 1), None)
            if subject is None or obj is None:
                continue
            out.append(_proposal(
                predicate, None, obj, subject, sentence, offset, source_id, predicates,
                likelihood, asserted, valid_from, valid_to, time_flags, time_notes,
                has_confidence_sentence, note=f"relational phrase {phrase!r}",
            ))
            break
        if out:
            return out

    for predicate, pattern, reader, required in MATCHERS:
        if required and required not in lower:
            continue
        match = pattern.search(sentence)
        if match is None:
            continue
        value, extra_flags, note = reader(match)
        allowed = predicates[predicate][2]
        if allowed is not None and value not in allowed:
            continue
        subject = _nearest_before(mentions, match.start()) or _subject_fallback(mentions)
        out.append(_proposal(
            predicate, value, None, subject, sentence, offset, source_id, predicates,
            likelihood, asserted, valid_from, valid_to, time_flags + extra_flags, time_notes,
            has_confidence_sentence, note=note,
        ))
        return out
    return out


def _nearest_before(mentions: list[dict], position: int) -> dict | None:
    """The entity mention closest to the left of ``position`` — the sentence's subject."""
    before = [m for m in mentions if m["end"] <= position]
    return (
        [m for m in before if not m["reporting_role"]] or before or [None]
    )[-1]


def _subject_fallback(mentions: list[dict]) -> dict:
    return ([m for m in mentions if not m["reporting_role"]] or mentions)[0]


def _times(sentence: str, stated: str | None) -> tuple[str | None, str | None, str | None, list[str], list[str]]:
    flags: list[str] = []
    notes: list[str] = []
    dtg = DTG.search(sentence)
    asserted = None
    if dtg and MONTH_ABBR.get(dtg.group(4).lower()):
        asserted = date(
            2000 + int(dtg.group(5)), MONTH_ABBR[dtg.group(4).lower()], int(dtg.group(1))
        ).isoformat()
        notes.append(f"asserted time from the date-time group {dtg.group(0)}")
    if asserted is None and stated:
        asserted = stated
        notes.append(f"asserted time from the report's stated date {stated}")
    if asserted is None:
        flags.append("asserted_at_missing")

    as_of = AS_OF.search(sentence)
    if as_of:
        valid_from = _date_from(as_of, MONTHS)
        notes.append(f"valid_from from the 'as of' cue: {as_of.group(0)}")
    else:
        valid_from = asserted
        flags.append("valid_from_assumed")
        notes.append("no 'as of' cue in the sentence: valid_from assumed to be the asserted date")
    until = VALID_UNTIL.search(sentence)
    valid_to = _date_from(until, MONTHS) if until else None
    return asserted, valid_from, valid_to, flags, notes


def _proposal(
    predicate: str,
    value: Any,
    obj: dict | None,
    subject: dict,
    sentence: str,
    offset: int,
    source_id: str,
    predicates: dict[str, tuple],
    likelihood: tuple[str, str] | None,
    asserted: str | None,
    valid_from: str | None,
    valid_to: str | None,
    flags: list[str],
    notes: list[str],
    has_confidence_sentence: bool,
    note: str | None = None,
) -> dict:
    value_type, unit, _, _ = predicates[predicate]
    flags = list(flags)
    notes = list(notes)
    if note:
        notes.append(note)

    subject_id = subject["entity_ids"][0] if len(subject["entity_ids"]) == 1 else None
    if subject_id is None:
        flags.append("entity_unresolved")
        notes.append(
            f"the surface form {subject['surface']!r} resolves to "
            f"{', '.join(subject['entity_ids'])}"
        )
    object_id = None
    if obj is not None:
        object_id = obj["entity_ids"][0] if len(obj["entity_ids"]) == 1 else None
        if object_id is None:
            flags.append("entity_unresolved")
            notes.append(
                f"the object surface form {obj['surface']!r} resolves to "
                f"{', '.join(obj['entity_ids'])}"
            )

    estimative = likelihood is not None
    if estimative and has_confidence_sentence:
        # ICD 203 1A.6 / invariant 12: likelihood and confidence never share a sentence.
        flags.append("mixed_likelihood_and_confidence")
        notes.append(
            "this sentence carries both a likelihood term and a confidence statement; "
            "the confidence was not read from it"
        )
    confidence_icd203 = None
    if has_confidence_sentence and not estimative:
        confidence_icd203 = CONFIDENCE.search(sentence).group(1).lower()
        notes.append("confidence read from the same factual sentence")
    if confidence_icd203 is None:
        flags.append("confidence_missing")

    claim = {
        "claim_id": None,
        "source_id": source_id,
        "subject_id": subject_id,
        "predicate": predicate,
        "object_id": object_id,
        "value": value,
        "value_type": value_type,
        "unit": unit,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "asserted_at": asserted,
        "estimative": estimative,
        "likelihood_icd203": likelihood[1] if likelihood else None,
        "likelihood_surface_term": likelihood[0] if likelihood else None,
        "confidence_icd203": confidence_icd203,
        "confidence": None,
        "span_start": offset,
        "span_end": offset + len(sentence),
        "status": "proposed",
        "supersedes_claim_id": None,
        "truth_claim_id": None,
    }
    return {"claim": claim, "flags": sorted(set(flags)), "notes": notes}
