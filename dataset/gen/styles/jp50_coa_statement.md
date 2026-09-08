# Style guide: COA statement (doc_type `coa_statement`)

Sources: JP 5-0 Ch. III §(6) assumptions (p. III-17–III-18), §(7) operational limitations
(p. III-18), §(9) mission statement (p. III-20), §(q) validity tests (pp. III-41–III-42), Fig. III-21
decision briefing guide (p. III-60); Ch. IV Fig. IV-9 end state/objectives/effects (p. IV-27),
§(b) branches and sequels / decision points (p. IV-38–IV-39). Directive paragraph scheme.

    1. Course of Action <name> (<strategy_id>).
    a. Mission. When directed [when], [who] [what] in [where] in order to [why].
    b. Military End State. <end state objective statement>.
    c. Objectives and Effects.
       (1) Objective <id>: <statement> (evaluation criterion weight w).
       (2) Effect <id>: <statement> (supports objective <id>).
    d. Operational Approach. Main effort: <line of effort>. Sequencing: sequential | simultaneous.
       Task organization: <units>. Reserves: <reserve policy>. Lines of effort and their policy rules:
       (1) <line of effort>: when <condition>, <action> (probability p).
    e. Decision Points and Branches. (1) <dp name>: at the latest in period n, when <condition>,
       branch to rules <ids>; tied to PIR <id>.
    f. Planning Assumptions (decision matrix). Every assumption the COA requires, one per line:
       (1) <assumption_id> (k=<index>): <statement>. Grounded in (<subject>, <predicate>) with
       tolerance <op value>. Origin: own | higher headquarters. Valid: logical yes/no, realistic
       yes/no, essential yes/no. Status: holds | violated | stale | unknown. Sensitivity if incorrect:
       <value>. Flag any assumption with realistic = no as "assumes away an adversary capability".
    g. Constraints (must do). (1) ...
    h. Restraints (cannot do). (1) ...
    i. Validity (JP 5-0 five tests).
       | Test | Result | Evidence |
       Suitable, Feasible, Acceptable, Distinguishable, Complete, each pass/fail with the evidence string.
    j. Risk. Commander's risk functional (expected | CVaR alpha | minimax); value V, its range across
       adversary COAs, robustness; High Military Risk events mitigated by this COA.

Invariant 15: the statement lists every assumption id the strategy requires. Vocabulary: JRAM terms
for risk (no ICD 203 likelihood words). The three Red COAs are labeled most likely / most dangerous /
alternative in the opponent model paragraph.
