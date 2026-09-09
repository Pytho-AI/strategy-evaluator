# UI recovery — provenance and procedure

The operator workbench under `app/ui/` is not new code. It was recovered from a
single supplied artifact, a `__bundler` HTML export:

```
/Users/akshay/Downloads/Stratistics Wargaming System.html
sha256  0d8e9e477aaac8213d0987f52c82468fa2753fa2b377c6aa743e5dd51c1aebed
bytes   1,118,147   (384 lines)
```

That file is the source of truth and is never modified. `app/tests/ui/conftest.py`
copies it out, serves the copy, and asserts the digest before and after the run.

Inside it: four `<script type="__bundler/*">` islands — `manifest`,
`ext_resources`, `page_order` and a JSON-encoded `template`. The template is
190,759 bytes (sha256 `d2d2b039ce2a6c12350e316bae360433c48e79013b062fb7f138366e15865c59`)
and every asset is a base64 (mostly gzipped) blob in the manifest. 38 resources
in total: 28 in the root bundle, 10 more inside the nested JIPOE map page, which
is itself a complete `__bundler` export.

## Step 1 — decode the bundle as data

`tools/extract.py` reads the four islands, base64-decodes and gunzips every
manifest entry, writes each one out with its hash, splits the template's inline
`<script>`/`<style>` islands into files, and recurses into any decoded resource
that is itself a bundle. **Nothing from the artifact is executed.**

```sh
python3 app/ui/tools/extract.py \
  "$HOME/Downloads/Stratistics Wargaming System.html" \
  /tmp/ui-decoded
```

Output:

```
/tmp/ui-decoded/
  manifest.inventory.json      per-resource uuid, mime, byte count, sha256
  template.raw.html            the template as shipped (uuid references intact)
  template.resolved.html       the same, uuids rewritten to resources/<file>
  resources/                   28 decoded root resources
  template_parts/
    markup.html                the <x-dc> body, helmet and logic script removed
    inline_01.js               class Component extends DCLogic (445 lines)
    inline_01.css              Industry design-system tokens + Barlow @font-face
    inline_02.css              Source Sans 3 @font-face
    inline_03.css              the app's dark-theme overrides
  jipoeMap/                    the nested bundle, same shape, 10 resources
```

Verified reproducible: re-running `extract.py` on the original produces a tree
byte-identical to the precheck's (`/tmp/precheck/ui/decoded/`) apart from the
absolute `source` path recorded inside `manifest.inventory.json`.

## Step 2 — lay the decoded tree out as static source

`tools/lay_out_source.py` does only mechanical work: it moves files to their
final names and rewrites resource references (uuid → relative path). It changes
no markup and no logic.

```sh
python3 app/ui/tools/lay_out_source.py /tmp/ui-decoded /tmp/ui-staged
```

What it decides:

* fonts are renamed from their uuids using the `@font-face` block that
  references them — `barlow-500-latin-ext.woff2`,
  `source-sans-3-cyrillic.woff2`. Source Sans 3 declares weights 400/500/600/700
  over the same seven subset files, so the weight is dropped from those names;
* the three `<style>` islands become `src/styles/01…03-*.css`, byte-identical
  apart from `url("<uuid>")` → `url("../../assets/fonts/<name>.woff2")`;
* `template_parts/markup.html` → `src/app.dc.html`, `inline_01.js` →
  `src/app.logic.js` (its `// type=text/x-dc` marker line dropped), and the
  `data-props` attribute → `src/app.props.json`;
* the nested JIPOE bundle is un-bundled in place into `assets/jipoe-map/`, its
  `template.raw.html` becoming `index.html` with the same uuid → path rewrite.
  The two script tags keep their original SRI hashes and still validate.

`app/ui/` is that output plus the seven hand edits in step 3 and the five new
files in step 4. To see exactly which files carry a hand edit:

```sh
python3 app/ui/tools/lay_out_source.py /tmp/ui-decoded /tmp/ui-staged
diff -r /tmp/ui-staged app/ui        # ignore the new files listed in step 4
```

## Step 3 — the seven hand edits

Everything the artifact needed `window.__resources` for was a blob URL standing
in for a file path. Each call site already carried the relative-path fallback
the source tree used before bundling; these edits restore it. Nothing else in
the recovered markup or logic changed — no relabelling, no restyling, no
handler rewrites. (P2 does that work; see `app/ui/README.md`.)

| # | File | Change | Why |
|---|---|---|---|
| 1 | `src/app.logic.js` l.74 | `await import((window.__resources && window.__resources.docreader) \|\| './docreader.js')` → `await import('./assets/docreader.js')` | drop the blob lookup; `docreader.js` is a real file again |
| 2 | `src/app.logic.js` l.412 | `mapSrc: (window.__resources && …jipoeMap + '#threat=' : './jipoe-map.html?threat=') + …` → `mapSrc: './assets/jipoe-map/index.html?threat=' + encodeURIComponent(T.name)` | same; the map page reads `location.search` before `location.hash`, so the query form is native |
| 3 | `src/app.logic.js` l.320 | `const B = window.BRANDING;` and `brandMark / brandTitle / brandProduct` added to the object `renderVals()` returns | branding indirection |
| 4 | `src/app.dc.html` l.724 | `<iframe src="{{ mapSrc }}">` → `<iframe sc-camel-src="{{ mapSrc }}">` | fixes `GET /%7B%7B%20mapSrc%20%7D%7D → 404`. The browser parses the template before dc-runtime binds it and fired one request for the literal string. `sc-camel-src` is not an HTML attribute, so nothing is requested; dc-runtime maps `sc-camel-<kebab>` back to the `src` prop when it compiles |
| 5 | `src/app.dc.html` l.9 | `【Pytho】` → `{{ brandMark }}` | branding indirection |
| 6 | `src/app.dc.html` l.53 | `Strategy Adjudicator` → `{{ brandTitle }}` | branding indirection |
| 7 | `assets/jipoe-map/index.html` l.203 | `fetch((window.__resources && …worldAtlas) \|\| 'https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json')` → `fetch('./data/countries-110m.json')` | serve the basemap locally; the page stays offline |

## Step 4 — the five new files

| File | Purpose |
|---|---|
| `index.html` | Entry page. Links the three stylesheets, loads the pinned React UMD bundles and the `@ds-bundle` stub, carries the `UNCLASSIFIED — SYNTHETIC` marking and an empty `<x-dc>` mount point. |
| `src/boot.js` | Replaces the bundler's boot script. Fetches `app.dc.html`, `app.logic.js` and `app.props.json`, puts them in the document the way dc-runtime expects (`<x-dc>` + `<script type="text/x-dc" data-dc-script>`), then loads `vendor/dc-runtime.js`, which self-boots and mounts. |
| `src/branding.js` | The `BRANDING` object — the only place product/team naming lives. |
| `tools/extract.py` | Step 1, kept as the provenance record. Copied from the precheck; the only change is that the output directory is now a required argument. |
| `tools/lay_out_source.py` | Step 2. |

`dc-runtime` still refetches `index.html` once at boot (it does that whenever
`window.__resources` is absent, to pick up an unmodified template). `index.html`
holds an empty `<x-dc></x-dc>`, so the refetch parses an empty template and is
correctly ignored. It is a 200, not an error.

## Step 5 — verify against the original

```sh
.venv/bin/python -m pytest -q app/tests/ui
```

`app/tests/ui/test_ui_recovery.py` serves `app/ui/` and a scratch copy of the
original on two free ports and drives both with Playwright at 1440x900. It
asserts the artifact's digest, zero page-origin console errors, zero failed or
4xx responses (the map iframe included), identical headings and identical
`#dc-root` text across all nine nav entries, and that `runSim`, the collection
`cycle` control and manual `ingest` still run. Screenshots land in
`app/tests/ui/screenshots/`.

## Resource inventory

38 resources, all decoded from the manifest as data. Byte counts and digests are
of the decoded content and are unchanged by the move.

| bundle | id in manifest | kind | bytes | sha256 | destination under `app/ui/` | what it is |
|---|---|---|---|---|---|---|
| jipoe-map | `worldAtlas` | data | 107761 | `2516c915867c7baf18ddec727aec46c315541a07cfb3d79a6559b05d5e94eee8` | `assets/jipoe-map/data/countries-110m.json` | world-atlas@2.0.2 countries-110m TopoJSON basemap for the JIPOE map. |
| jipoe-map | `566e3032-2fec-4ba6-bd4f-1fcb161057d9` | font | 10684 | `ce21e07f81120c29845d627644a977b85027fc564b68e23349ea599402e55e96` | `assets/jipoe-map/fonts/source-sans-3-cyrillic-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `a934a6a3-5fc8-44e2-b402-6c6789d236b3` | font | 18400 | `44aa5fb37c5aa2a2b44ceab9c077b42de47d50d47c0dcbefa2555082c38df8dd` | `assets/jipoe-map/fonts/source-sans-3-cyrillic.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `afc07d5d-c42e-4c48-a625-d7eb75eeda3d` | font | 9796 | `cd19f948c227b68e6feb8af39da356315dd47f8bd1406cc8bab78baf2c6ea85e` | `assets/jipoe-map/fonts/source-sans-3-greek-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `9054035c-1a3d-47bb-aad0-231bc0b3f118` | font | 14580 | `5045881eda8b85134f65682ac27163c2b060d1aeed619e21498f98f5448239d1` | `assets/jipoe-map/fonts/source-sans-3-greek.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `310d2b51-a414-41fd-99b4-8d1f3c5ef6af` | font | 60048 | `ed3571ea9ff752f1c846f1c9ad2b0006de42f478a2db9163a74db0729a4eb281` | `assets/jipoe-map/fonts/source-sans-3-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `b891d413-afa1-44c5-9609-bbf6e4c34aae` | font | 28792 | `ac057a5593cbe3df0d2585da5dd5f33b8efa84aa30550c710fe061b37fc5c54b` | `assets/jipoe-map/fonts/source-sans-3-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `71c92192-73a4-4981-baa5-524e24dcb160` | font | 10336 | `7a9ba93945d3cd9e6c2ad459d242c2281b423dd305e3ccb9956279f12deddfd3` | `assets/jipoe-map/fonts/source-sans-3-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| jipoe-map | `8b0e78de-c63a-489c-86ac-7c90c33725a0` | script | 279706 | `f2094bbf6141b359722c4fe454eb6c4b0f0e42cc10cc7af921fc158fceb86539` | `assets/jipoe-map/vendor/d3.v7.9.0.min.js` | d3 v7.9.0 (map bundle), loaded with its original SRI hash. |
| jipoe-map | `e498e85a-cd1a-4d2d-8cd4-67e0724d9b6e` | script | 7169 | `25cd02ae486cc5063e0215a4e4cfb15de83700c87ac48bac4d57dc6aaf3ebb89` | `assets/jipoe-map/vendor/topojson-client.v3.1.0.min.js` | topojson-client v3.1.0 (map bundle), loaded with its original SRI hash. |
| root | `docreader` | script | 4508 | `2de8523176fb413fa3ced69ea513858ab3f779394c0ce91fc39d202cf1ea2858` | `assets/docreader.js` | ES module: `.docx` unzip via `DecompressionStream('deflate-raw')` + `<w:t>` run extraction, `.txt`/`.md`/`.json`, `.pdf` via CDN pdf-parse, `extractPlan()`, `signalIndex()`. Imported dynamically by `loadDocs()`. |
| root | `26de9cf9-fe29-4129-b490-7dd53bf023b5` | font | 9632 | `bac411df68fa3d93ee4b12309c4df075c791d0390b536ca8d803890f889b76b4` | `assets/fonts/barlow-400-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `432b825d-6228-4c9b-b5f9-7b066de7c2d7` | font | 15656 | `7a686e76312866b7d506c103e51a829d4c96a0b4576835128d3b7b53801c095a` | `assets/fonts/barlow-400-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `ca71039e-0c9f-4d4a-88e5-5dffd48e80b9` | font | 4624 | `3dd62fbbcd748024be8d57b0d9d72c0d38b07b35024daad7f108c4f348c34fdc` | `assets/fonts/barlow-400-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `f8c26eba-bfae-4c8a-94b8-02b9497e9d48` | font | 9712 | `7985f1abf1d07b81181090dffaa1f7c3dde03eaa524d41e5bebd39ea5d3090de` | `assets/fonts/barlow-500-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `d7e4764e-b2d4-45c0-92b5-919f3e1c0325` | font | 15640 | `80e7dc5605dd451bb9b092d7f46704f08bf39d2866cb981aa8caddc016716aed` | `assets/fonts/barlow-500-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `4b67f1e4-3fdf-4693-ba2e-0df4c5b3ab9b` | font | 4764 | `2e9076077ee0824f953a795d32ba020651bf1b55d8d981b1b94c12fa03a95d8b` | `assets/fonts/barlow-500-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `b60e7579-f95b-4466-9414-64cd3f97bf99` | font | 9888 | `2b0e32435d0c87bc0d68f2522c6a7dceb8a2ac9cd0f8d9df7e5c162f778416c4` | `assets/fonts/barlow-700-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `7802800e-aee0-4d5b-b8c9-b9c9f012f474` | font | 15744 | `98aa8b5c2582107d73a6f1254f08b152b0c037ae5626a902dd44af8c781e0e6d` | `assets/fonts/barlow-700-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `44a70272-4a21-4979-b9db-5c6311aae84d` | font | 4796 | `892f58db77d3cf09ac112950ed83544d73b6bb1e1b528958eeef38980c1404ef` | `assets/fonts/barlow-700-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `458095f4-36db-454c-9b0a-7ecc2832b091` | font | 9264 | `ed8618e86bffee6caa69d0aa5c08339fa886d878962444348b09b2e5ec2d516c` | `assets/fonts/barlow-condensed-400-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `45011496-177f-4082-8918-dbd05abd0a9a` | font | 14672 | `0e2a408159b32d8105bcd1a0a4d6222fcee375a84fb62703c614ce34d8bb68bb` | `assets/fonts/barlow-condensed-400-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `d874f6f6-72e9-458e-9930-f4e0401b061a` | font | 4560 | `bc42ba6f77ac0be14c84afea284154ce761c7c0b8e4bb0b896bc0b606adedc88` | `assets/fonts/barlow-condensed-400-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `1f366bea-f958-44fd-88fb-bccd1b02339d` | font | 9236 | `a2f92ada1d0eaf10dd83b11392ea389c039aa78f6e17418fc062c23f0ba78438` | `assets/fonts/barlow-condensed-600-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `9fa5a098-1125-4ada-9c77-0062f095fde1` | font | 14844 | `5bc49d41f32810a114765314392332ce2acae2276635eee265a50319a12c1b49` | `assets/fonts/barlow-condensed-600-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `15c099a9-eda2-49e9-abb4-19ef6fd2189f` | font | 4628 | `50c25f3210bca008b36809e4f3f964fc4acab82e07a27d099b14c378ea58bf5b` | `assets/fonts/barlow-condensed-600-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `44fef992-ddf0-4b50-b57a-35f275be3129` | font | 10684 | `ce21e07f81120c29845d627644a977b85027fc564b68e23349ea599402e55e96` | `assets/fonts/source-sans-3-cyrillic-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `1c156018-6106-4d24-ae74-511b2f624cff` | font | 18400 | `44aa5fb37c5aa2a2b44ceab9c077b42de47d50d47c0dcbefa2555082c38df8dd` | `assets/fonts/source-sans-3-cyrillic.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `3beb99e6-9564-45c6-99e5-4c651e5546fa` | font | 9796 | `cd19f948c227b68e6feb8af39da356315dd47f8bd1406cc8bab78baf2c6ea85e` | `assets/fonts/source-sans-3-greek-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `8fa01e5d-9290-4774-995e-73f37d194e40` | font | 14580 | `5045881eda8b85134f65682ac27163c2b060d1aeed619e21498f98f5448239d1` | `assets/fonts/source-sans-3-greek.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `5528ec99-abd1-4c16-be8a-c8503d4b5964` | font | 60048 | `ed3571ea9ff752f1c846f1c9ad2b0006de42f478a2db9163a74db0729a4eb281` | `assets/fonts/source-sans-3-latin-ext.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `f88b8523-9e08-4452-99e7-088d355948cd` | font | 28792 | `ac057a5593cbe3df0d2585da5dd5f33b8efa84aa30550c710fe061b37fc5c54b` | `assets/fonts/source-sans-3-latin.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `e53f5099-d1a6-49f4-bab4-04a06556b230` | font | 10336 | `7a9ba93945d3cd9e6c2ad459d242c2281b423dd305e3ccb9956279f12deddfd3` | `assets/fonts/source-sans-3-vietnamese.woff2` | Self-hosted webfont subset; named from the `@font-face` family/weight/unicode-range block that references it. |
| root | `jipoeMap` | page | 418697 | `0c28a49e872d2a6301700d38046fa7858248a02b95fb9c5be35e71e708b3544f` | `assets/jipoe-map/index.html` | Nested `__bundler` HTML page — the d3 JIPOE overlay loaded in an iframe. Un-bundled in place by `tools/lay_out_source.py`; its own 10 resources are the rows below. |
| root | `15a49b3a-6d16-4e96-8400-6eb1bcf2e0f0` | script | 69150 | `8fe7df74405f3c55f49b7249c74ea1397e65d07dea2b1bd3b4a489bec2e28cbe` | `vendor/dc-runtime.js` | dc-runtime bundle — template compiler, `DCLogic`/`StreamableLogic` base class, React bootstrap. Header says GENERATED from `dc-runtime/src/*.ts` (`bun run build`); the source was not shipped. Vendored, never hand-edited. |
| root | `97ceecaa-8d01-4f91-bc09-d72e05f0d4b6` | script | 300 | `7d1ad60da19d57381ba6fc862d52a5501a2038938d13037f3e6e0f751b5e678d` | `vendor/ds-bundle-industry.js` | `@ds-bundle` stub declaring design-system namespace `Industry_indust` with zero components. A no-op; kept because the artifact shipped it. |
| root | `https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js` | script | 131835 | `35f4f974f4b2bcd44da73963347f8952e341f83909e4498227d4e26b98f66f0d` | `vendor/react-dom.production.min.js` | ReactDOM 18.3.1 UMD, pinned. Same. |
| root | `https://unpkg.com/react@18.3.1/umd/react.production.min.js` | script | 10751 | `d949f1c3687aedadcedac85261865f29b17cd273997e7f6b2bfc53b2f9d4c4dd` | `vendor/react.production.min.js` | React 18.3.1 UMD, pinned. Loaded by `index.html` so dc-runtime `loadReactUmd()` short-circuits and no CDN is contacted. |

## v3 recovery — 09 September 2026

Source artifact: `~/Downloads/Stratistics Wargaming System-v3.html`
SHA-256 `862e0e94a852cf4276213804e13f12ad6e4d06eb1c79cc1710aad7f2d92e5f02`, 1,138,702 bytes.

Reproduce:

```sh
.venv/bin/python app/ui/tools/extract.py "~/Downloads/Stratistics Wargaming System-v3.html" /tmp/v3
.venv/bin/python app/ui/tools/lay_out_source.py /tmp/v3 /tmp/v3-staged
```

`tools/lay_out_source.py` gained the v3 resource uuids (dc-runtime `e4442ba4`, react
`67de73d8`, react-dom `afe94f78`, ds-bundle `fb9a67ac`, docreader `d86d631a`; map bundle
d3 `5f0251e3`, topojson `a818376d`, world atlas `dc61f461`). Four hand edits on top of its
output, the same ones the earlier recovery needed:

| File | Change |
|---|---|
| `src/app.logic.js` l.82 | docreader import → `'./assets/docreader.js'` |
| `src/app.logic.js` l.484 | `mapSrc` blob lookup → `'./assets/jipoe-map/index.html?threat='` |
| `src/app.dc.html` l.253 | `<iframe src="{{ mapSrc }}">` → `sc-camel-src` (kills the `{{ mapSrc }}` 404) |
| `assets/jipoe-map/index.html` l.203 | world-atlas CDN fetch → `'./data/countries-110m.json'` |

`index.html` and `src/boot.js` are recovery scaffolding, not artifact code: they load the
three style islands, the pinned React 18.3.1 UMD bundles, the template and the logic, then
dc-runtime. The classification pill is added by `index.html`.

**Scenario note.** v3 carries its own scenario (USEUCOM OPORD 26-004, Operation Amber Shield,
Baltic/Russia) with hard-coded demo data. It is not the Meridian Sea dataset. Nothing on these
screens is API-backed. The API-backed workbench built against the dataset is preserved at
`app/ui-wired/` and served at `/wired/`.
