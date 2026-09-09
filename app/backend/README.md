# Backend — Strategy Option Evaluation workbench (P0)

Read-only HTTP API over the frozen `strategy-evaluation-dataset-pytho` dataset in
`dataset/`. P0 covers loading, identity, contracts and error states. Evaluation
services (per-strategy, risk, collection, evidence) arrive in P1.

## Run

From the repository root, with the project venv:

```bash
make app-run      # uvicorn on http://127.0.0.1:8765
make app-test     # .venv/bin/python -m pytest -q app/tests
```

`make app-run` is `.venv/bin/python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8765`.
Set `STRATEGY_DATASET_DIR` to serve a dataset directory other than `dataset/`.

Dependencies: `app/requirements-app.txt` plus the repo's `requirements.txt`.

## Endpoints

| Endpoint | Returns |
|---|---|
| `GET /api/health` | `ok`, dataset identity, `load_ms` for batch 0 |
| `GET /api/meta` | product name, dataset name, marking, identity, batches 0..3 with `as_of` and per-table row counts, world counts |
| `GET /api/injects` | the three inject manifests: `batch`, `as_of`, `docs`, `change_events`, `expected_effects` |
| `GET /api/snapshot?batch=0..3` | `as_of`, `batch`, `marking`, strategies, rankings, assumptions, problem-set assessments, collection requirements |
| `GET /api/strategies/{strategy_id}?batch=0..3` | one strategy in the snapshot's shape, plus its assumptions and its `strategy_objectives` weights |
| `GET /api/claims/{claim_id}?batch=0..3` | the claim row as loaded, plus its source `title` and `path`. P1 types the claim row and adds the collection listing. |

Lookups default to `batch=0`. An id the loaded batch does not contain returns 404
`{"error": {"code": "unknown_id", ...}}`; a `batch` outside 0..3 returns the same 422
`invalid_request` body as `/api/snapshot`.

Response models are pydantic models in `contracts.py`; the OpenAPI schema is at
`/docs` and `/openapi.json`.

Notes on the snapshot payload:

- `adversary_range` is the dataset's `value_ci`: the min/max expected value across
  adversary COAs. It is not a statistical confidence interval and not a casualty
  estimate.
- `value`, `robustness`, `p_holds`, `sensitivity`, `evpi`, `priority` and
  `jipcl_rank` are scenario-relative decision-support outputs, not predictions.
- `rankings` lists valid strategies best-value-first, one entry per (game, actor).
  Invalid and infeasible strategies stay in `strategies` but never appear in a
  ranking.
- `marking` is `UNCLASSIFIED — synthetic` and must stay visible in the UI and in
  exports. The product name lives only in `branding.py` (`PRODUCT_NAME`).
- `load_ms` and `response_ms` are different clocks. `load_ms` is how long the load
  that *populated the cache entry* took, so a cached batch keeps reporting the cold
  number; `response_ms` is the time this request spent in the route (snapshot lookup,
  copying the tables it needs, building the response model) and is well under a
  millisecond on a cache hit. `response_ms` stops before the framework serializes
  the model to JSON, so it is a floor on wall-clock latency, not the whole of it.
- `worlds.blue_worlds` is 64 — the theta-assignments over the Blue actor's
  assumptions. The data card's "66 worlds" is `worlds.distinct_world_labels`, the
  union of `payoffs.world` label strings across all four (game, actor) pairs; the
  three K=1 actors share the labels `0` and `1`. Summing the per-actor world sets
  gives 70. `/api/meta` reports both figures and the note.

## Where numbers come from

`adapter.py` calls `dataset.load(base=True, through_batch=batch)`, which runs
`dataset/eval/engine.py::recompute` on every call, and converts the returned
DataFrames to plain dicts. Rankings come from `eval.engine.ranking`.

The rules this backend keeps:

- No computed column is read from `dataset/truth/*.jsonl`. Values, statuses,
  rankings, sensitivities, EVPI, risk levels and JIPCL ranks are computed, not
  stored — reading the truth files directly gives the T0 world only. The
  forced-choice risk flag, for instance, is false everywhere in the truth file and
  true on six rows after batch 3.
- No eval formula is copied into the backend or the frontend.
- No expected outcome is typed into product code. The manifests are read by the
  tests as the oracle, never by the app to produce an answer.
- Nothing writes to `dataset/`. `app/tests/backend/test_no_source_writes.py`
  hashes every file under `dataset/` before and after the run.

## Cache ownership

The cache owns its tables; callers own what they are handed. `BatchSnapshot.tables`,
`.table()`, `.find()` and `.rows_where()` all return deep copies, so a caller that
mutates a response cannot change a later one. Copying every table costs about 9 ms
(4 ms of that the 864 claims) against a 2 s budget; a route that touches only
strategies/assumptions/objectives copies in under 0.3 ms. The adapter's own read-only
paths (`ranking`, `world_counts`) read the private `_tables` and skip the copy.
`app/tests/backend/test_adapter.py` mutates a returned table and asserts the next read
still equals a fresh load; `test_api.py` asserts the batch-1 response body is unchanged
by a mutation attempt.

## Cache key

Batch snapshots are cached under `(dataset identity, batch)`, where
dataset identity is

```text
<SHA-256 of dataset/strategy-evaluation-dataset-pytho.zip>:<git HEAD of the dataset checkout>
```

with `no-archive` / `no-git` standing in when either is unavailable. Changing the
archive or the checkout produces a different key, so a stale batch cannot be
served. A cold load of batch 3 takes about 40 ms against a 2 s budget, so caching
is a convenience, not a requirement.

## Error states

Preflight runs before any load and never falls back to mocked data.

| Condition | Status | `error.code` |
|---|---|---|
| `dataset/` missing, or missing `truth/`, `schema/`, `injects/`, or an inject manifest | 503 | `dataset_missing` |
| a schema file is gone, unparseable, has lost a column the API reads, changed its `x-primary-key`, or changed the type/enum/nesting of a field the API reads; or a required table loads empty | 500 | `schema_incompatible` |
| `batch` outside 0..3, or not an integer | 422 | `invalid_request` |
| a strategy or claim id the loaded batch does not contain | 404 | `unknown_id` |

Error bodies are `{"error": {"code": ..., "message": ..., "detail": {...}}}`.
The 503 message names the directory it looked in and the `STRATEGY_DATASET_DIR`
override; the 500 message names the table and the column, key, type or enum that
changed; the 404 message names the id that was asked for.

### Schema preflight

`REQUIRED_SHAPES` in `adapter.py` is the whole contract: per table, the properties the
API reads, the exact set of JSON types each may take once `$ref` and `anyOf` are
flattened, the exact enum value set where the product branches on it, and nested
properties where it reads into a structure. Preflight compares it against
`dataset/schema/*.json` and rejects, per property, a changed type, an added, removed or
renamed enum value, and a changed or missing nested field. Declared today:

| Table | Checked properties |
|---|---|
| `strategies` | ids/name (string), `status` (enum `valid`/`invalid`/`stale`/`infeasible`), `value`, `robustness` (nullable number), `value_ci` (nullable array), `validity` → the five tests → `pass` (boolean) and `evidence` (string) |
| `assumptions` | ids (string), `index_k` (integer), `statement`, `status` (enum `holds`/`violated`/`stale`/`unknown`), `p_holds`, `sensitivity`, `evpi` (nullable number) |
| `problem_set_assessments` | `problem_set_id`, `jsps_horizon` (enum), `max_risk_level` (enum `low`/`moderate`/`significant`/`high`), `he_ids` (array), `aggregated_statement_text` |
| `collection_requirements` | `req_id`, `status` (enum `research`/`validation`/`submission`/`satisfaction`/`closed`), `priority` (nullable number), `jipcl_rank` (nullable integer) |
| `payoffs` | `strategy_id`, `world` (string) |
| `strategy_objectives` | `strategy_id`, `objective_id` (string), `weight` (number) |
| `claims`, `sources` | `claim_id`/`source_id` (string), source `title` and `path` (string) |

Nothing speculative is listed: every row is a field `contracts.py` or a route reads.
`risk_assessments.risk_level` / `p_level` / `c_level` are deliberately absent — no route
reads that table yet, and the `RiskLevel` vocabulary the product does depend on is pinned
through `problem_set_assessments.max_risk_level`. When P1 serves risk, add the table
there.

## Files

```text
app/backend/adapter.py     dataset loading, identity, preflight, batch cache
app/backend/branding.py    PRODUCT_NAME and the classification marking
app/backend/contracts.py   typed pydantic responses
app/backend/errors.py      DatasetMissing / SchemaIncompatible
app/backend/main.py        create_app() and the four P0 endpoints
```
