"""Load the base dataset and optional extensions as pandas DataFrames."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd


DATASET_DIR = Path(__file__).resolve().parent


def _rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _manifest(root: Path, batch: int) -> dict:
    path = root / "injects" / f"batch_{batch}" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _cutoff(root: Path, through_batch: int) -> date:
    if through_batch == 0:
        return date(2026, 9, 8)
    return date.fromisoformat(_manifest(root, through_batch)["as_of"])


def _apply_closed_requirements(tables: dict[str, list[dict]], root: Path, through_batch: int) -> None:
    claims = tables["claims"]
    sources = {row["source_id"]: row for row in tables["sources"]}
    requirements = {row["req_id"]: row for row in tables["collection_requirements"]}
    for batch in range(1, through_batch + 1):
        manifest = _manifest(root, batch)
        for req_id in manifest["expected_effects"]["requirements_closed"]:
            req = requirements.get(req_id)
            if req is None:
                continue
            candidates = [
                claim for claim in claims
                if claim["subject_id"] == req["subject_id"]
                and claim["predicate"] == req["predicate"]
                and sources[claim["source_id"]]["batch"] == batch
                and claim["status"] == "approved"
            ]
            if candidates:
                req["status"] = "satisfaction"
                req["answered_by_source_id"] = candidates[0]["source_id"]


def _load_from(
    root: Path,
    *,
    base: bool = True,
    extensions: list[str] | None = None,
    through_batch: int = 0,
) -> dict[str, pd.DataFrame]:
    """Load a dataset directory. ``through_batch`` accepts 0, 1, 2, or 3."""
    root = Path(root)
    if through_batch not in range(4):
        raise ValueError("through_batch must be 0, 1, 2, or 3")
    selected = extensions or []
    tables: dict[str, list[dict]] = {}

    if base:
        dataset_path = str(Path(__file__).resolve().parent)
        if dataset_path not in sys.path:
            sys.path.insert(0, dataset_path)
        from eval.engine import recompute
        from eval.tables import TABLE_FILES

        tables = {name: _rows(root / "truth" / f"{name}.jsonl") for name in TABLE_FILES}
        tables["sources"] = [row for row in tables["sources"] if row["batch"] <= through_batch]
        source_ids = {row["source_id"] for row in tables["sources"]}
        tables["claims"] = [row for row in tables["claims"] if row["source_id"] in source_ids]
        tables["facts"] = [row for row in tables["facts"] if row["first_asserted_batch"] <= through_batch]
        cutoff = _cutoff(root, through_batch)
        tables["collection_requirements"] = [
            row for row in tables["collection_requirements"]
            if date.fromisoformat(row["created_at"]) <= cutoff
        ]
        _apply_closed_requirements(tables, root, through_batch)
        tables = recompute(tables, cutoff, through_batch)

    for extension in selected:
        truth = root / "extensions" / extension / "truth"
        if not truth.is_dir():
            raise ValueError(f"unknown extension: {extension}")
        for path in sorted(truth.glob("*.jsonl")):
            name = path.stem
            if name in tables:
                raise ValueError(f"extension table conflicts with base table: {name}")
            rows = _rows(path)
            if rows and "world_version" in rows[0]:
                rows = [row for row in rows if row["world_version"] <= through_batch]
            tables[name] = rows

    return {name: pd.DataFrame(rows) for name, rows in tables.items()}


def load(
    *,
    base: bool = True,
    extensions: list[str] | None = None,
    through_batch: int = 0,
) -> dict[str, pd.DataFrame]:
    """Load the packaged dataset from its installed directory."""
    return _load_from(
        DATASET_DIR,
        base=base,
        extensions=extensions,
        through_batch=through_batch,
    )
