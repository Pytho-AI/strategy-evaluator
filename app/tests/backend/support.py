"""Helpers the backend tests share, in a module with a name of its own.

They do not live in ``conftest.py`` because ``conftest`` is not a unique module name across
the test tree: ``from conftest import ...`` breaks as soon as a second test directory with
its own ``conftest.py`` is collected in the same run.

The Meridian regression client is the main one.

The registry default is ``amber_shield`` whenever its package loads. Everything in this
directory except ``test_scenarios.py`` is a Meridian regression suite -- it asserts against
``dataset/``, the inject manifests and direct ``eval`` recomputation -- so the scenario it
exercises is named once, here, instead of in several hundred call sites.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_DIR = REPO_ROOT / "dataset"


def hash_tree(root: Path) -> dict[str, str]:
    """SHA-256 of every file under root, keyed by relative path."""
    out: dict[str, str] = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        out[str(path.relative_to(root))] = digest.hexdigest()
    return out


class MeridianClient(TestClient):
    """A TestClient that pins ``scenario=meridian`` on every ``/api/`` request.

    A request that already names a scenario is left alone, and so is a non-API path.
    """

    def request(self, method, url, **kwargs):  # noqa: D102 - httpx signature
        text = str(url)
        params = kwargs.get("params")
        if text.startswith("/api/"):
            if params is not None:
                # httpx replaces the URL query with ``params``, so the pin goes there.
                if isinstance(params, dict) and "scenario" not in params:
                    kwargs["params"] = {**params, "scenario": "meridian"}
            elif "scenario=" not in text:
                url = f"{text}{'&' if '?' in text else '?'}scenario=meridian"
        return super().request(method, url, **kwargs)
