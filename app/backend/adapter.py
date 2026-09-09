"""Read-only adapter over the frozen dataset.

Every computed number in this module comes out of ``dataset.load(...)``, which runs
``dataset/eval/engine.py::recompute`` on each call. Nothing here reads ``truth/*.jsonl``
for a computed column, re-implements an eval formula, or writes to ``dataset/``.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from dataset import load as dataset_load
from dataset.loader import DATASET_DIR, _load_from

from .errors import DatasetMissing, SchemaIncompatible

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_NAME = "strategy-evaluation-dataset-pytho.zip"
BATCHES = (0, 1, 2, 3)

# The Blue player of the Meridian Sea scenario. These are dataset IDs, not values:
# every number attached to them is still computed by the loader.
BLUE_GAME_ID = "meridian"
BLUE_ACTOR_ID = "ent_blue"

VALIDITY_TESTS = ("suitable", "feasible", "acceptable", "distinguishable", "complete")


@dataclass(frozen=True)
class Shape:
    """What one schema property must still be for the API to read it.

    ``types`` is the exact set of JSON types the property may take once ``$ref`` and
    ``anyOf`` are flattened; ``enum`` is the exact value set, declared only where the
    product branches on it; ``properties`` recurses into nested objects.
    """

    types: tuple[str, ...]
    enum: tuple[str, ...] | None = None
    properties: dict[str, "Shape"] | None = None


_TEXT = Shape(("string",))
_COUNT = Shape(("integer",))
_NUMBER = Shape(("number",))
_LIST = Shape(("array",))
_MAYBE_NUMBER = Shape(("null", "number"))
_MAYBE_COUNT = Shape(("integer", "null"))
_MAYBE_LIST = Shape(("array", "null"))
_VALIDITY_RESULT = Shape(
    ("object",), properties={"pass": Shape(("boolean",)), "evidence": _TEXT}
)

# The shapes the API consumes, checked against dataset/schema/*.json before loading.
# Every entry is a field contracts.py or a route reads; nothing speculative. Risk levels
# reach the product only through problem_set_assessments.max_risk_level, so RiskLevel is
# pinned there rather than on risk_assessments, which no route reads yet.
REQUIRED_SHAPES: dict[str, dict[str, Shape]] = {
    "strategies": {
        "strategy_id": _TEXT,
        "game_id": _TEXT,
        "actor_id": _TEXT,
        "name": _TEXT,
        "status": Shape(
            ("null", "string"), enum=("infeasible", "invalid", "stale", "valid")
        ),
        "value": _MAYBE_NUMBER,
        "value_ci": _MAYBE_LIST,
        "robustness": _MAYBE_NUMBER,
        "validity": Shape(
            ("null", "object"),
            properties={name: _VALIDITY_RESULT for name in VALIDITY_TESTS},
        ),
    },
    "assumptions": {
        "assumption_id": _TEXT,
        "strategy_id": _TEXT,
        "index_k": _COUNT,
        "statement": _TEXT,
        "status": Shape(
            ("null", "string"), enum=("holds", "stale", "unknown", "violated")
        ),
        "p_holds": _MAYBE_NUMBER,
        "sensitivity": _MAYBE_NUMBER,
        "evpi": _MAYBE_NUMBER,
    },
    "problem_set_assessments": {
        "problem_set_id": _TEXT,
        "jsps_horizon": Shape(("string",), enum=("long", "mid", "near")),
        "max_risk_level": Shape(
            ("string",), enum=("high", "low", "moderate", "significant")
        ),
        "he_ids": _LIST,
        "aggregated_statement_text": _TEXT,
    },
    "collection_requirements": {
        "req_id": _TEXT,
        "status": Shape(
            ("string",),
            enum=("closed", "research", "satisfaction", "submission", "validation"),
        ),
        "priority": _MAYBE_NUMBER,
        "jipcl_rank": _MAYBE_COUNT,
    },
    "payoffs": {"strategy_id": _TEXT, "world": _TEXT},
    "strategy_objectives": {
        "strategy_id": _TEXT,
        "objective_id": _TEXT,
        "weight": _NUMBER,
    },
    "claims": {"claim_id": _TEXT, "source_id": _TEXT},
    "sources": {"source_id": _TEXT, "title": _TEXT, "path": _TEXT},
}

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    table: tuple(shapes) for table, shapes in REQUIRED_SHAPES.items()
}

REQUIRED_PRIMARY_KEYS: dict[str, list[str]] = {
    "strategies": ["strategy_id"],
    "assumptions": ["assumption_id"],
    "problem_set_assessments": ["problem_set_id", "jsps_horizon", "world_version"],
    "collection_requirements": ["req_id"],
    "payoffs": ["strategy_id", "opponent_strategy_id", "world"],
    "strategy_objectives": ["strategy_id", "objective_id"],
    "claims": ["claim_id"],
    "sources": ["source_id"],
}


def _clean(value: Any) -> Any:
    """pandas/numpy scalars and NaN out, plain JSON-able Python in."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return None if math.isnan(value) else value
    if isinstance(value, (int, str)):
        return value
    if hasattr(value, "item"):  # numpy / pandas scalar
        try:
            return _clean(value.item())
        except (ValueError, AttributeError):
            pass
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _records(frame: pd.DataFrame) -> list[dict]:
    return [{k: _clean(v) for k, v in row.items()} for row in frame.to_dict("records")]


@dataclass(frozen=True)
class DatasetIdentity:
    archive_sha256: str | None
    git_head: str | None
    key: str


@dataclass(frozen=True)
class BatchSnapshot:
    """One batch, cached under (dataset identity, batch).

    The cache owns ``_tables``; callers own what they are handed. Every accessor
    returns a deep copy, so mutating a response cannot change a later one. The whole
    table set copies in about 9 ms (4 ms of it the 864 claims) against the 2 s budget.
    """

    batch: int
    as_of: str
    load_ms: float
    _tables: dict[str, list[dict]]

    @property
    def tables(self) -> dict[str, list[dict]]:
        return copy.deepcopy(self._tables)

    def table(self, name: str) -> list[dict]:
        return copy.deepcopy(self._tables[name])

    def find(self, table: str, column: str, value: str) -> dict | None:
        """The first row of ``table`` whose ``column`` equals ``value``, deep-copied."""
        for row in self._tables[table]:
            if row.get(column) == value:
                return copy.deepcopy(row)
        return None

    def rows_where(self, table: str, column: str, value: str) -> list[dict]:
        return [copy.deepcopy(r) for r in self._tables[table] if r.get(column) == value]

    @property
    def table_counts(self) -> dict[str, int]:
        return {name: len(rows) for name, rows in self._tables.items()}


class DatasetAdapter:
    """Loads batches 0..3 and hands them out as plain dicts."""

    def __init__(self, dataset_dir: Path | str = DATASET_DIR) -> None:
        self.dataset_dir = Path(dataset_dir)
        self._identity: DatasetIdentity | None = None
        self._checked = False
        self._cache: dict[tuple[str, int], BatchSnapshot] = {}

    # ------------------------------------------------------------------ identity
    @property
    def identity(self) -> DatasetIdentity:
        if self._identity is None:
            archive = self.dataset_dir / ARCHIVE_NAME
            archive_sha = _sha256_file(archive) if archive.is_file() else None
            head = _git_head(self.dataset_dir)
            self._identity = DatasetIdentity(
                archive_sha256=archive_sha,
                git_head=head,
                key=f"{archive_sha or 'no-archive'}:{head or 'no-git'}",
            )
        return self._identity

    # ------------------------------------------------------------------ preflight
    def check(self) -> None:
        """Raise DatasetMissing / SchemaIncompatible before any load is attempted."""
        if self._checked:
            return
        if not self.dataset_dir.is_dir():
            raise DatasetMissing(
                f"dataset directory not found at {self.dataset_dir}. "
                "Check out the dataset next to the app, or point the adapter at it "
                "with the STRATEGY_DATASET_DIR environment variable.",
                {"dataset_dir": str(self.dataset_dir)},
            )
        for sub in ("truth", "schema", "injects"):
            if not (self.dataset_dir / sub).is_dir():
                raise DatasetMissing(
                    f"dataset directory {self.dataset_dir} has no {sub}/ — it is not a "
                    "strategy-evaluation dataset, or the checkout is incomplete.",
                    {"dataset_dir": str(self.dataset_dir), "missing": sub},
                )
        for batch in BATCHES[1:]:
            manifest = self.dataset_dir / "injects" / f"batch_{batch}" / "manifest.json"
            if not manifest.is_file():
                raise DatasetMissing(
                    f"inject manifest missing: {manifest}. Batches 1..3 cannot be replayed.",
                    {"batch": batch, "path": str(manifest)},
                )
        self._check_schema()
        self._checked = True

    def _check_schema(self) -> None:
        for table, columns in REQUIRED_COLUMNS.items():
            path = self.dataset_dir / "schema" / f"{table}.json"
            if not path.is_file():
                raise SchemaIncompatible(
                    f"schema contract missing for table {table!r} ({path}).",
                    {"table": table, "path": str(path)},
                )
            try:
                schema = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise SchemaIncompatible(
                    f"schema contract for table {table!r} is not valid JSON: {exc}",
                    {"table": table, "path": str(path)},
                ) from exc
            properties = schema.get("properties") or {}
            missing = [c for c in columns if c not in properties]
            if missing:
                raise SchemaIncompatible(
                    f"table {table!r} no longer declares the columns this API reads: "
                    f"{', '.join(missing)}. The dataset schema and the app are out of step.",
                    {"table": table, "missing_columns": missing},
                )
            expected_pk = REQUIRED_PRIMARY_KEYS[table]
            actual_pk = schema.get("x-primary-key")
            if actual_pk != expected_pk:
                raise SchemaIncompatible(
                    f"table {table!r} primary key changed: expected {expected_pk}, "
                    f"found {actual_pk}.",
                    {"table": table, "expected": expected_pk, "found": actual_pk},
                )
            defs = schema.get("$defs") or {}
            for name, shape in REQUIRED_SHAPES[table].items():
                _check_shape(table, name, properties[name], shape, defs)

    # ------------------------------------------------------------------ loading
    def as_of(self, batch: int) -> str:
        if batch == 0:
            return date(2026, 9, 8).isoformat()
        return str(self.manifest(batch)["as_of"])

    def manifest(self, batch: int) -> dict:
        path = self.dataset_dir / "injects" / f"batch_{batch}" / "manifest.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def manifests(self) -> list[dict]:
        return [self.manifest(b) for b in BATCHES[1:]]

    def snapshot(self, batch: int) -> BatchSnapshot:
        if batch not in BATCHES:
            raise ValueError(f"batch must be one of {list(BATCHES)}")
        self.check()
        key = (self.identity.key, batch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        started = time.perf_counter()
        try:
            if self.dataset_dir == DATASET_DIR:
                frames = dataset_load(base=True, through_batch=batch)
            else:
                frames = _load_from(self.dataset_dir, base=True, through_batch=batch)
        except FileNotFoundError as exc:
            raise DatasetMissing(
                f"the dataset at {self.dataset_dir} is incomplete: {exc}",
                {"dataset_dir": str(self.dataset_dir)},
            ) from exc
        except KeyError as exc:
            raise SchemaIncompatible(
                f"the dataset at {self.dataset_dir} is missing data the loader needs: {exc}",
                {"dataset_dir": str(self.dataset_dir)},
            ) from exc
        load_ms = (time.perf_counter() - started) * 1000.0
        tables = {name: _records(frame) for name, frame in frames.items()}
        self._verify_loaded(tables)
        snapshot = BatchSnapshot(
            batch=batch,
            as_of=self.as_of(batch),
            load_ms=round(load_ms, 3),
            _tables=tables,
        )
        self._cache[key] = snapshot
        return snapshot

    def _verify_loaded(self, tables: dict[str, list[dict]]) -> None:
        for table, columns in REQUIRED_COLUMNS.items():
            rows = tables.get(table)
            if not rows:
                raise SchemaIncompatible(
                    f"table {table!r} loaded empty; the API cannot answer from it.",
                    {"table": table},
                )
            missing = [c for c in columns if c not in rows[0]]
            if missing:
                raise SchemaIncompatible(
                    f"loaded table {table!r} is missing columns {missing}.",
                    {"table": table, "missing_columns": missing},
                )

    # ------------------------------------------------------------------ views
    def ranking(self, snapshot: BatchSnapshot, game_id: str, actor_id: str) -> list[str]:
        """Ranking of valid strategies by value, from eval/engine.py::ranking."""
        return list(_engine().ranking(snapshot._tables, game_id, actor_id))

    def blue_ranking(self, snapshot: BatchSnapshot) -> list[str]:
        return self.ranking(snapshot, BLUE_GAME_ID, BLUE_ACTOR_ID)

    def world_counts(self, snapshot: BatchSnapshot) -> tuple[int, int]:
        """(worlds available to the Blue actor, distinct world labels across all actors)."""
        actor_of = {
            s["strategy_id"]: (s["game_id"], s["actor_id"])
            for s in snapshot._tables["strategies"]
        }
        blue: set[str] = set()
        every: set[str] = set()
        for row in snapshot._tables["payoffs"]:
            every.add(row["world"])
            if actor_of.get(row["strategy_id"]) == (BLUE_GAME_ID, BLUE_ACTOR_ID):
                blue.add(row["world"])
        return len(blue), len(every)


def _flatten(node: dict, defs: dict) -> tuple[set[str], set[str] | None, dict]:
    """($ref/anyOf resolved) JSON types, enum values if any, and sub-properties."""
    ref = node.get("$ref")
    if ref:
        return _flatten(defs.get(ref.rsplit("/", 1)[-1], {}), defs)
    members = node.get("anyOf") or node.get("oneOf")
    if members:
        types: set[str] = set()
        enum: set[str] | None = None
        properties: dict = {}
        for member in members:
            member_types, member_enum, member_properties = _flatten(member, defs)
            types |= member_types
            if member_enum is not None:
                enum = (enum or set()) | member_enum
            properties.update(member_properties)
        return types, enum, properties
    declared = node.get("type")
    types = {declared} if isinstance(declared, str) else set(declared or ())
    enum = set(node["enum"]) if "enum" in node else None
    if enum is not None and not types:
        types = {"string"}
    return types, enum, dict(node.get("properties") or {})


def _check_shape(table: str, path: str, node: dict, shape: Shape, defs: dict) -> None:
    """Compare one declared property against the shape the API reads."""
    types, enum, properties = _flatten(node, defs)
    if types != set(shape.types):
        raise SchemaIncompatible(
            f"table {table!r} property {path!r} changed type: expected "
            f"{sorted(shape.types)}, found {sorted(types)}.",
            {
                "table": table, "property": path,
                "expected": sorted(shape.types), "found": sorted(types),
            },
        )
    if shape.enum is not None and enum != set(shape.enum):
        raise SchemaIncompatible(
            f"table {table!r} property {path!r} changed enum values: expected "
            f"{sorted(shape.enum)}, found {sorted(enum or ())}.",
            {
                "table": table, "property": path,
                "expected": sorted(shape.enum), "found": sorted(enum or ()),
            },
        )
    for name, sub in (shape.properties or {}).items():
        if name not in properties:
            raise SchemaIncompatible(
                f"table {table!r} property {path!r} no longer declares {name!r}, "
                "which the API reads.",
                {"table": table, "property": f"{path}.{name}", "missing": name},
            )
        _check_shape(table, f"{path}.{name}", properties[name], sub, defs)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(dataset_dir: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(dataset_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    head = out.stdout.strip()
    return head if out.returncode == 0 and head else None


def _engine():
    """eval/ is importable only with the dataset package directory on sys.path."""
    package_dir = str(DATASET_DIR)
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)
    from eval import engine

    return engine
