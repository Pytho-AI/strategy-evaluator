"""Deterministic JSONL I/O. Rows are written in insertion order with sorted keys so that a
regeneration from the same seed is byte-identical."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel


def _default(o: Any):
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, BaseModel):
        return o.model_dump(mode="json", by_alias=True)
    raise TypeError(f"not serializable: {type(o)}")


def dumps(row: Any) -> str:
    if isinstance(row, BaseModel):
        row = row.model_dump(mode="json", by_alias=True)
    return json.dumps(row, sort_keys=True, ensure_ascii=False, default=_default, allow_nan=False)


def write_jsonl(path: Path, rows: Iterable[Any]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(dumps(r) + "\n")
            n += 1
    return n


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
