# strategy-evaluation-dataset-pytho

Dataset generator and schema contract for a claim-graph prototype that serves four sponsor
use cases (foundational data ingestion, collection management, interconnected risk, strategy
option evaluation). Doctrine-grounded: CJCSM 3105.01C (JRAM), JP 5-0, CJCSI 3100.01F (JSPS),
JP 2-01, JP 3-60, and ICD 203 as reproduced in JRAM Fig. 19.

Layout:

- `doctrine/` — the five source PDFs (read-only; not committed, copy them here).
- `dataset/` — everything that ships: `schema/`, `truth/`, `corpus/`, `injects/`, `eval/`,
  `extensions/`, `gen/`, `doctrine/EXTRACTS.md`, `DATA_CARD.md`, `USE_CASE_MATRIX.md`,
  `PROGRESS.md`, `REVIEW.md`, `loader.py`.

Setup (Python 3.11+):

    uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt

Regenerate everything from the fixed seed and run every gate:

    make gen      # == (cd dataset && python -m gen --seed 20260908)
    make check    # == (cd dataset && python -m gen check --seed 20260908)

Load from Python (run from the repo root):

    from dataset import load
    d = load(base=True, extensions=["rag_qa"], through_batch=1)
    d["claims"].head()

License: CC BY 4.0. All scenario content is fictional; doctrine, organizations, processes and
product formats are real and cited in `dataset/schema/SCHEMA.md` and `dataset/doctrine/EXTRACTS.md`.
