# Style guide: tabular (doc_type `tabular`)

A CSV between the marking lines: line 1 `UNCLASSIFIED`, line 2 the caveat, line 3 the header row,
data rows, then `Acronyms used: ...` and the final `UNCLASSIFIED`. Header columns are lower case
(`entity,attribute,value,unit,as_of`). Dates in ISO 8601 are permitted here (machine table).
Perturbations: `typo` (~0.3% characters in value cells), `unit_drift`, `alias`.
