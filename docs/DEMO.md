# Five-minute demo

Status: verified on 2026-09-09 against the local production server at 1440x900.

## Start

```sh
make app-run
```

Open <http://127.0.0.1:8765/>. The command starts one local process for the UI
and API. It needs no cloud account or model key.

Say this once: the Meridian Sea theater is fictional. The system is a finite
decision model, not a prediction of combat outcomes. Expected value is not a
probability of success. The displayed range is the minimum and maximum across
adversary courses of action, not a confidence interval.

## 0:00–1:00 — decision at T0

1. Start on **Decision Overview** at **T0**.
2. Point to the visible `UNCLASSIFIED — SYNTHETIC` marking and as-of date.
3. Show that all three Blue options are valid and **Anchor** ranks first.
4. Point to the JP 5-0 Appendix F caution and the highest-sensitivity assumptions.
5. Open **Strategy Comparison**. Each option shows the five validity tests,
   objective contributions, resources, assumptions, and adversary response set.

## 1:00–2:00 — inject batch 1

1. Select **Batch 1**.
2. Open **Inject changes**. `str_blue_1` moves from valid to invalid because the
   **acceptable** test fails. Its value moves from `0.657667272` to
   `0.369958724`.
3. Return to **Strategy Comparison**. The invalid option remains visible but
   cannot be recorded as the recommendation.
4. Open **Predictive Interconnected Risk Engine**. The chokepoint problem set is
   Significant on the near, mid, and long horizons.

Point: the option changed because a named test failed. Its supporting claim and
source span are available from the evidence view.

## 2:00–3:00 — inject batch 2

1. Select **Batch 2**.
2. Open **Collection Management Agent**. `req_01` is satisfied and has no JIPCL
   rank. Its answer cites the batch-2 source.
3. Open **Assumptions & Requirements**. The Corvane basing assumptions move
   from unknown to holds.
4. Return to **Decision Overview**. `str_blue_1` is valid again and ranks first.

Point: this requirement closure is labelled manifest replay. It is not proof
that any newly uploaded report satisfies a requirement. The independent report
flow below proves that separate path.

## 3:00–4:00 — inject batch 3

1. Select **Batch 3**.
2. Open **Predictive Interconnected Risk Engine**. `he_05` is Significant on all
   three horizons with `p_raw = 0.57`. Show its dominant driver and forced-choice
   rationale.
3. Show that cyber and energy both become Significant. Energy moves through a
   cascade edge rather than a local claim change.
4. Open **Collection Management Agent**. `req_07` is JIPCL rank 1 with priority
   `0.24`, a throughput contradiction, and validation status.

## 4:00–5:00 — evidence and return

1. Open **Intelligence**.
2. Filter claims or open a driver claim. Show the exact excerpt, character
   offsets, source rating, asserted time, valid time, likelihood, confidence,
   and graph path.
3. Select **T0**. The baseline returns without a server restart.

## Independent report feedback loop

Use `app/scripts/fixtures/demo_report_dorne_range.md`, or paste a new fictional
report that follows its sentence pattern.

1. In **Collection Management Agent**, enter a strategy question, required
   evidence, gap reason, owner, LTIOV, and linked assumption. Draft it.
2. Draft the same gap again. The UI returns the existing stable `preq_…` ID and
   records a duplicate decision.
3. Expand the requirement, route it to `JIOC`, and record an allowed status.
4. In **Intelligence**, enter the reviewing actor, choose the report, and click
   **Ingest report**. The UI shows the stored original’s SHA-256, `local_rules`
   extractor, and proposed claims with exact spans.
5. Enter a decision reason and accept a supported claim. The graph version
   increments, the same evaluator reruns, and affected planning objects,
   strategy values, risk, and collection state update.
6. Re-ingest the report. It is marked duplicate and creates no second report or
   claims.
7. Refresh. Product-owned review and requirement history remain in the named
   workspace. **Reset demo workspace** clears only that workspace; `dataset/`
   remains unchanged.

Automated tests vary the report’s value and date. They also prove that report
arrival alone cannot close a requirement, accepted matching evidence can close
it, and expiry or contradiction can reopen it.

## Claims not made

- No dynamic or Monte Carlo wargame runs. There are no turns or reactive state
  transitions.
- No Army-published adversary model is identified in the supplied sources. The
  adversary courses of action and their mixture are team-authored fiction.
- Constraints and restraints in the frozen dataset are text fields without
  source spans. The product shows that absence and does not invent provenance.
- No external collection request is sent. Routing is an internal queue update.

## Live upload (added 09 September 2026)

The demo now starts with **no strategy loaded**. Drop the plan on stage 1 during the demo:

```text
docs/demo/USEUCOM_OPORD_26-004_AMBER_SHIELD.docx     (also .txt)
```

It is parsed in the browser — no upload to a server, no model key — and populates the
commander's intent, the military end state, eight planning assumptions (each "under review"
at 50% confidence, tracked back to the document) and seven priority intelligence requirements
(each marked as a gap). Those gaps are what stage 2 turns into collection requirements, so the
upload sets up the rest of the demo.

The document is fictional and marked `UNCLASSIFIED — SYNTHETIC`. A real `.docx` or `.txt` can be
dropped instead; `.pdf` needs network access for its parser and should be avoided offline.
