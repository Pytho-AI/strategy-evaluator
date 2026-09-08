## Goal
Finish all work in CLAUDE_CODE_PROMPT_dataset_and_schemas_v2.md and its referenced v1 prompt from Downloads.
## Now
P7 passed. Record its Git gate, then build P8 extension layers in priority order.
## Next
1. Repair facts history; gate: tests/test_p0.py and tests/test_p1.py.
2. P2: strategies, payoff tensors, grounding graph, validity; gate: tests/test_p2.py.
3. P3: risk inputs/cascade; gate: tests/test_p3.py.
4. P4: finish intelligence and doctrinal product rendering; gate: tests/test_p4.py.
5. P5: inject manifests and loader; gate: tests/test_p5.py.
6. P6: extraction/effects scorers and measured baseline; gate: tests/test_p6.py.
7. P7: data card, review samples, documentation, reproducibility, zip; gate: make check.
8. P8: all five required extensions, optional events if practical; per-extension tests, final package.
## Constraints
No web scraping. No external datasets beyond doctrine/.
This session does not build the application.
Treat every schema as a contract: once its acceptance tests pass, it is frozen.
Never fabricate a fact about a real entity, and never attribute a fictional fact to a real organization.
Write the test before the code. Do not advance on a failing gate.
Never commit a failing gate.
## Decisions
Continue existing branch dataset and preserve the three uncommitted files from Claude.
Use deterministic template rendering already selected in PROGRESS.md; document any unavailable LLM baseline honestly.
Dates use inclusive valid_to in the frozen contract; claim spans use half-open character offsets.
Name the deliverable and archive strategy-evaluation-dataset-pytho; keep the existing repository directory and Git history.
## Facts
Repo: /Users/akshay/Dev/pytho/claimgraph-dataset; Python: .venv/bin/python; seed: 20260908.
Commands: make gen, make check, make test; dataset CLI runs from dataset/.
Prompts: /Users/akshay/Downloads/CLAUDE_CODE_PROMPT_dataset_and_schemas_v2.md and CLAUDE_CODE_PROMPT_dataset_and_schemas.md.
Session file: /Users/akshay/.claude/projects/-Users-akshay-Dev-pytho/16799664-a28c-4ca1-9f0f-6441ef1f5125.jsonl.
gen/models.py: table models 18-589, registry 593 onward; gen/validate.py: invariants 30-338, dispatch/schema 343 onward.
gen/render.py: names/clauses 52-206, acronym expansion 207-253, compose 255-418, render_plans 421-463, build 469 onward.
gen/scenario_data.py: entities 1-138, facts/injects 139-263, guidance/objectives 265-298, actions/game 300-357, PIRs 359 onward.
## Done
Recovery: git history confirms P0/P1 commits; baseline pytest: 7 passed, 1 failed at tests/test_p1.py:53.
Read global user instructions, guardrails PLAN/CODE/DEBUG/EFFICIENCY/SESSION/TRAPS, and PDF skill.
P2–P7 focused gates pass; P7 `make check` passes schema, invariants 01–20, reproducibility, denylist.
## Open items
Audit agent contract_audit examines existing evaluator/model/validator defects without editing.
LLM rendering/baseline credentials and capability not yet established; no model baseline result may be fabricated.
## Failed attempts
Baseline (before edits): fct_0427 supersedes fct_0003 despite a 38-day validity gap.
ATTEMPT 1 [L1]: generated P4 products -> collection ltiov was an ISO string passed to fmt_date, raising AttributeError.
ATTEMPT 2 [L1]: patch command used invalid target /lify -> apply_patch rejected it; no file changed.
ATTEMPT 3 [L2]: P4 ranking gate -> req_05 ranked first because fallback priority summed graph degrees over current and future claims.
ATTEMPT 4 [L2]: P4 span gate -> fraction 0.78 rendered as 78 percent was not recognized as the same value.
ATTEMPT 5 [L3]: P4 coverage gate -> sitrep plan contained fct_0420, but render.py's sitrep branch ignored echo_facts.
ATTEMPT 6 [L4]: P6 truth sourcing score -> duplicate semantic claims paired across sources, producing 0.932292 despite identical input.
P7 baseline: dataset.loader did not exist; tests/test_p7.py failed during import.
