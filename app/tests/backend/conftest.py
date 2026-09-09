"""Shared fixtures. The dataset is a frozen contract: these tests only read it."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATASET_DIR = REPO_ROOT / "dataset"

# Product workspaces go to a throwaway directory for the whole run, so the tests never touch
# the developer's own app/workspace/. Set before the app is imported: the store reads it per
# call, but this keeps the intent obvious.
_WORKSPACES = tempfile.mkdtemp(prefix="strategy-workbench-workspaces-")
os.environ["STRATEGY_WORKSPACE_DIR"] = _WORKSPACES

from fastapi.testclient import TestClient  # noqa: E402

from app.backend.adapter import DatasetAdapter, eval_module  # noqa: E402
from app.backend.main import create_app  # noqa: E402

# Puts dataset/ on sys.path the one supported way, so a test can import the reference
# evaluator directly (`from eval.engine import recompute`) and use it as an oracle.
eval_module("tables")


def hash_tree(root: Path) -> dict[str, str]:
    """SHA-256 of every file under root, keyed by relative path."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        out[str(path.relative_to(root))] = digest.hexdigest()
    return out


@pytest.fixture(scope="session", autouse=True)
def dataset_hashes_before() -> dict[str, str]:
    """Hash dataset/ before the run; re-check it after the last test."""
    before = hash_tree(DATASET_DIR)
    yield before
    after = hash_tree(DATASET_DIR)
    assert after == before, (
        "the test run modified dataset/: "
        f"{sorted(set(before) ^ set(after)) or [k for k in before if before[k] != after.get(k)]}"
    )


@pytest.fixture(scope="session", autouse=True)
def workspace_root() -> Path:
    """Where product workspaces live during the run; removed afterwards."""
    root = Path(_WORKSPACES)
    yield root
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def workspace_id(request) -> str:
    """A workspace of this test's own, so tests never see each other's product state."""
    from app.backend.product.overlay import clear_cache
    from app.backend.product.store import Workspace

    import re

    name = re.sub(r"[^A-Za-z0-9_-]", "_", "ws_" + request.node.name)[:64]
    Workspace(name).reset()
    clear_cache()
    return name


@pytest.fixture(scope="session")
def adapter() -> DatasetAdapter:
    return DatasetAdapter()


@pytest.fixture(scope="session")
def client(adapter: DatasetAdapter) -> TestClient:
    return TestClient(create_app(adapter))


@pytest.fixture(scope="session")
def manifests() -> dict[int, dict]:
    """The inject manifests, read straight from the dataset, used as the test oracle."""
    return {
        batch: json.loads(
            (DATASET_DIR / "injects" / f"batch_{batch}" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        for batch in (1, 2, 3)
    }


@pytest.fixture
def dataset_copy(tmp_path: Path) -> Path:
    """A temp copy of the parts of dataset/ the adapter's preflight reads."""
    root = tmp_path / "dataset"
    root.mkdir()
    for sub in ("schema", "truth", "injects"):
        shutil.copytree(DATASET_DIR / sub, root / sub)
    return root
