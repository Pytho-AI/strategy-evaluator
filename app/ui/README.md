# Operator workbench UI

The workbench recovered from the supplied `__bundler` artifact. Same design,
same navigation, same interactions — see `RECOVERY.md` for where every file came
from and the seven hand edits applied on top.

It is plain static files. There is no build step: `dc-runtime` compiles the
template in the browser at load.

## Serve it standalone

```sh
cd app/ui
python3 -m http.server 8000
# http://127.0.0.1:8000/
```

It must be served over HTTP, not opened as a `file://` URL — `boot.js` fetches
the template and the logic, and `docreader.js` is a dynamically imported ES
module. Both are blocked on opaque file origins.

Everything it needs is vendored. The page makes no outbound request: React,
dc-runtime, the fonts, the JIPOE map, d3, topojson and the world basemap are all
local. The single exception is `assets/docreader.js`, which fetches
`pdf-parse` from jsDelivr — and only when a user uploads a `.pdf`.

## Mount it from the backend

Serve the directory as static files with directory-index behaviour:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/ui", StaticFiles(directory="app/ui", html=True), name="ui")
```

Every path in the page is relative to the document (`./src/…`, `./vendor/…`,
`./assets/…`), so any mount prefix works — but link to `/ui/` **with** the
trailing slash. Without it the browser resolves relative URLs against `/` and
every asset 404s. The API can then live under a sibling prefix; nothing in the
UI hard-codes an origin.

## Layout

```
index.html                    entry page: stylesheets, pinned React UMD, the
                              UNCLASSIFIED — SYNTHETIC marking, the <x-dc> mount
src/
  boot.js                     loads the template + logic, then dc-runtime
  branding.js                 BRANDING — the only place naming lives
  app.dc.html                 the <x-dc> template (markup + sc-for/sc-if/{{ }})
  app.logic.js                class Component extends DCLogic — all behaviour
  app.props.json              the startView / startStep prop schema
  styles/
    01-industry-tokens.css    design-system tokens + Barlow @font-face
    02-source-sans-3.css      Source Sans 3 @font-face
    03-app-overrides.css      the app's dark theme
vendor/                       generated/third-party, never hand-edited
  dc-runtime.js               template compiler + DCLogic + React bootstrap
  react.production.min.js     18.3.1 UMD
  react-dom.production.min.js 18.3.1 UMD
  ds-bundle-industry.js       @ds-bundle stub, declares no components (no-op)
assets/
  docreader.js                .docx/.txt/.md/.json/.pdf reader, extractPlan(),
                              signalIndex(); dynamically imported by loadDocs()
  fonts/*.woff2               22 subsetted webfaces
  jipoe-map/                  the d3 JIPOE overlay, loaded in an iframe
    index.html  vendor/d3…  vendor/topojson-client…  data/countries-110m.json
    fonts/*.woff2
tools/
  extract.py                  decode the artifact bundle as data
  lay_out_source.py           lay the decoded tree out as this source tree
```

### How it boots

`index.html` loads React and the stylesheets, then `boot.js` fetches
`app.dc.html`, `app.logic.js` and `app.props.json`, installs them as the
`<x-dc>` element and a `<script type="text/x-dc" data-dc-script>`, and loads
`vendor/dc-runtime.js`. dc-runtime finds both, compiles the template into React
elements, and replaces `<x-dc>` with `#dc-root`.

### Where to make changes

* **Naming** — `src/branding.js`. Nothing else carries the product or team name.
  The backend keeps its own copy in `app/backend/branding.py`
  (`PRODUCT_NAME`, `MARKING`). The two are not yet reconciled — the marking
  strings differ in case (`UNCLASSIFIED — SYNTHETIC` here, `UNCLASSIFIED —
  synthetic` there). P2 should make one of them the source and have the other
  read it, rather than leaving two literals.
* **Behaviour and data** — `src/app.logic.js`. One class; `renderVals()` is the
  single function that turns state into everything the template reads. That is
  the seam the services attach to.
* **Design** — `src/styles/*.css` and `src/app.dc.html`.
* **Never** `vendor/`. `dc-runtime.js` is generated upstream from
  `dc-runtime/src/*.ts` (`bun run build`) and that source was not shipped.

## Tests

```sh
uv pip install --python .venv/bin/python playwright   # or: .venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest -q app/tests/ui
```

Serves this directory and a copy of the original artifact side by side and
compares them in Chromium at 1440x900. See `app/tests/ui/test_ui_recovery.py`.

---

## What P2 must rewire

P0 is a faithful recovery: **every number this UI shows today is computed
locally from hand-written constants, and P0 deliberately left all of it in
place and unrelabelled.** Nothing below has a dataset behind it yet.

Two rules for the rewiring:

1. Nothing the artifact fabricates keeps its current label once a real number
   sits next to it. Each of the metrics below gets a supported source under its
   real name, or renders as explicitly unavailable. The UI already has the
   "thin evidence" treatment to reuse for that.
2. Stable ids come first. Six behaviours key off array position; introducing ids
   is a pure refactor of `app.logic.js` that touches no markup, and every other
   change depends on it.

### Handlers to replace

| Handler | `app.logic.js` | What it does today |
|---|---|---|
| `COA_LIB` + `buildCoas()` | l.152 / l.179 | Options come from a five-entry literal table; `buildCoas()` slices it and string-replaces the adversary name. |
| `compute()` | l.194 | Monte-Carlo over five hand-written constants per option (`s`, `cas`, `esc`, `days`, `res`). No adversary model, no state transition, no opposing decision — Gaussian noise around a fixed number. |
| `runSim()` | l.183 | A 120 ms `setInterval` progress bar over four status strings (`'Initializing red cell from JIPOE…'`, `'Sampling adversary reactions…'`, …) that assert a red cell which does not exist, then calls `compute()`. |
| `ranked()` / `rankWith()` | l.223 / l.220 | Weighted JRAM score, `raw / max` as a percentage. The JRAM 4-band scale itself (`level()`, `riskColor()`, `score()`) is the one rule a publication genuinely shapes — keep it. |
| `arcFor()` | l.231 | Returns a hard-coded three-row action/reaction/counteraction table keyed by option number, with only the adversary name templated in. DP1–DP3 are prose. |
| `PROBLEM_SETS` + the propagation block | l.119 / l.~387 | Failing an assumption applies a flat −0.14 to dependent options and −0.03 to the rest, and the "how far the effect travels" labels are read straight out of a hand-written array. There is no graph to traverse. |
| `sendWeakToCollection` / `w.draft` | l.383 | Drafts requirements from weak assumptions with `indicators: ['Indicators to be defined by J2']` and `assets: ['Unassigned']`, linked by array index. |
| `p.cycle` | l.416 | "Collection returned" sets the linked assumption to Valid and `conf: Math.max(a.conf, 85)` — no report, no claim, no review, no provenance. Replace with the reviewed-evidence satisfaction rule; the status advance becomes a consequence of the service response. |
| `ingest` | l.411 | Stores title and type, assigns `pir: 1 + (s.intel.length % 3)`, and discards the report body — `state.intel` has no body field. |
| `loadDocs()` / `docreader.js` | l.73 | Genuinely useful and worth keeping. Gaps: `.pdf` needs a CDN, `extractPlan()` returns text slices with no character offsets so no source span can be cited, nothing persists, and there is no review step between extraction and acceptance. |
| `postureStats` / `forces[]` | l.423 / l.424 | Literal strings and nine hand-written force packages. |
| `decide()` | l.291 | Records a decision object with `new Date().toLocaleString()`. Nothing else in the app is time-aware. |

### Fabricated metrics

| Shown as | Actually | 
|---|---|
| `P(SUCCESS)` 76% / 70% / 46% | fraction of `N=2000` Gaussian samples ≥ 0.5 around the literal `c.s`. Dataset utility is not a probability of success. |
| `80% CI` 29–100 / 23–100 / 4–91 | the 10th and 90th percentile of that made-up noise term. Not a simulation confidence interval. |
| `CASUALTIES P90` 2.5% / 1.9% / 0.6% | 90th percentile of `c.cas × (0.7+0.6·ag) + N(0, 0.45·c.cas)`. The dataset's adversary range is not a casualty estimate. |
| `P(ESCALATION)` 36% / 22% / 13%, and `20/12/7% beyond theater` | two Bernoulli draws at `c.esc + 0.35(ag−0.5)` and `0.35 + 0.4·ag`. |
| Propagation hop counts — `Direct`, `1 hop`, `2 hops` | the position of a label in `PROBLEM_SETS[failIdx]`. No edges are traversed. |
| The ARC table and its DP1–DP3 decision points | `arcFor()`'s fixed script. Not derived from any run. |
| `Weighted Score` 59/70/75%, `33/56`, `Rank stability 76%`, the aggression sweep, `widen … by ~22 points of σ`, `−17 / −6 / −1 pts` | all downstream of the same five constants. |
| Force Posture `82%` C-1/C-2 ready, `5` component commands, `4 packages`, `Peak COA demand 85%` | literals in `postureStats`, plus `Math.max(...buildCoas().map(c => c.res))`. |
| Claim-graph confidence 90/75/55/40/25/30 | a lookup on the first letter of the admiralty grade. |
| `Run R-0417`, `2 h ago`, `72 h from …` | literals; `New Run` is `'R-' + (400 + random·500)`. |

### Array-position identifiers

`p.assumption` (requirement → claim), `c.deps` (option → assumption),
`PROBLEM_SETS[failIdx]`, `pir: 1 + (len % 3)`, the `A${i + 1}` claim labels, and
`planSel`. Insert or reorder one assumption and every requirement silently
re-points.

### Scenario identity

The UI's fictional universe is Olvana / Khorathidin / Sungzon / North Torbia /
Operation ENDURING PHOENIX / UNSCR 2781. **Meridian Sea appears nowhere in it.**
Add Meridian Sea as a separate dataset-backed scenario; do not merge the two.

Also: no Army-published adversary model is cited anywhere in the artifact — no
`TC 7-100`, no `ATP 7-100.x`, no `FM`, no `ADP`. The nearest thing is the
free-text phrase "DIA-model adversary" in `THREATS.OLV.desc`. Real citations
(CJCSI 3100.01F, JP 5-0, CJCSM 3105.01, JP 2-01.3, JP 2-0) are used as labels
only, and fictional documents (UNSCR 2781, OPORD 26-002, WARNORD 26-001) are
rendered in the same visual register as real ones. That needs visibly different
treatment before any demo.
