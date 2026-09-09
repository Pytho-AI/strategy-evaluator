# P0 validation command outputs — 09 September 2026

Working directory: /Users/akshay/Dev/pytho/strategy-evaluation-workbench
P0 was in progress and files changed concurrently. The target app-test and capability matrix
appeared during the review. Results below are separate observations, not one atomic revision.

## Dataset checks

Command:
```sh
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/akshay/Dev/pytho/strategy-evaluation-workbench/docs/reviews make check
```

Exit 0:
```text
schema                 PASS  all rows of 28 tables validate
01                     PASS  referential integrity and PK uniqueness
02                     PASS  864 spans inside their source text and mention subject/value
03                     PASS  every fact instantiated by >= 1 claim; every intelligence-bearing document yields >= 1 claim
04                     PASS  no conflicting approved claims overlap in valid time; supersession acyclic
05                     PASS  39 (strategy, condition) groups sum to 1
06                     PASS  weights and opponent distributions sum to 1
07                     PASS  payoffs cover all 600 (strategy, opponent, world) triples exactly once
08                     PASS  escalation edges (6) form a DAG
09                     PASS  every assumption has a grounding fact; shared indices identify the same proposition
10                     PASS  every computed column reproduces from truth to 1e-9
11                     PASS  all 92 products carry the markings and no other marking string
12                     PASS  no sentence mixes a likelihood term with a confidence term
13                     PASS  no product mixes ICD 203 and JRAM vocabularies (deliberate negatives caught: ['src_0042'])
14                     PASS  all 27 risk statements match the Fig. 11 slot order and are <= 90 words
15                     PASS  every assumption is in the decision matrix; every COA statement lists its assumptions
16                     PASS  every strategy carries the five validity entries and a status; invalid COAs absent from comparison tables
17                     PASS  every comparison table is followed by the App. F caution sentence
18                     PASS  MSR rows carry strategic_value/damage_degree; MR rows carry risk_subset/fig28_row
19                     PASS  0 forced-choice assessments all carry posture_rationale
20                     PASS  acronyms glossary-only, spelled out at first use, listed at the end; paragraph scheme, dates, synonyms and lengths conform
repro                  PASS  regeneration with seed 20260908 is byte-identical
denylist               PASS  no real nation/alliance/command/weapon names in scenario content
ext:rag_qa             PASS  schemas, starter query, license, and eval pass
ext:target_systems     PASS  schemas, starter query, license, and eval pass
ext:capability         PASS  schemas, starter query, license, and eval pass
ext:authority          PASS  schemas, starter query, license, and eval pass
ext:collection_assets  PASS  schemas, starter query, license, and eval pass
ext:events             PASS  schemas, starter query, license, and eval pass
```

## Dataset tests

Command:
```sh
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/akshay/Dev/pytho/strategy-evaluation-workbench/docs/reviews PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=docs/reviews/pytest-p0-dataset' make test
```

Exit 0 (concatenated output chunks):
```text
...................................                                      [100%]
=============================== warnings summary ===============================
tests/test_p0.py::test_extracts_verbatim
tests/test_p0.py::test_extracts_verbatim
  <frozen importlib._bootstrap>:488: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

tests/test_p0.py::test_extracts_verbatim
tests/test_p0.py::test_extracts_verbatim
  <frozen importlib._bootstrap>:488: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

tests/test_p0.py::test_extracts_verbatim
  <frozen importlib._bootstrap>:488: DeprecationWarning: builtin type swigvarlink has no __module__ attribute

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
35 passed, 5 warnings in 9.71s
sys:1: DeprecationWarning: builtin type swigvarlink has no __module__ attribute
```

## App test target — initial observation

Command: `env PYTHONDONTWRITEBYTECODE=1 make app-test`

```text
make: *** No rule to make target `app-test'.  Stop.
```

The target was added by the building session during the review. The missing target is resolved
in the final observation below.

## Backend tests — intermediate observation

Command:
```sh
env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/akshay/Dev/pytho/strategy-evaluation-workbench/docs/reviews .venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=docs/reviews/pytest-p0-backend app/tests/backend
```

Exit 0:
```text
........................................................                 [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/akshay/Dev/pytho/strategy-evaluation-workbench/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
56 passed, 1 warning in 0.54s
```

## App test target — final observation

Command: `env PYTHONDONTWRITEBYTECODE=1 make app-test`

Exit 0:
```text
............................................................             [100%]

=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/akshay/Dev/pytho/strategy-evaluation-workbench/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
60 passed, 1 warning in 1.00s
```

This target currently runs backend tests. No app/ui directory was present, so it is not evidence
of frontend test coverage.

## API probes

Read-only FastAPI TestClient calls to create_app(DatasetAdapter()):
```text
{"batch": 0, "status": 200, "load_ms": 34.325, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
{"batch": 1, "status": 200, "load_ms": 29.423, "blue_ranking": ["str_blue_2", "str_blue_3"]}
{"batch": 2, "status": 200, "load_ms": 41.463, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
{"batch": 3, "status": 200, "load_ms": 31.471, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
GET /api/claims 404
GET /api/strategies/str_blue_1 404
GET /api/strategies/str_does_not_exist 404
MISSING DATASET 503 {"error": {"code": "dataset_missing", "message": "dataset directory not found at /path-that-does-not-exist/reviewer-dataset. Check out the dataset next to the app, or point the adapter at it with the STRATEGY_DATASET_DIR environment variable.", "detail": {"dataset_dir": "/path-that-does-not-exist/reviewer-dataset"}}}
SCHEMA TYPE MUTATION value object: ACCEPTED
SCHEMA TYPE MUTATION status object: ACCEPTED
```

Schema mutation was an in-memory Path.read_text patch, not a dataset-file edit.
Reproduce it with P0-probes.py next to this log.

## Hashes and source integrity

Command:
```sh
shasum -a 256 app/backend/adapter.py app/backend/main.py app/backend/contracts.py app/tests/backend/test_api.py docs/STATE.md dataset/strategy-evaluation-dataset-pytho.zip
```

```text
a5a8c08b956ab1a975cda370a01fa656986be56e5f097d97c2b3f090ac154056  app/backend/adapter.py
e641552edf3b5e379f5b03aace835456398043c447f9c2cd6ff82b769cd8e31f  app/backend/main.py
d2ddc0af3a6786f85051bc975a3419418794ea612b89d07e5a8c7ec346c8786b  app/backend/contracts.py
174a8e4296a69d854ea287866326a40a046b419b70f5a2944e9f9c2e775f463f  app/tests/backend/test_api.py
c6e5447dac2215c707cc613afc99675d3437eddf249bbb677ed8404d3776dc4d  docs/STATE.md
fc5c9d311fd1392d0af367f4522842afa807b29ad60ba41cda446cbbeac54418  dataset/strategy-evaluation-dataset-pytho.zip
```

Archive hash matched at the beginning and end of the source checks.
`git diff --stat -- dataset` returned no output.

## Follow-up: 12:51 UTC

Command (repository root):

```sh
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=docs/reviews/pytest-p0-backend app/tests/backend
```

Output (two received chunks joined):

```text
........................................................................ [ 86%]
...........                                                              [100%]
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/starlette/testclient.py:53
  /Users/akshay/Dev/pytho/strategy-evaluation-workbench/.venv/lib/python3.12/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
83 passed, 1 warning in 1.09s
```

Exit 0. UI tests were excluded to avoid their hard-coded screenshot output under app/.

Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/P0-probes.py
```

Output:

```text
{"batch": 0, "status": 200, "load_ms": 32.868, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
{"batch": 1, "status": 200, "load_ms": 30.191, "blue_ranking": ["str_blue_2", "str_blue_3"]}
{"batch": 2, "status": 200, "load_ms": 39.848, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
{"batch": 3, "status": 200, "load_ms": 30.408, "blue_ranking": ["str_blue_1", "str_blue_2", "str_blue_3"]}
GET /api/claims 404
GET /api/strategies/str_blue_1 200
GET /api/strategies/str_does_not_exist 404
SCHEMA TYPE MUTATION value object: REJECTED table 'strategies' property 'value' changed type: expected ['null', 'number'], found ['object'].
SCHEMA TYPE MUTATION status object: REJECTED table 'strategies' property 'status' changed type: expected ['null', 'string'], found ['object'].
```

Exit 0. `/api/claims` collection route is not implemented; the per-ID route is now implemented
and its positive and negative controls passed in the backend suite.
