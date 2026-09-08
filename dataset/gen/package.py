"""Write submission documentation, review samples, and a reproducible archive."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from eval.baseline import run_surface_baseline


NAME = "strategy-evaluation-dataset-pytho"
FICTION_NOTICE = "All content is fictional. No real persons, polities, organizations, or systems."
LICENSE_TEXT = """Creative Commons Attribution 4.0 International

The synthetic scenario, generated corpus, schemas, and team-authored code and documentation are
licensed under the Creative Commons Attribution 4.0 International License. You may share and adapt
the material for any purpose if you give appropriate credit, link to the license, and indicate
whether changes were made.

License text: https://creativecommons.org/licenses/by/4.0/legalcode

The cited doctrine source documents are not relicensed by this notice and remain subject to their
source terms.
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _counts(ctx) -> dict[str, int]:
    worlds = {row["world"] for row in ctx.tables["payoffs"]}
    return {
        "documents": len(ctx.tables["sources"]),
        "claims": len(ctx.tables["claims"]),
        "entities": len(ctx.tables["entities"]),
        "strategies": len(ctx.tables["strategies"]),
        "worlds": len(worlds),
    }


def _data_card(ctx, baseline: dict) -> str:
    counts = _counts(ctx)
    size = ", ".join(f"{value} {key}" for key, value in counts.items())
    extraction = baseline["extraction"]["overall"]
    return f"""# {NAME}

## Description

A deterministic synthetic corpus and relational truth set for testing claim extraction, collection management, interconnected risk assessment, and strategy option evaluation. It contains a fictional theater, dated claims, structured decision data, three update batches, and reference scoring code.

## Use cases

- Foundational Data Ingestion: extract sourced, dated claims from mixed document types.
- Collection Management: rank information gaps and close requirements when new reporting arrives.
- Interconnected Risk: compute JRAM-aligned risk statements, cascades, and trends.
- Strategy Option Evaluation: test validity, expected value, sensitivity, robustness, and value of information.

## Size

The base release contains {size}. Counts include the three inject batches. Shipped extensions are `rag_qa`, `target_systems`, `capability`, `authority`, `collection_assets`, and the optional `events` layer with 600 records.

## Schema summary

The normalized tables, keys, constraints, computed fields, and formulas are defined in [schema/SCHEMA.md](schema/SCHEMA.md).

## Generation method

The generator builds structured truth first with seed 20260908, then renders deterministic templates and locates each evidence span in the rendered text. No language model was used to render this release. Controlled perturbations include paraphrase, aliases, unit drift, stale echoes, implication, distractors, typographic noise, and one proposed contradiction. IDs remain stable when regenerated with the same seed.

## Ground truth

Facts describe the scenario state. Claims link source spans to those facts. Computed strategy, risk, and collection fields can be reproduced with `eval/engine.py`. Inject manifests record expected changes between adjacent world versions.

{FICTION_NOTICE}

## License

CC BY 4.0. The synthetic scenario and generated content are team-authored. Doctrine remains subject to its source terms.

## Known limitations

The dataset uses a finite payoff tensor, one fictional theater, four dated world states, and template-rendered prose. It does not simulate transition dynamics beyond the payoff tensor. The offline baseline is a literal-surface proxy, not a language-model benchmark. A live LLM baseline was not run because `ANTHROPIC_API_KEY` was unavailable.

## Evaluation

Run `make check` from the repository root. Truth scored against itself is 1.0. The measured offline literal-surface proxy has extraction F1 {extraction['f1']:.6f} and style compliance {baseline['style_compliance']:.6f}. See [eval/README.md](eval/README.md).

## Doctrinal basis

- CJCSM 3105.01C, Joint Risk Analysis, 14 February 2025: Enclosures A–E and Figures 5, 6, 8, 11, 12, 19, 22, 23, 26, and 28.
- JP 5-0, Joint Planning, 1 December 2020: course-of-action development and comparison.
- CJCSI 3100.01F, Joint Strategic Planning System, 29 January 2024: time horizons and risk framing.
- JP 2-01, Joint and National Intelligence Support to Military Operations, 5 July 2017: Chapter III section 13 and Figure III-8.
- JP 3-60, Joint Targeting, 20 September 2024: target-system terms and characteristics.
- ICD 203, Analytic Standards, as reproduced in CJCSM 3105.01C Figure 19: likelihood and confidence language.

Short source extracts and page citations are in [doctrine/EXTRACTS.md](doctrine/EXTRACTS.md).

## Fidelity statement

The ICD 203 terms, JRAM probability and consequence levels, named risk levels, strategy validity tests, and product slots follow the cited sources. The risk-contour cell assignments are the team's reading of the centers of Figure 8 because that figure does not publish a cell table. Expected value, sensitivity, robustness, EVPI, and the noisy-OR cascade are computable dataset extensions; the doctrine does not prescribe those formulas.
"""


def _matrix() -> str:
    return """# Use case matrix

| Sponsor use case | Tables used | Eval | Status | Doctrinal basis |
|---|---|---:|---|---|
| Foundational Data Ingestion | sources, entities, claims, facts | Y | shipped | ICD 203 analytic standards |
| Collection Management | pirs, collection_requirements, assumptions, claims | Y | shipped | JP 2-01 Ch. III §13 and Fig. III-8 |
| Interconnected Risk | problem_sets, harmful_events, risk_drivers, risk_assessments, escalation_edges | Y | shipped | CJCSM 3105.01C Figs. 5, 6, 8, 11, 12, 22, 23, 26, 28 |
| Strategy Option Evaluation | games, strategies, payoffs, assumptions, objectives, resources | Y | shipped | JP 5-0 COA development and comparison |
| RAG Intelligence Service | questions | Y | shipped | ICD 203 and cited doctrine definitions |
| Target System Object Development | systems, target_system_components, system_members, system_links, target_characteristics | Y | shipped | JP 3-60 Ch. I and Glossary |
| Capability Assessment Visualization | capability_areas, capability_components, capability_scores | Y | shipped | Dataset computation |
| Mission Authority Broker | authority_tiers, action_authority, recommendation_authority, decision_log | Y | shipped | JRAM senior-leader risk communication |
| Dynamic Collection Resource Optimization | assets, asset_coverage, tasking_plan | Y | shipped | JP 2-01 collection management |
| Multi-INT Fusion | events | Y | shipped (optional) | Synthetic event streams |
"""


def _eval_readme(baseline: dict) -> str:
    score = baseline["extraction"]["overall"]
    return f"""# Evaluation

Run from `dataset/`:

```sh
python -m gen check --seed 20260908
pytest ../tests/test_p6.py
```

A perfect result has precision, recall, F1, temporal accuracy, effect exact-match, and ranking correlation equal to 1.0, with no style violations.

The measured offline literal-surface proxy processed {baseline['documents']} documents. Its extraction precision is {score['precision']:.6f}, recall is {score['recall']:.6f}, F1 is {score['f1']:.6f}, and style compliance is {baseline['style_compliance']:.6f}. It recognizes literal surface mentions, uses publication dates, and omits likelihood, confidence, and supersession handling.

`python -m eval.run_llm_baseline --model MODEL` runs the one-call-per-document naive LLM baseline. It was not run for this release because `ANTHROPIC_API_KEY` was unavailable. No live result is claimed.

License: CC BY 4.0.
"""


def _gen_readme() -> str:
    return """# Generator

Run `python -m gen --seed 20260908` from `dataset/`. The ordered stages build scaffold data, bitemporal facts, document plans, rendered claims, strategies, payoff tensors, dependencies, risks, collection requirements, doctrinal products, injects, and package files.

Each assumption has an `index_k`. Payoff rows enumerate every Boolean assumption world. `eval/value.py` computes the change in expected utility for assumption `k` by holding all other assumption probabilities fixed and comparing `theta_k = 1` with `theta_k = 0`; this difference is `delta_k`. EVPI compares the best expected strategy before and after observing that bit.

To list claims carried by stale-echo sources:

```python
from dataset import load
d = load()
sources = d["sources"]
sources = sources[sources["perturbations"].apply(lambda values: "stale_echo" in values)]
print(d["claims"].merge(sources[["source_id", "path"]], on="source_id"))
```

IDs and output bytes are stable for seed 20260908. License: CC BY 4.0.
"""


def _review_samples(ctx) -> None:
    root = ctx.dataset_dir
    claims_by_source: dict[str, list[dict]] = {}
    for claim in ctx.tables["claims"]:
        claims_by_source.setdefault(claim["source_id"], []).append(claim)
    selected: dict[str, dict] = {}
    for source in ctx.tables["sources"]:
        selected.setdefault(source["doc_type"], source)
    for doc_type, source in sorted(selected.items()):
        text = (root / source["path"]).read_text(encoding="utf-8")
        rows = ["| claim_id | subject | predicate | value | span |", "|---|---|---|---|---|"]
        for claim in claims_by_source.get(source["source_id"], []):
            value = claim.get("object_id") or claim.get("value")
            span = text[claim["span_start"]:claim["span_end"]].replace("|", "\\|").replace("\n", " ")
            rows.append(f"| {claim['claim_id']} | {claim['subject_id']} | {claim['predicate']} | {value} | {span} |")
        sample = f"# Review sample: {source['path']}\n\n{text.rstrip()}\n\n## Claims\n\n" + "\n".join(rows)
        _write(root / "review" / "samples" / f"{doc_type}_{source['source_id']}.md", sample)


def _archive(root: Path) -> None:
    archive = root / f"{NAME}.zip"
    files = [
        path for path in root.rglob("*")
        if path.is_file()
        and path != archive
        and "__pycache__" not in path.parts
        and path.name not in {".DS_Store"}
    ]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), (2026, 9, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(ctx) -> None:
    root = ctx.dataset_dir
    baseline = run_surface_baseline(ctx.tables, root)
    _write(root / "DATA_CARD.md", _data_card(ctx, baseline))
    _write(root / "USE_CASE_MATRIX.md", _matrix())
    _write(root / "eval" / "README.md", _eval_readme(baseline))
    _write(root / "gen" / "README.md", _gen_readme())
    _write(root / "LICENSE", LICENSE_TEXT)
    _review_samples(ctx)
    _archive(root)
