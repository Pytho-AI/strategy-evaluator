# Operator workbench UI

The UI uses the shell from `/Users/akshay/Downloads/UI_V2.html` and the API-backed
screens built for the Strategy Evaluation Workbench. The source artifact remains
unchanged. Its SHA-256 is:

```text
b949279befe8fbe7856601cd0f55a6cc1675a707272d81928459b6896c7fdf0c
```

The V2 top command bar and four-stage workflow are retained. Its simulated
scores, local collection cycle, and fake feed are not used. Every strategy,
risk, evidence, and collection result comes from the backend.

## Run

From the repository root:

```sh
make app-run
```

Open <http://127.0.0.1:8765/>. One FastAPI process serves the API and static UI.
There is no frontend build step.

All demo dependencies are local. Text, Markdown, CSV, JSON, and DOCX files are
read in the browser. PDF bytes go to the local API and are parsed with PyMuPDF.

## Source layout

```text
index.html
src/
  api.js                 same-origin API client and OpenAPI route discovery
  boot.js                loads metadata, template, logic, and runtime
  branding.js            non-product chrome; product name comes from /api/meta
  app.dc.html            UI V2 shell and API-backed screen template
  app.logic.js           state, API calls, and response formatting
  app.props.json
  styles/
vendor/                  pinned React and recovered dc-runtime
assets/                  fonts, document reader, and local JIPOE map
tools/                   artifact extraction tools; artifacts are decoded as data
```

## Data rules

- `api.js` is the only network client.
- The UI never computes a score, ranking, risk level, or manifest outcome.
- Missing endpoints and fields render named unavailable states.
- Likelihood and confidence remain separate.
- `value_ci` is shown as an adversary-scenario range, not a confidence interval.
- Write calls require an actor. Review calls also require a reason.
- Product state uses a named workspace outside `dataset/`.

## Tests

```sh
make app-test
```

The browser tests run Chromium against the real backend and frozen dataset.
They cover the V2 shell, all four batches, strategy validity, evidence spans and
traces, risk cascades, collection priorities, report ingestion, claim review,
deduplication, routing, status, persistence, reset, and console/network errors.
