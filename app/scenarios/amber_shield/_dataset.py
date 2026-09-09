"""The one supported way to import the frozen dataset's reference code.

`eval/` and `gen/` resolve only with the dataset package directory on sys.path (the same
bootstrap `app/backend/adapter.py::eval_module` uses). Nothing here writes to dataset/.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = REPO_ROOT / "dataset"


def _bootstrap() -> None:
    for path in (str(REPO_ROOT), str(DATASET_DIR)):
        if path not in sys.path:
            sys.path.insert(0, path)


def eval_module(name: str):
    """Import `eval.<name>` from the frozen dataset."""
    _bootstrap()
    return importlib.import_module(f"eval.{name}")


def gen_module(name: str):
    """Import `gen.<name>` from the frozen dataset."""
    _bootstrap()
    return importlib.import_module(f"gen.{name}")
