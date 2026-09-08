"""Shared generation context: seed, RNG, T0, id counters, validated table rows, rendered docs."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from gen.io import sha256_text, write_jsonl, write_text
from gen.models import TABLE_BY_NAME

DATASET_DIR = Path(__file__).resolve().parents[1]
T0 = date(2026, 9, 8)


@dataclass
class Ctx:
    seed: int
    dataset_dir: Path = DATASET_DIR
    t0: date = T0
    rng: random.Random = field(init=False)
    tables: dict[str, list[dict]] = field(default_factory=lambda: {n: [] for n in TABLE_BY_NAME})
    docs: dict[str, str] = field(default_factory=dict)  # relative path -> text
    counters: dict[str, int] = field(default_factory=dict)
    world_version: int = 0

    def __post_init__(self):
        self.rng = random.Random(self.seed)

    # ids -------------------------------------------------------------
    def next_id(self, prefix: str, width: int = 4) -> str:
        n = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = n
        return f"{prefix}_{n:0{width}d}"

    # rows ------------------------------------------------------------
    def add(self, table: str, row: BaseModel | dict) -> dict:
        model = TABLE_BY_NAME[table].model
        inst = row if isinstance(row, BaseModel) else model(**row)
        d = inst.model_dump(mode="json", by_alias=True)
        self.tables[table].append(d)
        return d

    def get(self, table: str, **match: Any) -> dict:
        for r in self.tables[table]:
            if all(r.get(k) == v for k, v in match.items()):
                return r
        raise KeyError(f"{table} {match}")

    def day(self, offset: int) -> date:
        return self.t0 + timedelta(days=offset)

    # docs ------------------------------------------------------------
    def add_doc(self, rel_path: str, text: str) -> str:
        self.docs[rel_path] = text
        return sha256_text(text)

    # output ----------------------------------------------------------
    def write(self, truth_dir: Path | None = None) -> None:
        truth_dir = truth_dir or self.dataset_dir / "truth"
        for name in TABLE_BY_NAME:
            write_jsonl(truth_dir / f"{name}.jsonl", self.tables[name])
        for rel, text in self.docs.items():
            write_text(self.dataset_dir / rel, text)
