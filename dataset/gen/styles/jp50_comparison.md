# Style guide: COA comparison (rendered inside a `coa_statement` decision product)

Sources: JP 5-0 App. F §2 weighted numerical comparison (pp. F-1–F-3, Figs. F-1 and F-2); Ch. III
§(12) evaluation criteria (p. III-22); JRAM Encl. B §3.i(9)(b) common numerical basis (p. B-22).

## Weighted numerical comparison table (invariant 16, 17)
Only valid COAs appear (a COA failing any validity test is excluded from comparison).

    | Criterion | Weight | COA 1 rating | COA 1 product | COA 2 rating | COA 2 product | COA 3 rating | COA 3 product |
    | Objective A | 0.40 | 3 | 1.20 | 2 | 0.80 | 1 | 0.40 |
    | ... |
    | Weighted total |  |  | ... |  | ... |  | ... |

Ratings are 1–3, 3 = best (App. F §2.b(3): "The highest number is best"). `rating_1_to_3` is
derived from the rank of each COA's expected contribution to that criterion.

The table is always followed by the App. F caution sentence, verbatim as stored in
`eval/style_check.py::CAUTION`:

    This numeric method is not the result of a rigorous mathematical analysis; comparing courses of
    action by criterion is more accurate than comparing total values.

## Common numerical basis (JRAM Encl. B §3.i(9)(b))
Alongside the table, state each COA's computed value V with its uncertainty: "V = 0.62 (range 0.55
to 0.70 across adversary courses of action; robustness 0.41)". Values inform, not replace, the
commander's judgment (JRAM Encl. B §3.i(9)(c)).
