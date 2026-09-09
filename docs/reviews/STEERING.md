# Reviewer steering — 09 September 2026

The user has asked for ongoing independent monitoring and prompts for the implementing
Claude session. Reviewer writes stay under docs/reviews/. This file is advice to the builder,
not a new product specification or permission to change frozen data.

## Communication cadence

Latest user instruction: remain monitor/reviewer; every few review rounds, consolidate
actionable findings into one prompt typed through Lloyd's exact Claude session thread.
The user presses Enter in Claude. Never equate Lloyd's "typed" acknowledgment with
submission, never resend an unsubmitted note, and do not send per-poll status messages
to the builder. Do not implement product features or alter the bridge.

## Current integration priority

User update at approximately 12:42 UTC: **six hours remain**, giving an approximate cutoff
of 18:42 UTC / 14:42 America/New_York on 09 September. This is a planning anchor, not an
independently verified event schedule. The user also explicitly requests that monitoring not
repeat P0 reviews. Focus on integration and the new-report decision loop; keep P0 findings
in their existing report and recheck them once fixes are ready.

Latest user clarification: **"6 hours is plenty dont worry about rushing."** Keep the full
scope and quality gates. The earlier reviewer-suggested hourly cutoffs and feature-freeze
schedule are withdrawn. Use completion-driven reviews and report a realistic ETA from
observed progress. Prioritize the connected decision loop because it proves the product,
not as a reason to omit other required capabilities.

Prioritize one complete path through the existing UI:

strategy -> decision-relevant gap -> draft collection requirement -> new report ->
reviewed claim -> changed recommendation -> exact source excerpt.

Get this working before polishing secondary screens. Keep every required phase gate;
use this path as the next integration checkpoint rather than expanding feature scope.
Make a changed report value produce a different result. Prove an irrelevant or expired
report cannot close a requirement. Label fixture replay and new-report processing clearly.
Unsupported simulation metrics remain unavailable.

The four original P0-review.md findings were rechecked at 12:51 UTC and are resolved for
their reported cases. The empty workflow-table exception, app-test target, and capability
matrix are also addressed. Do not spend further review cycles repeating these closed cases;
move to the integration gates while keeping regression coverage.

## Evidence required at the next review

- Phase/commit and changed files; distinguish passing tests from work still in progress.
- A working local URL when the UI is connected, with one reproducible browser path.
- API results with dataset identity, as-of time, and consistent batch/version across panels.
- A source excerpt that supports the displayed claim, including dates and review state.
- For ingestion: source body retained, evidence reviewed, satisfaction rule exercised,
  repeat ingestion deduplicated, and history preserved after refresh.
- ETA for the next working browser checkpoint, then the remaining required gates.

## Next integration prompt

For the next integration checkpoint, show one strategy assumption linked to its applicable
claim and exact source excerpt, with validity dates, review status, reliability, and credibility.
Keep UI recovery tests separate from product acceptance tests: preserving the original
placeholder behavior does not prove backend integration. Add a test showing that batch 1
removes the invalid option from recommendations and updates all connected panels consistently.

Observed recovery assertions (`app/tests/ui/test_ui_recovery.py`) intentionally check that
manual ingest displays a title even though its body is discarded, and that Run Wargame
displays P(SUCCESS). Those are valid artifact-equivalence checks, not final product acceptance.
When connecting Meridian Sea, scope these checks to the original placeholder scenario or
replace their product-path counterparts with assertions against real API results. Do not
preserve fabricated output merely to keep a recovery test green.

Reviewer browser status: setup succeeded but browser discovery returned no available browsers.
Independent visual acceptance remains unverified. The recovery suite writes screenshots
under app/tests/ui/screenshots, so the reviewer has not executed that suite unchanged under
the write-only-to-docs/reviews boundary.

## Pitch and demo priorities

Lead with the planner's decision and demonstrate the evidence that changes it. Show the new
report feedback loop early; use the other injects and detailed doctrinal tables as supporting
evidence. The current demo outline is five minutes of replay plus two to three minutes of new
report handling. The actual presentation limit has not yet been supplied, so do not assume
that seven to eight minutes will fit. Keep a short route through the decisive change ready.

Do not claim a score means probability of success, that the adversary-scenario range is a
statistical confidence interval, or that a model is Army-grounded without a publication-to-rule
trace. Report these as implementation facts rather than spending the main demo on internals.

## Monitoring log

- 13:10 UTC, rounds 1–4 consolidated: current-evidence trace gaps reproduced in views.claim_trace;
  batch 1 clm_0844, batch 2 clm_0850, and batch 3 clm_0856 have no outgoing trace paths
  despite driving Blue assumptions. See P1-trace-probes.py and P1-integration-notes.md.
  Also recorded the out-of-order batch completion issue in P2-integration-notes.md.
  Lloyd's read-only screen command showed an empty composer before the new note.
  Posted one consolidated prompt to the exact Claude thread, Slack ts 1788959403.435589.
  The user is responsible for Enter; do not assume submission or send a duplicate.

- 13:06 UTC, integration round 2: the new claim/source contracts include reliability,
  credibility and span_text. An independent direct Index probe across batches 0–3 found
  no selected current claim with non-approved status, a future asserted/valid-from date,
  or expired valid-to date. Exact, nonempty source slices matched for clm_0001, clm_0178,
  clm_0300 (B/2 approved, B/1 superseded, D/4 proposed). These checks exercise derivation,
  not the still-changing API or screen. No new actionable defect established; no prompt sent.

- 13:04 UTC, integration round 1 (in progress): new app/ui/src/api.js and
  app/backend/derive.py appeared; main UI logic and adapter are changing. Derivation
  delegates current-claim selection and evaluation to the dataset engine and introduces
  exact span slicing. UI render/template integration is still being edited. Deferred
  acceptance tests until this slice is coherent; no Slack prompt sent this round.

- 13:00 UTC: user authorized using the Slack Lloyd agent to message Claude. Verified the
  exact session's Lloyd thread (`D0BH069C8P4`, parent `1788899970.637629`) and posted one
  concise integration note, explicitly requesting no acknowledgment or plan interruption.
  Slack confirmed message `1788958805.574479`; Lloyd replied at 13:00:07 UTC that it
  "typed into pytho-ed". User subsequently confirmed it was NOT submitted: text remained
  in the composer awaiting Enter. Treat this as typed only, not delivered to Claude for
  processing. Lloyd's documented controls expose escape/interrupt but no standalone Enter;
  direct Terminal Computer Use is denied by the environment. Do not resend the note.
  Avoid repeat messages; future notes should address a new, concrete issue or completed-phase gate.

- 12:56 UTC: user supplied `https://claude.ai/code/session_01RWNzEmyhUfxnExeRUr4WxY`.
  P0 commit `9299540` records this exact Claude-Session trailer, confirming it matches
  the local session being monitored. The web page could not be fetched; local log evidence
  remains available. At 12:55:12 the builder announced P1 and P2a running in parallel.
  Builder ETA: P1/P2a ~75 min, P2b/P3 ~100 min, P4 ~50 min, P5 ~30 min, roughly
  4.5 hours total remaining. These are estimates, not independently verified completion times.

- 12:54 UTC: the user-named Claude session log confirms builder activity. At 12:52:36
  the builder announced the P0 gate, then commit/P1. Its 12:52:54 tool result reports
  `98 passed, 1 warning in 12.45s`, including recovery UI tests; archive hash matches.
  This is builder-reported execution evidence, distinct from the reviewer's independently
  executed 83 backend tests. No independent browser acceptance is claimed.

- 12:51 UTC: backend-only suite passes 83 tests, one Starlette deprecation warning.
  Independent schema mutation probes now reject both incompatible types; valid strategy
  lookup returns 200 and unknown lookup 404. New nested-mutation tests protect cached data.
  P0-review.md has a resolution addendum. Next review remains product integration.

- 12:46 UTC: recovered UI entry file and strategy/claim detail routes now exist. Read-only
  TestClient checks returned 200 for `str_blue_1` and claims `clm_0001`, `clm_0178`,
  `clm_0300` at batch 3. All fields in those three claim rows match frozen truth exactly
  (approved, superseded, proposed respectively). This is API evidence only, not screen
  verification. `SourceView` currently returns only source_id/title/path; source reliability
  and credibility exist in the dataset but are not returned. Strategy assumptions expose
  metrics without their grounding links. The next P1 integration checkpoint should connect
  assumption -> applicable claim -> exact source excerpt, including reliability/credibility.
  This is unfinished integration work, not a finding against a claimed completed P1.

- 12:41 UTC: P0 still marked in progress. Prior check: 35 dataset tests and 60 backend tests
  passed. CAPABILITY_MATRIX.md and DEMO.md now exist; UI extraction tooling is appearing.
  STATE.md now explicitly documents the empty workflow-table exception. Remaining P0 findings
  will be reviewed when their implementation changes. No new test run was needed at this poll.
