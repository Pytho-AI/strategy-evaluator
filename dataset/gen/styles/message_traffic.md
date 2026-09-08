# Style guide: message traffic (doc_type `message_traffic`)

<= 120 words between the markings (glossary excluded). Header lines in words (no header acronyms
outside the glossaries), then numbered paragraphs. Sentence case body with unit shorthand;
character-level typos at ~0.3% when the `typo` perturbation is planned.

    Date-time group: 081430Z SEP 26
    From: <unit>
    To: <unit or role>
    Subject: <short subject>
    1. <fact sentence> [src: self].
    2. <fact sentence>.
    Acronyms used: ...

Reported facts only; no ICD 203 or JRAM vocabulary. Dates inside the body use the date-time group
form. Perturbations commonly carried: `typo`, `alias`, `unit_drift` (nautical miles), `implicit`.
