"""Fixtures for the AMBER SHIELD scenario package.

These tests read the frozen dataset's models, invariants and reference evaluator and never write
to `dataset/`. The scenario is assembled and recomputed once per session.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.scenarios.amber_shield import build as build_module  # noqa: E402
from app.scenarios.amber_shield import corpus_docs as corpus_module  # noqa: E402
from app.scenarios.amber_shield import payoffs as payoffs_module  # noqa: E402
from app.scenarios.amber_shield import placeholders as rows_module  # noqa: E402
from app.scenarios.amber_shield import scenario as scenario_module  # noqa: E402
from app.scenarios.amber_shield._dataset import DATASET_DIR, eval_module, gen_module  # noqa: E402



@pytest.fixture(scope="session")
def build():
    return build_module


@pytest.fixture(scope="session")
def S():
    return scenario_module


@pytest.fixture(scope="session")
def P():
    return payoffs_module


@pytest.fixture(scope="session")
def rows():
    """`placeholders`: the claim, risk and collection rows derived from evidence."""
    return rows_module


@pytest.fixture(scope="session")
def corpus():
    return corpus_module


@pytest.fixture(scope="session")
def validate():
    return gen_module("validate")


@pytest.fixture(scope="session")
def models():
    return gen_module("models")


@pytest.fixture(scope="session")
def engine():
    return eval_module("engine")


@pytest.fixture(scope="session")
def value():
    return eval_module("value")


@pytest.fixture(scope="session")
def claimset():
    return eval_module("claimset")


@pytest.fixture(scope="session")
def dataset_dir() -> Path:
    return DATASET_DIR


@pytest.fixture(scope="session")
def scenario_root() -> Path:
    """`sources.path` is relative to the scenario package, not to `dataset/`; the corpus-reading
    invariants (02, 11-13, 15-17, 20) resolve document paths against this."""
    return build_module.ROOT


@pytest.fixture(scope="session")
def authored() -> dict:
    """Authored rows, model-validated, before recompute."""
    return build_module.tables()


@pytest.fixture(scope="session")
def computed() -> dict:
    """Authored rows with every COMPUTED column filled by eval/engine.py::recompute."""
    return build_module.load()


@pytest.fixture(scope="session")
def blue(computed) -> list[dict]:
    """The five Blue courses of action, in the UI's order."""
    order = [c[0] for c in scenario_module.COAS]
    rows = {s["strategy_id"]: s for s in computed["strategies"] if s["actor_id"] == scenario_module.BLUE}
    return [rows[sid] for sid in order]


@pytest.fixture(scope="session")
def ui_js() -> str:
    return (REPO_ROOT / "app" / "ui" / "src" / "app.logic.js").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def opord_text() -> str:
    path = REPO_ROOT / "docs" / "demo" / "USEUCOM_OPORD_26-004_AMBER_SHIELD.txt"
    return " ".join(path.read_text(encoding="utf-8").split())
