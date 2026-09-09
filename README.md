# strategy-evaluation-workbench

A locally runnable Strategy Option Evaluation workbench, built for a hackathon demo. An operator
loads the fictional Meridian Sea scenario at T0, compares three Blue strategy options against
their five JP 5-0 validity tests, scrubs through three timed inject batches, and traces every
number back to the claim and source span that produced it.

The repository holds both halves: the frozen `strategy-evaluation-dataset-pytho` release under
`dataset/`, and the product that reads it under `app/`.

This is a **standalone** effort. It does not use, modify or depend on coa-engine, pytho-arena,
pytho-vite or pytho-app. Their simulators are recorded as not used, with the evidence, in
[`docs/CAPABILITY_MATRIX.md`](docs/CAPABILITY_MATRIX.md).

## Layout

| Path | Contents |
|---|---|
| `dataset/` | The frozen dataset release: `schema/`, `truth/`, `corpus/`, `injects/`, `eval/`, `extensions/`, `gen/`, `doctrine/EXTRACTS.md`, `DATA_CARD.md`, `USE_CASE_MATRIX.md`, `loader.py`, and the archive. A contract — read only. |
| `app/backend` | FastAPI service on Python 3.12, importing `dataset.load` and `dataset/eval` directly. Owns loading, filtering, recomputation, joins and trace construction. |
| `app/ui` | The UI V2 operator shell with API-backed screens, served by FastAPI. Renders typed API responses; no dataset formula is copied into it. |
| `docs/` | [`STATE.md`](docs/STATE.md) — precheck, architecture decision, dataset facts, phase table, risks. [`CAPABILITY_MATRIX.md`](docs/CAPABILITY_MATRIX.md) — every submitted claim against what exists. [`DEMO.md`](docs/DEMO.md) — the guided demo script. |
| `doctrine/` | The five source PDFs, read-only and not committed. Copy them here. |

## Running the product

    make app-run     # serves the workbench at http://127.0.0.1:8765
    make app-test    # the product's own test suite

One command, offline, no credentials. Verified at 1440x900 against the production
server with the full T0 → batch 1 → batch 2 → batch 3 → T0 flow and no console or
network failures.

## The dataset

`dataset/` is the frozen `strategy-evaluation-dataset-pytho` release: a deterministic synthetic
corpus and relational truth set for testing claim extraction, collection management,
interconnected risk assessment, and strategy option evaluation. It contains a fictional theater,
dated claims, structured decision data, three update batches, and reference scoring code.

Doctrine-grounded: CJCSM 3105.01C (JRAM), JP 5-0, CJCSI 3100.01F (JSPS), JP 2-01, JP 3-60, and
ICD 203 as reproduced in JRAM Fig. 19. Extracts and page citations are in
`dataset/doctrine/EXTRACTS.md`; schemas and formulas in `dataset/schema/SCHEMA.md`.

Size: 92 documents, 864 claims, 122 entities, 9 strategies, 64 Blue worlds. Counts include the
three inject batches. Shipped extensions: `rag_qa`, `target_systems`, `capability`, `authority`,
`collection_assets`, and the optional `events` layer.

Archive SHA-256, immutable:

    fc5c9d311fd1392d0af367f4522842afa807b29ad60ba41cda446cbbeac54418

The dataset's schemas and computed results are frozen contracts. Do not modify them to make the
product easier to build.

### Dataset setup

Python 3.11+ (the venv here is 3.12):

    uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt

### Regenerate and gate

    make gen      # == (cd dataset && python -m gen --seed 20260908)
    make check    # == (cd dataset && python -m gen check --seed 20260908)
    make test     # == pytest -q tests

`make check` runs schema load, invariants 01-20, eval truth-against-truth, the reproducibility
diff and the denylist grep, plus the six extension gates — 28 gates. Regeneration with seed
`20260908` is byte-identical. `make check` writes into a temporary directory and never touches
`dataset/`.

### Load from Python

Run from the repository root:

    from dataset import load
    d = load(base=True, extensions=["rag_qa"], through_batch=1)
    d["claims"].head()

All three arguments are keyword-only; `through_batch` is 0-3. Every base load calls
`eval.engine.recompute`, so values, statuses, rankings, risk levels, EVPI priorities and JIPCL
ranks in the returned frames are computed on the spot, not read from disk. Some state — the ICD
203 forced-choice flag and its posture rationale — exists **only** in that recomputed result;
reading `truth/*.jsonl` directly will show it as absent. Always go through `load()`.

`load(base=True, extensions=<all six>, through_batch=3)` measures at about 0.04 s.

## License

CC BY 4.0 — see `LICENSE`. The synthetic scenario, generated corpus, schemas, and team-authored
code and documentation are licensed under it. The cited doctrine source documents are not
relicensed and remain subject to their source terms.

## Notices

- **Standalone.** Nothing outside this repository is modified. The other Pytho repositories, and
  the user work in them, are listed as protected in `docs/STATE.md`.
- **Fiction.** All scenario content — the Meridian Sea theater, its entities, documents, claims,
  strategies and adversary courses of action — is fictional and team-authored. No real persons,
  polities, organizations or systems. Doctrine, processes and product formats are real and cited.
- **UNCLASSIFIED, synthetic.** That marking is visible in the application and in every export.
- **Decision support, not prediction.** The model is a finite payoff tensor over enumerated
  worlds. Values are scenario-relative decision-support outputs, not predictions of real combat
  outcomes. The `value_ci` field is the min/max expected value across adversary courses of
  action — an adversary-scenario range, not a statistical confidence interval — and dataset
  utility is not a probability of success. Likelihood and confidence are separate quantities and
  are never displayed as one.
