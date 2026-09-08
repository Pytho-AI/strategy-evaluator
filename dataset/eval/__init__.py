"""Reference evaluation harness. Pure functions over the truth tables; the app must match these.

Modules: tables (loading), claimset (current-claim lookup), value (V, sensitivity, robustness, EVPI),
jram (crosswalk, contour, consequence matrices, cascade, trend, statement renderers), validity
(five JP 5-0 tests, distinguishability), engine (recompute every COMPUTED column), style_check
(invariants 11-20 on text), score_extraction, score_effects, baseline.
"""
