"""Joins, name resolution and eval bridges over one loaded batch.

Every number reaching a route is either a column the loader already recomputed
(``dataset.load`` runs ``eval/engine.py::recompute``) or the return value of a function in
``dataset/eval``. No eval formula is re-implemented here, and nothing writes to ``dataset/``.
"""
from __future__ import annotations

from datetime import date
from functools import cached_property
from pathlib import Path
from typing import Any

from .adapter import BatchSnapshot, eval_module

HORIZONS = ("near", "mid", "long")

# Which table resolves a dependency-graph node id, and the column that keys it.
NODE_TABLES: dict[str, tuple[str, str]] = {
    "claim": ("claims", "claim_id"),
    "assumption": ("assumptions", "assumption_id"),
    "strategy": ("strategies", "strategy_id"),
    "action": ("actions", "action_id"),
    "objective": ("objectives", "objective_id"),
    "problem_set": ("problem_sets", "problem_set_id"),
    "harmful_event": ("harmful_events", "he_id"),
}


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def caution() -> str:
    """The JP 5-0 App. F caution, imported from eval/style_check.py (never retyped)."""
    return eval_module("style_check").CAUTION


class Index:
    """A read-only, indexed view of one cached batch. Built once per (dataset, batch)."""

    def __init__(self, snapshot: BatchSnapshot, dataset_dir: Path) -> None:
        self.snapshot = snapshot
        self.dataset_dir = Path(dataset_dir)
        self.batch = snapshot.batch
        self.as_of = date.fromisoformat(snapshot.as_of)
        self._t = snapshot.raw
        self._text: dict[str, str] = {}

    # ------------------------------------------------------------------ tables
    def rows(self, table: str) -> list[dict]:
        return self._t.get(table, [])

    def by(self, table: str, key: str) -> dict[str, dict]:
        return {r[key]: r for r in self.rows(table)}

    def group(self, table: str, key: str) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for row in self.rows(table):
            out.setdefault(row[key], []).append(row)
        return out

    @cached_property
    def strategies(self) -> dict[str, dict]:
        return self.by("strategies", "strategy_id")

    @cached_property
    def entities(self) -> dict[str, dict]:
        return self.by("entities", "entity_id")

    @cached_property
    def objectives(self) -> dict[str, dict]:
        return self.by("objectives", "objective_id")

    @cached_property
    def claims(self) -> dict[str, dict]:
        return self.by("claims", "claim_id")

    @cached_property
    def sources(self) -> dict[str, dict]:
        return self.by("sources", "source_id")

    @cached_property
    def harmful_events(self) -> dict[str, dict]:
        return self.by("harmful_events", "he_id")

    @cached_property
    def problem_sets(self) -> dict[str, dict]:
        return self.by("problem_sets", "problem_set_id")

    @cached_property
    def assumptions(self) -> dict[str, dict]:
        return self.by("assumptions", "assumption_id")

    @cached_property
    def rules_by_strategy(self) -> dict[str, list[dict]]:
        return self.group("policy_rules", "strategy_id")

    @cached_property
    def risk_rows(self) -> dict[tuple[str, str], dict]:
        return {(r["he_id"], r["jsps_horizon"]): r for r in self.rows("risk_assessments")}

    # ------------------------------------------------------------------ names
    def entity_name(self, entity_id: str | None) -> str | None:
        if not entity_id:
            return None
        row = self.entities.get(entity_id)
        return row["canonical_name"] if row else entity_id

    def claim_label(self, claim: dict) -> str:
        subject = self.entity_name(claim["subject_id"])
        value = claim.get("object_id") if claim.get("value_type") == "entity" else claim.get("value")
        return f"{subject} {claim['predicate']} = {value}"

    def display_name(self, node_type: str, node_id: str) -> str:
        """A readable label for a dependency-graph node, resolved through its table."""
        table_key = NODE_TABLES.get(node_type)
        if table_key is None:
            return node_id
        row = self.by(*table_key).get(node_id)
        if row is None:
            return node_id
        if node_type == "claim":
            return self.claim_label(row)
        for field in ("canonical_name", "name", "statement"):
            if row.get(field):
                return str(row[field])
        return node_id

    # ------------------------------------------------------------------ eval bridges
    @cached_property
    def _value(self):
        return eval_module("value")

    @cached_property
    def _engine(self):
        return eval_module("engine")

    @cached_property
    def _validity(self):
        return eval_module("validity")

    @cached_property
    def _claimset_mod(self):
        return eval_module("claimset")

    @cached_property
    def risk_levels(self) -> list[str]:
        """JRAM's own low → high ordering (eval/jram.py::RISK_LEVELS)."""
        return list(eval_module("jram").RISK_LEVELS)

    @cached_property
    def claimset(self):
        return self._claimset_mod.ClaimSet(self.rows("claims"))

    @cached_property
    def payoff_index(self):
        return self._value.PayoffIndex(self.rows("payoffs"))

    @cached_property
    def _assumption_vectors(self) -> dict[tuple[str, str], tuple[int, list[float]]]:
        out = {}
        for game_id, actor_id in sorted(
            {(s["game_id"], s["actor_id"]) for s in self.rows("strategies")}
        ):
            k, p, _ = self._engine.assumption_vector(
                self._t, game_id, actor_id, self.claimset, self.as_of
            )
            out[(game_id, actor_id)] = (k, p)
        return out

    def objective_order(self, game_id: str, actor_id: str) -> list[str]:
        return self._engine.objective_order(self._t, game_id, actor_id)

    def ranking(self, game_id: str, actor_id: str) -> list[str]:
        """Valid strategies best value first (eval.engine.ranking)."""
        return list(self._engine.ranking(self._t, game_id, actor_id))

    def opponent_dist(self, strategy: dict) -> dict[str, float]:
        return self._engine.opponent_dist(self._t, strategy["opponent_model_id"])

    def contributions(self, strategy_id: str) -> dict[str, float]:
        """E[u_k] per objective for one strategy.

        ``eval.value.value`` with a one-hot weight vector and rho = expected is exactly the
        E[u_k] the engine uses for the App. F ratings; no formula is copied.
        """
        strategy = self.strategies[strategy_id]
        key = (strategy["game_id"], strategy["actor_id"])
        order = self.objective_order(*key)
        n_worlds, probabilities = self._assumption_vectors[key]
        opponents = self.opponent_dist(strategy)
        out: dict[str, float] = {}
        for i, objective_id in enumerate(order):
            weights = [1.0 if j == i else 0.0 for j in range(len(order))]
            out[objective_id] = self._value.value(
                strategy_id,
                self.payoff_index,
                weights,
                opponents,
                probabilities,
                n_worlds,
                "expected",
            )
        return out

    def worst_case_cost(self, strategy_id: str) -> dict[str, float]:
        """Expected worst-case resource use, from eval.validity.worst_case_cost."""
        strategy = self.strategies[strategy_id]
        horizon = self.by("games", "game_id")[strategy["game_id"]]["horizon"]
        return self._validity.worst_case_cost(
            self.rules_by_strategy.get(strategy_id, []),
            self.by("actions", "action_id"),
            horizon,
        )

    def current_claim(self, subject_id: str, predicate: str) -> dict | None:
        """The approved claim valid at as_of (eval.claimset.ClaimSet.current)."""
        return self.claimset.current(subject_id, predicate, self.as_of)

    def driver_claims(self, driver: dict, horizon: str) -> list[dict]:
        """The approved claims that satisfy a driver's term in one horizon window."""
        start, end = self._claimset_mod.horizon_window(self.as_of, horizon)
        return [
            claim
            for claim in self.claimset.in_window(
                driver["claim_subject_id"],
                driver["claim_predicate"],
                start,
                end,
                known_at=self.as_of,
            )
            if self._claimset_mod.satisfies(
                self.claimset.value_of(claim), driver["op"], driver["value"]
            )
        ]

    def claim_value(self, claim: dict) -> Any:
        return self.claimset.value_of(claim)

    def satisfies(self, value: Any, op: str, reference: Any) -> bool:
        """eval.claimset.satisfies: the comparison the engine itself applies."""
        return self._claimset_mod.satisfies(value, op, reference)

    def is_current_evidence(self, claim: dict) -> bool:
        """True when this claim is one the evaluator can select at ``as_of``.

        The same test ``eval.claimset.ClaimSet.current`` applies: approved, asserted by
        ``as_of``, and with a valid-time window that contains it.
        """
        if claim["status"] != "approved":
            return False
        asserted = _date(claim.get("asserted_at")) or _date(claim["valid_from"])
        valid_from, valid_to = _date(claim["valid_from"]), _date(claim.get("valid_to"))
        return (
            asserted is not None
            and asserted <= self.as_of
            and valid_from is not None
            and valid_from <= self.as_of
            and (valid_to is None or valid_to >= self.as_of)
        )

    # ------------------------------------------------------------------ claim flags
    @cached_property
    def superseded_by(self) -> dict[str, str]:
        return {
            c["supersedes_claim_id"]: c["claim_id"]
            for c in self.rows("claims")
            if c.get("supersedes_claim_id")
        }

    @cached_property
    def contradictions(self) -> dict[str, list[str]]:
        """claim_id -> the claims it conflicts with.

        A proposed claim conflicts with an approved claim on the same (subject, predicate)
        when their valid-time windows overlap and their values differ.
        """
        out: dict[str, list[str]] = {}
        by_key: dict[tuple[str, str], list[dict]] = {}
        for claim in self.rows("claims"):
            by_key.setdefault((claim["subject_id"], claim["predicate"]), []).append(claim)
        for rows in by_key.values():
            approved = [c for c in rows if c["status"] == "approved"]
            for proposed in [c for c in rows if c["status"] == "proposed"]:
                for other in approved:
                    if not _windows_overlap(proposed, other):
                        continue
                    if self.claim_value(proposed) == self.claim_value(other):
                        continue
                    out.setdefault(proposed["claim_id"], []).append(other["claim_id"])
                    out.setdefault(other["claim_id"], []).append(proposed["claim_id"])
        return out

    def is_stale(self, claim: dict) -> bool:
        valid_to = _date(claim.get("valid_to"))
        return valid_to is not None and valid_to < self.as_of

    def is_superseded(self, claim: dict) -> bool:
        return claim["status"] == "superseded" or claim["claim_id"] in self.superseded_by

    def span_text(self, claim: dict) -> str | None:
        """The exact [span_start, span_end) slice of the source document."""
        source = self.sources.get(claim["source_id"])
        if source is None:
            return None
        text = self._text.get(source["source_id"])
        if text is None:
            path = self.dataset_dir / source["path"]
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            self._text[source["source_id"]] = text
        return text[claim["span_start"] : claim["span_end"]] or None

    def attach_text(self, source_id: str, text: str) -> None:
        """Register a product report's text so ``span_text`` can slice it without a file."""
        self._text[source_id] = text

    def register_contradiction(self, claim_id: str, other_claim_id: str) -> None:
        """Record a reviewed contradiction between two approved claims, both ways."""
        for a, b in ((claim_id, other_claim_id), (other_claim_id, claim_id)):
            edges = self.contradictions.setdefault(a, [])
            if b not in edges:
                edges.append(b)

    # ------------------------------------------------------------------ graph walks
    @cached_property
    def edges_from(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for edge in self.rows("dependencies"):
            out.setdefault(edge["from_id"], []).append(edge)
        return out

    @cached_property
    def edges_to(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for edge in self.rows("dependencies"):
            out.setdefault(edge["to_id"], []).append(edge)
        return out

    def walk(self, node_id: str, depth: int = 3) -> list[list[dict]]:
        """Every outgoing dependency chain from a node, up to ``depth`` edges."""
        paths: list[list[dict]] = []

        def step(current: str, trail: list[dict]) -> None:
            edges = self.edges_from.get(current, []) if len(trail) < depth else []
            onward = [e for e in edges if e["to_id"] not in {x["from_id"] for x in trail}]
            if not onward:
                if trail:
                    paths.append(trail)
                return
            for edge in onward:
                step(edge["to_id"], trail + [edge])

        step(node_id, [])
        return paths

    @cached_property
    def escalation_into(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for edge in self.rows("escalation_edges"):
            out.setdefault(edge["to_he_id"], []).append(edge)
        return out

    @cached_property
    def escalation_out_of(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for edge in self.rows("escalation_edges"):
            out.setdefault(edge["from_he_id"], []).append(edge)
        return out

    def upstream_paths(self, he_id: str) -> list[list[str]]:
        """Every chain of escalation edges that feeds this harmful event."""
        paths: list[list[str]] = []

        def step(node: str, trail: list[str]) -> None:
            parents = [e for e in self.escalation_into.get(node, []) if e["from_he_id"] not in trail]
            if not parents:
                if len(trail) > 1:
                    paths.append(trail)
                return
            for edge in parents:
                step(edge["from_he_id"], [edge["from_he_id"]] + trail)

        step(he_id, [he_id])
        return paths


def _windows_overlap(a: dict, b: dict) -> bool:
    a_from, a_to = _date(a["valid_from"]), _date(a.get("valid_to"))
    b_from, b_to = _date(b["valid_from"]), _date(b.get("valid_to"))
    return (a_to is None or a_to >= b_from) and (b_to is None or b_to >= a_from)
