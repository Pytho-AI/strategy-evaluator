# Guided demo script — skeleton

Two flows: the timed inject replay (T0 → batch 1 → batch 2 → batch 3 → T0) and the new-report
collection loop. Target length five minutes for flow A, two to three minutes for flow B.

**Status: skeleton.** Every step below is marked *to be verified in P4*. The expected values come
from the batch manifests and the loader smoke test, not from a run of the product. Nothing here
is confirmed until the browser acceptance flow passes at 1440x900, 1280x800 and a narrow mobile
width.

Standing rules for the demo itself:

- All scenario content is UNCLASSIFIED and synthetic. Keep that marking visible on screen and in
  every export.
- `value_ci` is the **adversary-scenario range** across the three Red COAs. Never call it a
  confidence interval. Dataset utility is not probability of success.
- Likelihood and confidence stay separate. Do not merge them into one probability.
- If a screen has no supported source for a number, it shows unavailable. No fallback to the
  UI's placeholder math.

---

## Setup

| Step | Action | Expected | Status |
|---|---|---|---|
| S1 | Start the product with the one documented offline command (`make app-run`, to be confirmed in P4) | Backend and static UI up on one local URL; no network requests leave the machine | to be verified in P4 |
| S2 | Open the decision overview | Scenario **Meridian Sea**, as-of date and batch **T0**, UNCLASSIFIED-synthetic marking visible | to be verified in P4 |
| S3 | Confirm the baseline state | Three valid Blue options; ranking `str_blue_1`, `str_blue_2`, `str_blue_3`; `str_blue_1` value 0.657667272 | to be verified in P4 |

Say out loud, once, at S2: this is a fictional theater and a finite decision model, not a
prediction of real outcomes.

---

## Flow A — the three inject beats

### Beat 1 — batch 1, as-of 2026-09-28

| Step | Action | Expected | Status |
|---|---|---|---|
| A1.1 | Select batch 1 on the timeline | Every panel recomputes from the backend; no page reload | to be verified in P4 |
| A1.2 | Open `str_blue_1` on the strategy comparison | Status **valid → invalid**. The failing gate is named exactly: the **acceptable** test, `V = 0.3700 below aspiration w·τ = 0.5000`. Suitable, feasible, distinguishable and complete all still pass | to be verified in P4 |
| A1.3 | Read the value change | 0.657667272 → 0.369958724 | to be verified in P4 |
| A1.4 | Read the ranking | Valid ranking is `str_blue_2`, then `str_blue_3`. `str_blue_1` stays visible but cannot be recommended | to be verified in P4 |
| A1.5 | Open the risk view | The **chokepoint** problem set becomes **Significant** on all three horizons (near, mid, long — moderate → significant) | to be verified in P4 |
| A1.6 | Click through from the value change to its evidence | source span → claim → assumption → validity gate, with the exact source excerpt and its asserted and valid dates | to be verified in P4 |

Point to make: an option did not get worse by opinion. One test failed, the test is named, and the
claim behind it is one click away.

### Beat 2 — batch 2, as-of 2026-10-23

| Step | Action | Expected | Status |
|---|---|---|---|
| A2.1 | Select batch 2 | All panels recompute | to be verified in P4 |
| A2.2 | Open the collection view | **`req_01` closes**: research, JIPCL rank 1 → satisfaction, rank null. Its `answered_by_source_id` cites the approved claim from this batch | to be verified in P4 |
| A2.3 | Open the assumption detail for k2 | `asm_blue_1_k2` and `asm_blue_3_k2` move **unknown → holds** (both `index_k = 2`) | to be verified in P4 |
| A2.4 | Return to the strategy comparison | `str_blue_1` is **valid again**; value 0.369958724 → 0.647275499 | to be verified in P4 |
| A2.5 | Read the ranking | `str_blue_1`, `str_blue_2`, `str_blue_3` | to be verified in P4 |

Point to make: this closure is **labelled replay** — the manifest says `req_01` closes. It is not
the product deciding that a report satisfied a requirement. That is flow B.

### Beat 3 — batch 3, as-of 2026-11-17

| Step | Action | Expected | Status |
|---|---|---|---|
| A3.1 | Select batch 3 | All panels recompute | to be verified in P4 |
| A3.2 | Open the assumption detail for k4 | `asm_blue_2_k4` moves **holds → violated** | to be verified in P4 |
| A3.3 | Open `he_05` in the risk view | **Significant** on all three horizons (moderate → significant), `p_raw = 0.57`, likelihood `likely`, dominant driver `rd_0016` | to be verified in P4 |
| A3.4 | Open the forced-choice rationale on `he_05` | `forced_choice_applied = true` with the posture rationale shown verbatim: "Roughly even chance intelligence estimate; plotted Likely because friendly posture factors are Blue logistics network: lacks rehearsed mitigations; Meridian Cyber Protection Team: lacks rehearsed mitigations." Posture subjects `inf_blue_logistics_network`, `unit_cyber_protection_team` | to be verified in P4 |
| A3.5 | Read the problem sets | **cyber** and **energy** both become Significant on all three horizons. Energy moved through a cascade edge, not a local change — show the cascade path | to be verified in P4 |
| A3.6 | Open the collection view | **`req_07` is the first collection priority**: JIPCL rank 1, priority 0.24, `gap_type = contradiction`, `predicate = throughput_per_day`, `subject = inf_kestrel_lane`, `created_at = 2026-11-15`, status `validation`. It is absent from the batch-2 view because requirements are date-filtered by `created_at <= as_of` | to be verified in P4 |

Point to make: the forced-choice flag exists only in the recomputed state. Reading the truth files
directly would show it as false everywhere.

### Return

| Step | Action | Expected | Status |
|---|---|---|---|
| A4.1 | Select T0 again, or use reset-to-T0 | Every panel returns to the S3 baseline; no server restart; nothing under `dataset/` was written | to be verified in P4 |

---

## Flow B — new report to recomputation

A report that is not in the fixture. The ingestion path must be provably unable to read gold
claims, answer keys or manifest `expected_effects`; state which parser or model actually ran.

| Step | Action | Expected | Status |
|---|---|---|---|
| B1 | From a strategy question or PIR, identify a gap | The gap names the strategy or PIR it comes from, the linked assumption or option, the required evidence, and the gap reason | to be verified in P4 |
| B2 | Draft a collection requirement from that gap | A draft with a **stable ID** (not an array position), proposed owner, required evidence, LTIOV and status. A repeat of the same gap is deduplicated with a recorded review decision | to be verified in P4 |
| B3 | Route the draft | An internal queue assignment, with actor, time and reason recorded. Nothing is sent to an external recipient | to be verified in P4 |
| B4 | Ingest a new fictional report authored after the fixture | Original text and its hash preserved; proposed claims extracted with **exact spans** and separate asserted and valid times; entities resolved; uncertain or missing fields shown for review, not invented | to be verified in P4 |
| B5 | Review the proposed claims | Accept the supported ones, reject the rest. Actor, time, source revision and decision reason recorded. A contradictory claim does not silently replace approved evidence | to be verified in P4 |
| B6 | Recompute | The same deterministic evaluation functions used in replay run against the product's versioned graph. Affected assumptions, option validity and value, risks and collection priorities update | to be verified in P4 |
| B7 | Check requirement satisfaction | The requirement closes only because the accepted evidence meets it. Document arrival alone is not enough; expiry or contradiction reopens an unresolved need | to be verified in P4 |
| B8 | Re-ingest the same source | No duplicate claims and no duplicate requirements | to be verified in P4 |
| B9 | Vary the report's value and date in a test | The resulting claim, requirement state, and option and risk changes respond to the actual accepted content | to be verified in P4 |
| B10 | Refresh the page | Review decisions and requirement history survive. The earlier state and the audit record are preserved. Resetting the demo affects only its explicit demo workspace | to be verified in P4 |

If flow B is not finished, say so in the demo and in the final report: the demo is **partial**.

---

## Error and empty states to show if asked

| Step | Action | Expected | Status |
|---|---|---|---|
| E1 | Request an unknown batch | Clear 4xx, readable message, no crash | to be verified in P4 |
| E2 | Request an unknown ID | Clear 4xx | to be verified in P4 |
| E3 | Start with the dataset missing or a schema mismatch | Fails clearly and says why; no silent fallback to mocked or hard-coded results | to be verified in P4 |

---

## What the demo does not claim

Say these plainly rather than letting a screen imply them:

- **No dynamic wargaming.** The model is a finite Bayesian game: 64 enumerated Blue worlds over
  six assumption bits, three Red COAs, evaluated in closed form. No turns, no state transitions,
  no reactive Red. The UI's animated progress bar is not a simulation run and any screen still
  showing it is placeholder.
- **No Army-published adversary model.** No Army publication is named anywhere in the submitted
  text, the UI, the dataset or `doctrine/`. The three Red COAs and their 0.55/0.25/0.20 mixture
  are team-authored fiction and are labelled as such.
- **JP 5-0 grounding is real and is the strongest part.** Show the five validity tests, the exact
  failing gate, and the App. F caution — the numerical method is not rigorous mathematical
  analysis, and comparison by criterion is more accurate than comparison of totals.
- **The Meridian Sea scenario is distinct from the UI's own Olvana / ENDURING PHOENIX content.**
  The two are never merged and the UI's numbers are never relabelled as dataset results.
