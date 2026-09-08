# Style guide: CJCS directive format (all products)

Applies to every rendered document and product. Source: CJCSM 3105.01C and CJCSI 3100.01F page
furniture and paragraph scheme; formatting guardrails v2 §1A.

## Markings (invariant 11)
- Line 1: `UNCLASSIFIED`
- Line 2: `SYNTHETIC DATA — FOR EXERCISE AND DEVELOPMENT USE ONLY. NOT A REAL ASSESSMENT.`
- Last line: `UNCLASSIFIED`
- No other classification or control marking anywhere, including portion marks such as `(U)`,
  and no `//` separators. Never write the words SECRET, CONFIDENTIAL, NOFORN, FOUO, CUI, ORCON.

## Paragraph scheme (invariant 20 / 1A.2)
Directive-style products (risk context statements, collection plans, COA statements, reference
entries, guidance, assessments) use the CJCS hierarchy and nothing else:

    1.  Top-level paragraph
    a.  Sub-paragraph
    (1)  Sub-sub-paragraph
    (a)  Fourth level
    1)  Fifth level (underlined in doctrine; rendered as "1)" in plain text)

No bullets (`•`, `-`, `*`). Tables use Markdown pipes; a pipe table is not a bullet.

## Dates and times (1A.3)
- Message traffic and situation reports carry a date-time group `DDHHMMZ MON YY`, e.g. `081430Z SEP 26`.
- All other prose dates: `DD Month YYYY`, e.g. `08 September 2026`. Never ISO `YYYY-MM-DD` in prose.
- Schemas (JSONL) use ISO 8601.

## Acronyms (1A.4, invariant 20)
- Only acronyms present in `acronyms.yml` (the five glossaries + ICD 203) may appear.
- Spell out at first use: `Combatant Command (CCMD)`; thereafter `CCMD`. Plural `CCMDs` is allowed.
- Every product ends (just before the closing marking) with `Acronyms used: A, B, C` or
  `Acronyms used: none`.
- Terms with no glossary acronym are always written in words: "date-time group",
  "situation report", "noncombatant evacuation", "not later than". (OB is permitted; ORBAT is not.)
- Do not write titles in all capitals: an all-capital word is read as an acronym.

## Nomenclature
Use the newest document's nomenclature in rendered products: Department of War (DoW), Secretary of
War (SecWar). Quoted doctrine text from 2020/2024 documents is never altered.

## Sourcing (1A.13)
In intelligence products every asserted fact is followed by `[src: <source_id>]`. A sources
paragraph states each source's reliability (A–F) and credibility (1–6).
