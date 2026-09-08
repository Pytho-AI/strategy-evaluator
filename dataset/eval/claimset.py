"""Current-claim lookup over a claim list: the approved claim valid at a date for (subject, predicate)."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional


def _d(s) -> Optional[date]:
    if s is None or isinstance(s, date):
        return s
    return date.fromisoformat(s)


def satisfies(value: Any, op: str, ref: Any) -> bool:
    try:
        if op == "==":
            return value == ref
        if op == "!=":
            return value != ref
        if op == "<":
            return value < ref
        if op == "<=":
            return value <= ref
        if op == ">":
            return value > ref
        if op == ">=":
            return value >= ref
        if op == "abs_le":
            return abs(float(value)) <= float(ref)
        if op == "in":
            return value in ref
    except TypeError:
        return False
    raise ValueError(f"unknown op {op}")


class ClaimSet:
    """Index of claims by (subject_id, predicate). `current()` returns the approved claim whose
    valid-time window contains `as_of`; among several, the one with the latest asserted_at wins."""

    def __init__(self, claims: list[dict]):
        self.by_key: dict[tuple[str, str], list[dict]] = {}
        for c in claims:
            self.by_key.setdefault((c["subject_id"], c["predicate"]), []).append(c)

    def all(self, subject_id: str, predicate: str, approved_only: bool = True, known_at: Optional[date] = None) -> list[dict]:
        rows = self.by_key.get((subject_id, predicate), [])
        return [r for r in rows if ((not approved_only) or r.get("status", "approved") == "approved")
                and (known_at is None or _d(r.get("asserted_at", r["valid_from"])) <= known_at)]

    def current(self, subject_id: str, predicate: str, as_of: date) -> Optional[dict]:
        best = None
        for c in self.all(subject_id, predicate, known_at=as_of):
            vf, vt = _d(c["valid_from"]), _d(c.get("valid_to"))
            if vf <= as_of and (vt is None or vt >= as_of):
                if best is None or _d(c.get("asserted_at", c["valid_from"])) >= _d(best.get("asserted_at", best["valid_from"])):
                    best = c
        return best

    def in_window(self, subject_id: str, predicate: str, start: date, end: date, known_at: Optional[date] = None) -> list[dict]:
        out = []
        for c in self.all(subject_id, predicate, known_at=known_at):
            vf, vt = _d(c["valid_from"]), _d(c.get("valid_to"))
            if vf <= end and (vt is None or vt >= start):
                out.append(c)
        return out

    def value_of(self, c: dict) -> Any:
        return c["object_id"] if c.get("value_type") == "entity" else c.get("value")


def horizon_window(as_of: date, horizon: str) -> tuple[date, date]:
    from gen.vocab import HORIZON_YEARS  # local import keeps eval importable without gen at runtime

    a, b = HORIZON_YEARS[horizon]
    return as_of + timedelta(days=int(a * 365.25)), as_of + timedelta(days=int(b * 365.25))
