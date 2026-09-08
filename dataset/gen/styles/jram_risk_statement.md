# Style guide: JRAM risk, opportunity and aggregated risk statements

Sources: CJCSM 3105.01C Fig. 11 (p. B-16), Fig. 12 (p. B-17), Fig. 5 (p. B-7); Encl. B §3.g(1);
probability levels Fig. 6 (p. B-8); consequence levels Fig. 7 (p. B-8); risk levels Fig. 8 (p. B-9);
trend modifiers Encl. B §3.c(3) (p. B-10); time horizons Encl. B §3.a(1)–(2) (p. B-3); risk types
Encl. C §6.b (pp. C-8–C-13).

## Vocabulary (1A.5, 1A.7, 1A.8)
- Probability: `Very Unlikely`, `Unlikely`, `Likely`, `Very Likely` (quoted, capitalized).
- Consequence: `Minor`, `Modest`, `Major`, `Extreme` (quoted, capitalized).
- Risk level: `Low`, `Moderate`, `Significant`, `High`, optionally `, trending up,` / `, trending down,`.
- Risk type: `Military Strategic Risk`, `Military Risk (Risk-to-Mission)`, `Military Risk (Risk-to-Force)`.
  Subsets when named: Operational Risk, Projected Mission Risk, Force Management Risk, Institutional Risk.
- Time horizon: `immediate (days to months)`, `near-term (0-3 years)`, `mid-term (2-7 years)`, `long-term (5-15 years)`.
  Every statement names exactly one.

## Risk statement (Fig. 11, invariant 14, <= 90 words)
Verbatim slot order:

    There is a "[probability level]" probability that [harmful event] in the [time horizon],
    driven primarily by [key drivers] under current [action/inaction/posture/plan] conditions,
    will result in "[consequence level]" consequence. This results in [risk level][, trending up/down,]
    [risk type] to [thing of value].

Rendered by `eval/jram.py::render_risk_statement`; parsed by `RISK_STATEMENT_RE`.

## Opportunity statement (Fig. 12)

    There is a "[probability level]" probability that [beneficial event/opportunity] in the
    [time horizon], if [key actions/conditions] are undertaken, will generate "[consequence level]"
    (beneficial) improvement in [thing of value]. If not pursued, this creates [risk level] risk to [risk type].

## Aggregated (complex) risk statement (Fig. 5)

    If the following related harmful events or conditions occur in combination within the
    [time horizon], [event 1; event 2; event 3], then the Joint Force's ability to
    [execute mission/maintain posture/etc.] may be [degraded/denied] resulting in [risk] to
    [thing of value] in the [time horizon].

"may be" is the doctrine template's own wording and is exempt from the synonym rule. Each event is
assessed individually before aggregation (Fig. 5 note).

## Forced choice (1A.10)
When the dominant driver claim carries the ICD 203 term "roughly even chance", the probability is
never plotted neutrally: it is `Likely` if friendly forces are highly vulnerable, out of position or
lack rehearsed mitigations; `Unlikely` if hardened, postured to react or possessing strong existing
mitigations (Encl. C §4.d(2)). The assessment records the posture factors in `posture_rationale`
(Encl. C §4.e) and the product states them in its sources/assumptions paragraph.
