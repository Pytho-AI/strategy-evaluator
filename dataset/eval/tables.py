"""Load truth/ (or an app's output directory) into {table_name: [row dict, ...]}."""
from __future__ import annotations

import json
from pathlib import Path

TABLE_FILES = [
    "sources", "entities", "claims", "facts", "guidance", "games", "actions", "objectives", "resources",
    "strategies", "strategy_objectives", "strategy_resources", "policy_rules", "decision_points",
    "opponent_models", "payoffs", "distinguishability", "assumptions", "dependencies", "problem_sets",
    "harmful_events", "risk_sources", "risk_drivers", "risk_assessments", "problem_set_assessments",
    "escalation_edges", "pirs", "collection_requirements",
]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_dir(d: Path) -> dict[str, list[dict]]:
    d = Path(d)
    return {name: read_jsonl(d / f"{name}.jsonl") for name in TABLE_FILES}


def index(rows: list[dict], key: str) -> dict:
    return {r[key]: r for r in rows}
