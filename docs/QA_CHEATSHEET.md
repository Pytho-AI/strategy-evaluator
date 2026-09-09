# Pytho test cheatsheet

## Start

```sh
make app-run
```

Open <http://127.0.0.1:8765/> at desktop size. Keep browser developer tools open
on the Console and Network tabs. Expected result: no console errors and no failed
API requests.

## Five-minute product test

| Step | Action | Expected result |
|---|---|---|
| 1 | On **Decision Overview**, select **T0**. | All three options are valid. **Anchor** ranks first. The page shows `UNCLASSIFIED — SYNTHETIC` and an as-of date. |
| 2 | Open **Strategy Comparison**. | Each option shows five validity tests, objectives, resources, assumptions, and adversary responses. |
| 3 | Select **Batch 1**, then open **Inject changes**. | `str_blue_1` becomes invalid because **acceptable** fails. Value changes from `0.657667272` to `0.369958724`. |
| 4 | Open **Predictive Interconnected Risk Engine**. | Chokepoint risk is **Significant** on near, mid, and long horizons. |
| 5 | Select **Batch 2**, then open **Collection Management Agent**. | `req_01` is satisfied, has no JIPCL rank, and cites the batch-2 source. |
| 6 | Open **Assumptions & Requirements**. | Corvane basing assumptions change from unknown to holds. |
| 7 | Return to **Decision Overview**. | `str_blue_1` is valid again and ranks first. |
| 8 | Select **Batch 3**, then open the risk engine. | `he_05`, cyber, and energy are **Significant**. `he_05` shows `p_raw = 0.57`; energy shows a cascade path. |
| 9 | Open the collection agent. | `req_07` is JIPCL rank 1 with priority `0.24` and a throughput contradiction. |
| 10 | Open **Intelligence** and inspect a driver claim. | Exact excerpt, character offsets, source rating, asserted time, valid time, likelihood, confidence, and graph path are visible. |
| 11 | Select **T0**. | The baseline returns without restarting the server. |

## Independent report feedback-loop test

Use this file:

```text
app/scripts/fixtures/demo_report_dorne_range.md
```

1. Open **Collection Management Agent**.
2. Fill strategy question, required evidence, gap reason, owner, LTIOV, and a
   linked assumption. Click **Draft requirement**.
3. Submit the same gap again. Expected: the same stable `preq_...` ID appears
   and the history records a duplicate decision.
4. Expand the requirement. Set **Route to** to `JIOC` and click **Route
   requirement**. Select an allowed status and click **Record status**.
5. Open **Intelligence**. Enter a reviewing actor, choose the fixture, and click
   **Ingest report**.
6. Confirm the stored original shows a SHA-256, the `local_rules` extractor, and
   proposed claims with exact source spans.
7. Enter a decision reason and accept a supported claim. Expected: graph version
   increases and affected assumptions, strategy values, risk, and collection
   state update.
8. Ingest the same file again. Expected: it is marked duplicate and does not
   create another report or claim set.
9. Refresh the browser. Expected: review and requirement history remain.
10. Click **Reset demo workspace**. Expected: product-owned state clears and the
    frozen `dataset/` remains unchanged.

## Failure-recovery check

Stop the server while the UI is open and trigger a screen change. Expected: the
UI shows a named unavailable/error state, not invented data. Restart with
`make app-run`, refresh, and repeat the action. Expected: normal data returns.

## Automated release gates

Run these from the repository root:

```sh
make check
make test
make app-test
git diff --check
git diff --name-only -- dataset
shasum -a 256 dataset/strategy-evaluation-dataset-pytho.zip
unzip -t dataset/strategy-evaluation-dataset-pytho.zip
```

Pass conditions:

- `make check`, `make test`, and `make app-test` all pass.
- `git diff --check` prints nothing.
- `git diff --name-only -- dataset` prints nothing.
- Dataset archive SHA-256 equals
  `fc5c9d311fd1392d0af367f4522842afa807b29ad60ba41cda446cbbeac54418`.
- `unzip -t` reports no archive errors.

## Claims to avoid during the demo

- This is a finite decision model, not a combat-outcome predictor.
- Expected value is not a probability of success.
- The displayed range is the minimum and maximum across adversary courses of
  action, not a confidence interval.
- Batch replay is labelled manifest replay. It does not prove that a newly
  uploaded report satisfies a requirement.
- Routing updates an internal queue. It does not send an external collection
  request.
