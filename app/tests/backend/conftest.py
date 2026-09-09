"""Shared fixtures. The dataset is a frozen contract: these tests only read it."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATASET_DIR = REPO_ROOT / "dataset"

from fastapi.testclient import TestClient  # noqa: E402

from app.backend.adapter import DatasetAdapter  # noqa: E402
from app.backend.main import create_app  # noqa: E402


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
