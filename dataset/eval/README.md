# Evaluation

Run from `dataset/`:

```sh
python -m gen check --seed 20260908
pytest ../tests/test_p6.py
```

A perfect result has precision, recall, F1, temporal accuracy, effect exact-match, and ranking correlation equal to 1.0, with no style violations.

The measured offline literal-surface proxy processed 92 documents. Its extraction precision is 0.014124, recall is 0.005787, F1 is 0.008210, and style compliance is 0.000000. It recognizes literal surface mentions, uses publication dates, and omits likelihood, confidence, and supersession handling.

`python -m eval.run_llm_baseline --model MODEL` runs the one-call-per-document naive LLM baseline. It was not run for this release because `ANTHROPIC_API_KEY` was unavailable. No live result is claimed.

License: CC BY 4.0.
