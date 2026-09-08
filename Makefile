PY ?= .venv/bin/python
SEED ?= 20260908

.PHONY: check gen test schema acronyms extracts clean

# One command: schema load, invariants, eval truth-vs-truth, reproducibility diff, denylist grep.
check:
	@cd dataset && ../$(PY) -m gen check --seed $(SEED)

gen:
	@cd dataset && ../$(PY) -m gen --seed $(SEED)

test:
	@$(PY) -m pytest -q tests

schema:
	@cd dataset && ../$(PY) -m gen schema

acronyms:
	@cd dataset && ../$(PY) -m gen.styles.build_acronyms

clean:
	@rm -rf dataset/truth/*.jsonl dataset/corpus/* dataset/injects/batch_*
