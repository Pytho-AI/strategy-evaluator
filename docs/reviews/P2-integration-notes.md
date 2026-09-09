# P2 integration notes — in-progress source

Reviewer observations, not a completed-phase verdict. Product files are being edited by
the builder. Recheck against the completed slice before treating these as final findings.

## Round 3 — request ordering

Success check: after requesting batch 1 and then batch 3, the settled UI state must remain
at batch 3 even if batch 1 responds last (or controls must prevent overlapping requests).

Observed in app/ui/src/app.logic.js::loadBatch: every completion calls setState without
checking whether its batch request is still the latest. A read-only Node VM test instantiated
the actual class with a setState stub and deferred API responses. It requested 1, then 3,
resolved 3 first, then 1. Exact output:

```json
{"probe":"out-of-order loadBatch completion","lastRequestedBatch":3,"finalBatch":1,"finalSnapshotBatch":1,"latestSelectionPreserved":false}
```

This proves a method-level race, not an independently observed browser failure. The
template is still being connected. Recheck whether final batch controls prevent overlap;
if they do not, add an out-of-order response test and prevent stale success/error responses
from replacing the latest selection. No product code was changed by the reviewer.

## Earlier checks

- Round 1: API client and backend derivation layer appeared; rendering was incomplete.
- Round 2: all four batches selected approved, temporally applicable current claims.
  Three exact excerpts matched the source slices. New source contracts carry reliability
  and credibility. API serialization and screen rendering still await verification.

Rounds 1–4 were consolidated in Slack message 1788959403.435589 at approximately
13:10 UTC. Lloyd's screen command showed an empty composer before posting. The user
presses Enter; submission has not yet been verified. Do not duplicate the note.
