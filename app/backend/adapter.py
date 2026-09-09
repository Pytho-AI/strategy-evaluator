"""Read-only adapter over the frozen dataset.

Every computed number in this module comes out of ``dataset.load(...)``, which runs
``dataset/eval/engine.py::recompute`` on each call. Nothing here reads ``truth/*.jsonl``
for a computed column, re-implements an eval formula, or writes to ``dataset/``.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
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

# Extension layers the collection view reads. Loaded when the checkout has them; a dataset
# without them still serves every endpoint, with the extension-backed fields empty.
EXTENSIONS = ("collection_assets", "authority")

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
_FLAG = Shape(("boolean",))
_LIST = Shape(("array",))
_OBJECT = Shape(("object",))
_ANY = Shape(())  # the schema declares no type: the API passes the value through
_MAYBE_TEXT = Shape(("null", "string"))
_MAYBE_NUMBER = Shape(("null", "number"))
_MAYBE_COUNT = Shape(("integer", "null"))
_MAYBE_LIST = Shape(("array", "null"))
_HORIZON = Shape(("string",), enum=("long", "mid", "near"))
_RISK_LEVEL = Shape(("string",), enum=("high", "low", "moderate", "significant"))
_NODE_TYPE = Shape(
    ("string",),
    enum=(
        "action", "assumption", "claim", "harmful_event", "objective", "problem_set",
        "strategy",
    ),
)
_VALIDITY_RESULT = Shape(
    ("object",), properties={"pass": Shape(("boolean",)), "evidence": _TEXT}
)

# The shapes the API consumes, checked against dataset/schema/*.json before loading.
# Every entry is a field contracts.py or a route reads; nothing speculative. Enums are
# declared only where the product branches on the value.
REQUIRED_SHAPES: dict[str, dict[str, Shape]] = {
    "strategies": {
        "strategy_id": _TEXT,
        "game_id": _TEXT,
        "actor_id": _TEXT,
        "name": _TEXT,
        "summary": _TEXT,
        "echelon": _TEXT,
        "status": Shape(
            ("null", "string"), enum=("infeasible", "invalid", "stale", "valid")
        ),
        "value": _MAYBE_NUMBER,
        "value_ci": _MAYBE_LIST,
        "robustness": _MAYBE_NUMBER,
        "aspiration": _MAYBE_NUMBER,
        "risk_functional": _TEXT,
        "risk_alpha": _MAYBE_NUMBER,
        "adversary_coa_label": _MAYBE_TEXT,
        "opponent_model_id": _TEXT,
        "end_state_objective_id": _TEXT,
        "mission_who": _TEXT,
        "mission_what": _TEXT,
        "mission_when": _TEXT,
        "mission_where": _TEXT,
        "mission_why": _TEXT,
        "main_effort": _TEXT,
        "sequencing": _TEXT,
        "reserve_policy": _TEXT,
        "task_org": _LIST,
        "constraints": _LIST,
        "restraints": _LIST,
        "mitigates_he_ids": _LIST,
        "theory_of_victory": _LIST,
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
        "subject_id": _TEXT,
        "predicate": _TEXT,
        "tolerance": Shape(("object",), properties={"op": _TEXT, "value": _ANY}),
        "role": _TEXT,
        "origin": Shape(("string",), enum=("higher_hq", "own")),
        "jp50_logical": _FLAG,
        "jp50_realistic": _FLAG,
        "jp50_essential": _FLAG,
        "in_decision_matrix": _FLAG,
    },
    "problem_set_assessments": {
        "problem_set_id": _TEXT,
        "jsps_horizon": _HORIZON,
        "max_risk_level": _RISK_LEVEL,
        "he_ids": _LIST,
        "aggregated_statement_text": _TEXT,
    },
    "problem_sets": {
        "problem_set_id": _TEXT,
        "name": _TEXT,
        "entity_id": _TEXT,
        "tier": _COUNT,
        "thing_of_value_ids": _LIST,
        "risk_owner_role": _TEXT,
        "risk_context_source_id": _MAYBE_TEXT,
        "tolerance_statement": _TEXT,
        "strategic_context": _TEXT,
        "scope_and_boundaries": _TEXT,
        "assumptions_and_constraints": _TEXT,
        "expected_outputs": _TEXT,
    },
    "harmful_events": {
        "he_id": _TEXT,
        "problem_set_id": _TEXT,
        "statement": _TEXT,
        "risk_type": Shape(("string",), enum=("MR", "MSR")),
        "risk_subset": _MAYBE_TEXT,
        "strategic_value": _MAYBE_TEXT,
        "damage_degree": _MAYBE_TEXT,
        "fig28_row": _MAYBE_TEXT,
        "fig28_cell": _MAYBE_TEXT,
        "base_p": _NUMBER,
        "condition": _TEXT,
        "posture_subject_ids": _LIST,
        "thing_of_value_id": _TEXT,
        "beneficial_counterpart_he_id": _MAYBE_TEXT,
        "beneficial_statement": _MAYBE_TEXT,
        "key_actions": _MAYBE_TEXT,
    },
    "risk_assessments": {
        "he_id": _TEXT,
        "jsps_horizon": _HORIZON,
        "p_raw": _NUMBER,
        "p_level": _TEXT,
        "c_level": _TEXT,
        "risk_level": _RISK_LEVEL,
        "trend": _TEXT,
        "forced_choice_applied": _FLAG,
        "posture_rationale": _MAYBE_TEXT,
        "dominant_driver_id": _MAYBE_TEXT,
        "active_driver_ids": _LIST,
        "statement_text": _TEXT,
    },
    "risk_drivers": {
        "driver_id": _TEXT,
        "he_id": _TEXT,
        "claim_subject_id": _TEXT,
        "claim_predicate": _TEXT,
        "driver_kind": _TEXT,
        "locus": _TEXT,
        "op": _TEXT,
        "value": _ANY,
        "delta": _NUMBER,
        "horizons": _LIST,
        "label": _TEXT,
    },
    "risk_sources": {
        "rs_id": _TEXT,
        "he_id": _TEXT,
        "source_kind": _TEXT,
        "entity_id": _TEXT,
        "description": _TEXT,
    },
    "escalation_edges": {
        "edge_id": _TEXT,
        "from_he_id": _TEXT,
        "to_he_id": _TEXT,
        "lift": _NUMBER,
        "mechanism": _TEXT,
    },
    "collection_requirements": {
        "req_id": _TEXT,
        "status": Shape(
            ("string",),
            enum=("closed", "research", "satisfaction", "submission", "validation"),
        ),
        "priority": _MAYBE_NUMBER,
        "jipcl_rank": _MAYBE_COUNT,
        "pir_id": _TEXT,
        "eei": _TEXT,
        "indicators": _LIST,
        "sir": _TEXT,
        "gap_type": _TEXT,
        "subject_id": _TEXT,
        "predicate": _TEXT,
        "assumption_id": _MAYBE_TEXT,
        "rfi_disposition": _TEXT,
        "routing": _TEXT,
        "ltiov": _TEXT,
        "created_at": _TEXT,
        "answered_by_source_id": _MAYBE_TEXT,
    },
    "pirs": {
        "pir_id": _TEXT,
        "statement": _TEXT,
        "commander_role": _TEXT,
        "priority_rank": _COUNT,
        "decision_point_ids": _LIST,
    },
    "payoffs": {"strategy_id": _TEXT, "world": _TEXT},
    "strategy_objectives": {
        "strategy_id": _TEXT,
        "objective_id": _TEXT,
        "weight": _NUMBER,
        "rating_1_to_3": _MAYBE_COUNT,
    },
    "strategy_resources": {
        "strategy_id": _TEXT,
        "resource_id": _TEXT,
        "budget": _NUMBER,
    },
    "resources": {"resource_id": _TEXT, "name": _TEXT, "unit": _TEXT},
    "policy_rules": {
        "rule_id": _TEXT,
        "strategy_id": _TEXT,
        "action_id": _TEXT,
        "periods": _MAYBE_LIST,
    },
    "decision_points": {
        "dp_id": _TEXT,
        "strategy_id": _TEXT,
        "name": _TEXT,
        "branch_rule_ids": _LIST,
        "pir_id": _MAYBE_TEXT,
        "latest_period": _MAYBE_COUNT,
    },
    "opponent_models": {
        "opponent_model_id": _TEXT,
        "actor_id": _TEXT,
        "distribution": _LIST,
    },
    "actions": {
        "action_id": _TEXT,
        "name": _TEXT,
        "cost": _OBJECT,
        "mechanism": _TEXT,
        "tactic_class": _TEXT,
        "line_of_effort": _TEXT,
    },
    "objectives": {
        "objective_id": _TEXT,
        "name": _TEXT,
        "kind": _TEXT,
        "statement": _MAYBE_TEXT,
        "aspiration": _MAYBE_NUMBER,
        "metric": _TEXT,
    },
    "games": {"game_id": _TEXT, "horizon": _COUNT},
    "entities": {
        "entity_id": _TEXT,
        "entity_type": _TEXT,
        "canonical_name": _TEXT,
    },
    "dependencies": {
        "edge_id": _TEXT,
        "from_type": _NODE_TYPE,
        "from_id": _TEXT,
        "to_type": _NODE_TYPE,
        "to_id": _TEXT,
        "kind": Shape(
            ("string",),
            enum=(
                "contradicts", "drives", "enables", "escalates", "grounds", "requires",
                "supports",
            ),
        ),
        "mechanism": _TEXT,
        "weight": _NUMBER,
        "evidence_claim_ids": _LIST,
    },
    "claims": {
        "claim_id": _TEXT,
        "source_id": _TEXT,
        "subject_id": _TEXT,
        "predicate": _TEXT,
        "object_id": _MAYBE_TEXT,
        "value": Shape(("boolean", "integer", "null", "number", "string")),
        "value_type": _TEXT,
        "unit": _MAYBE_TEXT,
        "valid_from": _TEXT,
        "valid_to": _MAYBE_TEXT,
        "asserted_at": _TEXT,
        "estimative": _FLAG,
        "likelihood_icd203": _MAYBE_TEXT,
        "likelihood_surface_term": _MAYBE_TEXT,
        "confidence_icd203": _TEXT,
        "confidence": _NUMBER,
        "span_start": _COUNT,
        "span_end": _COUNT,
        "status": Shape(
            ("string",), enum=("approved", "proposed", "rejected", "superseded")
        ),
        "supersedes_claim_id": _MAYBE_TEXT,
        "truth_claim_id": _MAYBE_TEXT,
    },
    "sources": {
        "source_id": _TEXT,
        "title": _TEXT,
        "path": _TEXT,
        "doc_type": _TEXT,
        "author_org": _TEXT,
        "reliability": _TEXT,
        "credibility": _TEXT,
        "published_at": _TEXT,
        "batch": _COUNT,
    },
}

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    table: tuple(shapes) for table, shapes in REQUIRED_SHAPES.items()
}

REQUIRED_PRIMARY_KEYS: dict[str, list[str]] = {
    "strategies": ["strategy_id"],
    "assumptions": ["assumption_id"],
    "problem_set_assessments": ["problem_set_id", "jsps_horizon", "world_version"],
    "problem_sets": ["problem_set_id"],
    "harmful_events": ["he_id"],
    "risk_assessments": ["he_id", "jsps_horizon", "world_version"],
    "risk_drivers": ["driver_id"],
    "risk_sources": ["rs_id"],
    "escalation_edges": ["edge_id"],
    "collection_requirements": ["req_id"],
    "pirs": ["pir_id"],
    "payoffs": ["strategy_id", "opponent_strategy_id", "world"],
    "strategy_objectives": ["strategy_id", "objective_id"],
    "strategy_resources": ["strategy_id", "resource_id"],
    "resources": ["resource_id"],
    "policy_rules": ["rule_id"],
    "decision_points": ["dp_id"],
    "opponent_models": ["opponent_model_id"],
    "actions": ["action_id"],
    "objectives": ["objective_id"],
    "games": ["game_id"],
    "entities": ["entity_id"],
    "dependencies": ["edge_id"],
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

    @property
    def raw(self) -> dict[str, list[dict]]:
        """The cache's own tables, uncopied. Read them; never mutate them."""
        return self._tables

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
        self._indexes: dict[tuple[str, int], Any] = {}

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
        extensions = [
            name
            for name in EXTENSIONS
            if (self.dataset_dir / "extensions" / name / "truth").is_dir()
        ]
        try:
            if self.dataset_dir == DATASET_DIR:
                frames = dataset_load(
                    base=True, extensions=extensions, through_batch=batch
                )
            else:
                frames = _load_from(
                    self.dataset_dir,
                    base=True,
                    extensions=extensions,
                    through_batch=batch,
                )
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
    def index(self, batch: int):
        """The joined, read-only view of one batch (app/backend/derive.py::Index)."""
        from .derive import Index

        snapshot = self.snapshot(batch)
        key = (self.identity.key, batch)
        cached = self._indexes.get(key)
        if cached is None:
            cached = Index(snapshot, self.dataset_dir)
            self._indexes[key] = cached
        return cached

    def ranking(self, snapshot: BatchSnapshot, game_id: str, actor_id: str) -> list[str]:
        """Ranking of valid strategies by value, from eval/engine.py::ranking."""
        return list(eval_module("engine").ranking(snapshot.raw, game_id, actor_id))

    def blue_ranking(self, snapshot: BatchSnapshot) -> list[str]:
        return self.ranking(snapshot, BLUE_GAME_ID, BLUE_ACTOR_ID)

    def world_counts(self, snapshot: BatchSnapshot) -> tuple[int, int]:
        """(worlds available to the Blue actor, distinct world labels across all actors)."""
        actor_of = {
            s["strategy_id"]: (s["game_id"], s["actor_id"])
            for s in snapshot.raw["strategies"]
        }
        blue: set[str] = set()
        every: set[str] = set()
        for row in snapshot.raw["payoffs"]:
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


def eval_module(name: str):
    """Import ``eval.<name>``: eval/ resolves only with the dataset package dir on sys.path."""
    package_dir = str(DATASET_DIR)
    if package_dir not in sys.path:
        sys.path.insert(0, package_dir)
    return importlib.import_module(f"eval.{name}")
