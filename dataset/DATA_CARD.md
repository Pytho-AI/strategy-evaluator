# strategy-evaluation-dataset-pytho

## Description

A deterministic synthetic corpus and relational truth set for testing claim extraction, collection management, interconnected risk assessment, and strategy option evaluation. It contains a fictional theater, dated claims, structured decision data, three update batches, and reference scoring code.

## Use cases

- Foundational Data Ingestion: extract sourced, dated claims from mixed document types.
- Collection Management: rank information gaps and close requirements when new reporting arrives.
- Interconnected Risk: compute JRAM-aligned risk statements, cascades, and trends.
- Strategy Option Evaluation: test validity, expected value, sensitivity, robustness, and value of information.

## Size

The base release contains 92 documents, 864 claims, 122 entities, 9 strategies, 66 worlds. Counts include the three inject batches. Shipped extensions are `rag_qa`, `target_systems`, `capability`, `authority`, `collection_assets`, and the optional `events` layer with 600 records.

## Schema summary

The normalized tables, keys, constraints, computed fields, and formulas are defined in [schema/SCHEMA.md](schema/SCHEMA.md).

## Generation method

The generator builds structured truth first with seed 20260908, then renders deterministic templates and locates each evidence span in the rendered text. No language model was used to render this release. Controlled perturbations include paraphrase, aliases, unit drift, stale echoes, implication, distractors, typographic noise, and one proposed contradiction. IDs remain stable when regenerated with the same seed.

## Ground truth

Facts describe the scenario state. Claims link source spans to those facts. Computed strategy, risk, and collection fields can be reproduced with `eval/engine.py`. Inject manifests record expected changes between adjacent world versions.

All content is fictional. No real persons, polities, organizations, or systems.

## License

CC BY 4.0. The synthetic scenario and generated content are team-authored. Doctrine remains subject to its source terms.

## Known limitations

The dataset uses a finite payoff tensor, one fictional theater, four dated world states, and template-rendered prose. It does not simulate transition dynamics beyond the payoff tensor. The offline baseline is a literal-surface proxy, not a language-model benchmark. A live LLM baseline was not run because `ANTHROPIC_API_KEY` was unavailable.

## Evaluation

Run `make check` from the repository root. Truth scored against itself is 1.0. The measured offline literal-surface proxy has extraction F1 0.008210 and style compliance 0.000000. See [eval/README.md](eval/README.md).

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
