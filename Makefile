PY ?= .venv/bin/python
SEED ?= 20260908

.PHONY: check gen test schema acronyms extracts clean app-test app-run

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

# ---------------------------------------------------------------- app (backend)
app-test:
	@$(PY) -m pytest -q app/tests

app-run:
	@$(PY) -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8765

# ---------------------------------------------------------------- container / deploy
image:
	@docker build -t strategy-evaluation-workbench:latest .

image-run:
	@docker rm -f strategy-workbench >/dev/null 2>&1 || true
	@docker run -d --name strategy-workbench -p $${HOST_PORT:-8790}:8765 -v workbench-state:/data strategy-evaluation-workbench:latest
	@echo "http://127.0.0.1:$${HOST_PORT:-8790}/"

deploy-ec2:
	@./deploy/deploy-ec2.sh
