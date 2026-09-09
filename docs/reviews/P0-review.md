# P0 independent review — in-progress snapshot

## Follow-up at 12:51 UTC

The four findings below describe the earlier snapshot and are now resolved for their
reported cases. Do not keep treating them as open blockers:

- R1: both independent in-memory type mutations now raise `SchemaIncompatible`.
  New suite cases also cover enum and nested validity changes.
- R2: existing strategy and claim IDs now return 200; unknown IDs return typed 404 errors.
  Tests pair those positive and negative controls on implemented routes.
- R3: STATE.md now explicitly records 56/57 and explains the intentionally empty workflow
  logs as an accepted exception rather than claiming all original assertions passed.
- R4: new tests mutate nested strategy values/validity, append rows, remove a table and
  mutate assumption probabilities; fresh reads remain equal to independent baseline data.
  Public table accessors now return copies.

Backend-only verification: **83 passed, 1 warning in 1.09s**. Exact command and independent
probe output are appended to P0-validation-output.md. The dataset suites were not rerun
because this follow-up checked product-only changes. The UI recovery tests now exist, but
were not run by the reviewer: their screenshot fixture writes under app/, outside the reviewer
write boundary. Independent browser discovery returned no connected browsers.

Three claim API rows (clm_0001, clm_0178, clm_0300 at batch 3) match every original claim
field exactly. Source metadata is still limited to ID/title/path, and no source-to-screen
trace is verified. P1 integration work remains open. This addendum closes the reported P0
defects; it does not certify all phases or replace a completed-phase acceptance review.

## Original snapshot

Review started 09 September 2026 against HEAD `f7cc9149088200bc655601410cc0de4e793e4457`
and the current uncommitted product files. P0 is explicitly marked in progress in
`docs/STATE.md`. Another session is building concurrently. This file will record results
for the observed snapshot; it does not certify later changes.

Verdict: **P0 partial; not approved as complete.** This is an early review, not a claim
that the builder has declared P0 complete. No product source was edited and no commit made.

## Executed checks

Exact commands, outputs, warnings, and source hashes are in
[P0-validation-output.md](P0-validation-output.md).

- `make check`: exit 0, all printed gates pass, including reproduction of the frozen ZIP.
- `make test`: exit 0, 35 passed, 5 warnings.
- Direct backend pytest: exit 0, 56 passed, 1 warning on the intermediate snapshot.
- `make app-test`: initially no target; the builder added it during review. Final execution
  exits 0 with 60 passed and 1 warning. These are backend tests; app/ui was absent.
- API snapshot batches 0..3: all 200; Blue rankings follow the three manifest transitions.
  Load times in the observed calls: 29.423–41.463 ms.
- Missing dataset: `/api/health` returns a structured 503 `dataset_missing` error.
- Archive checksum unchanged; `git diff --stat -- dataset` prints nothing.

The initial missing `docs/CAPABILITY_MATRIX.md` appeared during review and is no longer a
missing-file finding. `docs/DEMO.md` was still absent at the last inspection. Its browser
execution is scheduled for P4, so its absence is recorded as pending work rather than a P0
behavioral defect. The capability matrix correctly identifies unresolved wargaming and
adversary-source claims; this review does not independently validate all its external
repository/publication assertions.

## Findings

### R1 — Medium: incompatible field types pass schema preflight

Location: `app/backend/adapter.py:172` (`_check_schema`), especially lines 187–201.
It checks property names and primary keys, but not field types, nested structures, or enums.
Changing only `strategies.properties.value` to `{"type":"object"}` is accepted. Changing
`strategies.properties.status` to the same incompatible type is also accepted. These schema
changes conflict with the typed response contract, yet `DatasetAdapter.check()` succeeds.

Reproduction: `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/P0-probes.py`.
The probe patches schema reads in memory; no dataset file is changed.

Existing test: `app/tests/backend/test_dataset_errors.py:45`,
`test_tampered_schema_drops_a_column_the_api_reads`, removes `value_ci` and asserts
`with pytest.raises(SchemaIncompatible)`. That proves missing-property rejection but can pass
while incompatible types are accepted, as demonstrated. Keep the frozen dataset intact;
the product preflight needs a compatibility check covering the shapes it consumes.

### R2 — Medium: unknown-ID test cannot prove implemented lookup validation

Location: `app/tests/backend/test_api.py:109`,
`test_unknown_id_lookup_is_not_served_yet`.
Assertions:

```python
assert client.get('/api/strategies/str_does_not_exist').status_code == 404
assert client.get('/api/claims/clm_does_not_exist').status_code == 404
```

Both pass when the routes are completely absent. Direct reproduction also returns 404 for
the existing `str_blue_1`. The test itself honestly labels this a placeholder, but it does
not meet the handoff's P0 unknown-ID acceptance requirement. Add a valid-ID 200 control and
unknown-ID rejection on the same implemented route, or keep this criterion explicitly partial
until P1. Do not treat an unregistered route as input validation coverage.

### R3 — Medium: all-PASS precheck contradicts an explicitly failed assertion

Location: `docs/STATE.md:30`–31 marks the loader/manifest smoke test PASS while recording
`56 of 57 assertions pass`. The handoff requires required extension tables to be present and
nonempty; the authority decision log and collection tasking plan are empty. The dataset is
frozen, so this is not a request to populate it. Distinguish read-model tables from intentionally
empty workflow logs, identify the accepted product behavior for those logs, and record the
exception rather than representing the original assertion as passing. The existing manifest
comparison checks do pass independently.

### R4 — Low: cache immutability test checks identity, not immutability

Location: `app/tests/backend/test_adapter.py:16`,
`test_cached_snapshots_are_returned_unchanged`, asserts only `first is second`.
`BatchSnapshot` freezes attributes but its nested tables remain mutable, and `table()` returns
the stored lists directly (`app/backend/adapter.py:103`–113). The test can pass even if an
internal caller mutates the returned data and changes subsequent responses. No external
mutation endpoint currently exposes this path, so this is a contract/test weakness, not a
demonstrated remote corruption bug. Decide whether callers receive isolated copies or immutable
data and test that behavior before product-state mutations are added.

## Acceptance-test quality

| Test | Exact assertion or operation | What it proves and what it can miss |
|---|---|---|
| `test_snapshot_loads_every_batch_with_nonempty_tables` | `assert response.status_code == 200`; `assert body[table]` | All four batch endpoints and five response collections are populated. Could pass with fixed values. Manifest tests supply the value check. |
| `test_strategy_values_and_statuses_match_the_manifest` | `assert after[sid]['value'] == pytest.approx(row['value_after'], abs=1e-9)` | Enumerated changed strategy values/statuses match an external fixture oracle. Could pass with manifest hardcoding; source inspection must accompany it. |
| `test_ranking_matches_the_manifest` | `assert blue_ranking(snapshot(client, batch)) == effects['ranking_after']` | Exact Blue ranking at each batch. Stronger than comparing sorted membership. |
| `test_blue_ranking_comes_from_the_reference_engine` | `assert sorted(adapter.blue_ranking(snapshot)) == sorted(valid)` | Membership only; a reversed ranking could pass this test. The separate manifest ranking test closes that gap for Blue fixture batches. |
| `test_invalid_batch_is_rejected_with_422` | `assert response.status_code == 422`; checks structured error code/message | Covers out-of-range, empty, nonnumeric, and fractional query inputs. |
| `test_missing_dataset_directory_returns_503` | `assert response.status_code == 503, url` | Missing root produces a clear failure across all four existing routes. Independently reproduced for health. |
| `dataset_hashes_before` / no-source-writes tests | `assert after == before` for SHA-256 tree maps | Detects retained content changes in dataset files across the test run; ignores bytecode, and cannot prove no transient write occurred. |
| `test_cold_load_of_batch_3_is_under_two_seconds` | `assert elapsed < 2.0` | Real cold adapter construction/load satisfies the laptop bound in this run. Does not measure browser completion time. |

## Source-of-truth and provenance checks

Search: `rg -n 'str_blue_|0\\.658|significant|req_07|value_ci|confidence|likelihood' app/backend`.
The observed hits are `value_ci` in required-column declarations, the direct `adversary_range`
mapping in main.py, and its contract description. Those are valid schema references. No
hand-entered strategy scores, rankings, risk levels, or copied evaluation formulas were found
in the inspected backend. Dataset ID constants for game/actor selection are identifiers, not
fabricated numerical outputs. Rankings call `eval.engine.ranking`; snapshots call the loader.

`contracts.py:85` correctly calls `value_ci` an adversary range and explicitly says it is not
a statistical confidence interval. There is no displayed UI yet to verify this label visually.
The API currently returns assumption `p_holds` without exposing source likelihood/confidence;
that is not itself evidence of merging them, but the source fields still need to be delivered.

Three-claim end-to-end provenance verification is **not possible in this snapshot**:
`GET /api/claims` returns 404, the snapshot response has no claims/sources, and app/ui is absent.
Do not mistake inspecting ground truth directly for proving it reaches the API or screen.
Record this as pending P1/P3 coverage. Browser testing at all three sizes begins at P2;
new-report ingestion adversarial testing begins at P3. Neither phase is claimed ready here.

## Requirement verdicts

| Requirement | Evidence | Verdict |
|---|---|---|
| Frozen dataset gates and archive identity | make check, make test, checksum, no dataset diff | met |
| Read adapter and typed API responses | adapter/main/contracts; 60 backend tests | met |
| Batch 0..3 evaluation and valid Blue ranking | API probes and manifest tests | met |
| Invalid batch and missing dataset errors | 422 tests and independent 503 probe | met |
| Unknown-ID validation on real routes | absent valid and invalid routes both return 404 | partial |
| Incompatible-schema rejection | missing-property/key checks pass; type mutations accepted | partial |
| All precheck assertions pass | state reports a failed assertion under PASS | partial |
| No retained dataset content writes | suite tree-hash checks and unchanged archive | met |
| Source-to-screen provenance for three claims | claims route and UI absent | missing |
| Adversary-range label | accurate backend contract; UI pending | partial |
| Backend and UI test entry point | make app-test added and green; no UI suite yet | partial |
| Browser and new-report acceptance | future P2/P3 phases, not exercised | missing |

Highest-priority follow-ups: R1 schema compatibility; R2 valid/invalid ID controls;
R3 reconcile the failed precheck assertion; R4 clarify and test cached-snapshot ownership.
These findings apply to the recorded source snapshot and should be rechecked if the building
session has already changed the named functions.
