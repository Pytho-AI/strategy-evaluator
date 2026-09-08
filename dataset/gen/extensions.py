"""Generate the five required extension layers and the optional event layer."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from eval.claimset import ClaimSet
from gen import scenario_data as S
from gen.io import write_jsonl, write_text


STR = {"type": "string"}
NUM = {"type": "number"}
INT = {"type": "integer"}
BOOL = {"type": "boolean"}
NULL_STR = {"type": ["string", "null"]}


def _schema(required: list[str], properties: dict) -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": required,
        "properties": properties,
        "additionalProperties": False,
    }


def _emit(root: Path, name: str, tables: dict[str, list[dict]], schemas: dict[str, dict],
          sponsor: str, description: list[str], base_tables: list[str], eval_files: dict[str, str]) -> None:
    ext = root / "extensions" / name
    for table, rows in tables.items():
        write_jsonl(ext / "truth" / f"{table}.jsonl", rows)
        write_text(ext / "schema" / f"{table}.json", json.dumps(schemas[table], sort_keys=True, indent=2) + "\n")
    code = [
        "from dataset import load",
        f'data = load(extensions=["{name}"])',
        f'rows = data["{next(iter(tables))}"]',
        "print(rows.head())",
        "print(len(rows))",
    ]
    readme = f"""# {name}

Intended use case: {sponsor}.
{description[0]}
{description[1]}

Base tables referenced: {', '.join(base_tables)}.

```python
{chr(10).join(code)}
```

IDs remain stable for seed 20260908. License: CC BY 4.0.
"""
    write_text(ext / "README.md", readme)
    for rel, text in eval_files.items():
        write_text(ext / "eval" / rel, text.rstrip() + "\n")


def _value(claim: dict):
    return claim.get("object_id") or claim.get("value")


def _rag(ctx) -> None:
    sources = {row["source_id"]: row for row in ctx.tables["sources"]}
    entities = {row["entity_id"]: row for row in ctx.tables["entities"]}
    claims = [row for row in ctx.tables["claims"] if sources[row["source_id"]]["batch"] == 0 and row["status"] == "approved"]
    questions = []

    def add(text, answer_ids, answer, difficulty, as_of="2026-09-08", citation=None):
        questions.append({
            "question_id": f"q_{len(questions) + 1:04d}", "question": text,
            "answer_claim_ids": answer_ids, "answer_value": answer,
            "difficulty": difficulty, "question_type": difficulty, "as_of": as_of,
            "doctrine_citation": citation,
        })

    for i in range(120):
        claim = claims[i % len(claims)]
        subject = entities[claim["subject_id"]]["canonical_name"]
        add(f"What is the reported {claim['predicate'].replace('_', ' ')} of {subject} as of 8 September 2026?",
            [claim["claim_id"]], _value(claim), "single_hop")

    location_claims = [row for row in claims if row["predicate"] == "located_at"]
    status = {(row["subject_id"], row["predicate"]): row for row in claims if row["predicate"] == "status"}
    pairs = [(row, status[(row["object_id"], "status")]) for row in location_claims if (row["object_id"], "status") in status]
    for i in range(30):
        first, second = pairs[i % len(pairs)]
        subject = entities[first["subject_id"]]["canonical_name"]
        add(f"Where is {subject} located, and what is the reported status of that location?",
            [first["claim_id"], second["claim_id"]],
            {"location_id": first["object_id"], "status": second["value"]}, "multi_hop")

    temporal = [row for row in claims if row.get("valid_to")]
    for i in range(30):
        claim = temporal[i % len(temporal)]
        subject = entities[claim["subject_id"]]["canonical_name"]
        add(f"What was {subject}'s {claim['predicate'].replace('_', ' ')} on {claim['valid_from']}?",
            [claim["claim_id"]], _value(claim), "temporal", claim["valid_from"])

    for i in range(20):
        add(f"What was the readiness of fictional unit Echo-{i + 1:02d} on 8 September 2026?",
            [], None, "unanswerable")

    doctrine = [
        ("What is a harmful event in Joint Risk Analysis?", "An event that could cause an impact to a thing of value.", "CJCSM 3105.01C, Encl. C, p. C-2"),
        ("What are the two main risk categories in Joint Risk Analysis?", "Military risk and military-strategic risk.", "CJCSM 3105.01C, Encl. C, p. C-1"),
        ("What does risk likelihood describe?", "The chance that a harmful event will occur.", "CJCSM 3105.01C, Encl. C, Fig. 6"),
        ("What does risk consequence describe?", "The degree of impact if a harmful event occurs.", "CJCSM 3105.01C, Encl. C"),
        ("What is a course of action?", "A potential way to accomplish an assigned mission.", "JP 5-0, Glossary"),
        ("What is a priority intelligence requirement?", "An intelligence requirement the commander identifies as critical to decision making.", "JP 2-01, Glossary"),
        ("What is a target system?", "A broad set of interrelated components that produces a capability or performs a function.", "JP 3-60, Glossary"),
        ("What is target system analysis?", "Analysis that identifies and evaluates target-system components and relationships.", "JP 3-60, Glossary"),
        ("What is an intelligence confidence level?", "A judgment based on the quality and quantity of supporting information.", "ICD 203, as reproduced in CJCSM 3105.01C Fig. 19"),
        ("What does the JSPS near-term horizon cover?", "Zero to three years.", "CJCSI 3100.01F, JSPS horizons"),
    ]
    for question, answer, citation in doctrine:
        add(question, [], answer, "doctrinal", citation=citation)

    schema = _schema(
        ["question_id", "question", "answer_claim_ids", "answer_value", "difficulty", "question_type", "as_of", "doctrine_citation"],
        {"question_id": STR, "question": STR, "answer_claim_ids": {"type": "array", "items": STR},
         "answer_value": {}, "difficulty": {"enum": ["single_hop", "multi_hop", "temporal", "unanswerable", "doctrinal"]},
         "question_type": {"enum": ["single_hop", "multi_hop", "temporal", "unanswerable", "doctrinal"]},
         "as_of": {"type": "string", "format": "date"}, "doctrine_citation": NULL_STR})
    evaluator = '''"""Exact-answer and citation-id scorer for the RAG QA extension."""
def score(predictions, truth):
    expected = {row["question_id"]: row for row in truth}
    answer = citation = 0
    for row in predictions:
        gold = expected.get(row["question_id"])
        if gold and row.get("answer_value") == gold["answer_value"]:
            answer += 1
        if gold and set(row.get("answer_claim_ids", [])) == set(gold["answer_claim_ids"]):
            citation += 1
    n = max(1, len(expected))
    return {"answer_match": answer / n, "citation_match": citation / n}
'''
    _emit(ctx.dataset_dir, "rag_qa", {"questions": questions}, {"questions": schema},
          "RAG Intelligence Service",
          ["Questions test single-hop, joined, temporal, absent-answer, and doctrinal retrieval.",
           "Gold answers cite base claim IDs or a doctrine location."],
          ["claims", "facts", "sources", "entities"],
          {"score.py": evaluator, "result.json": json.dumps({"answer_match": 1.0, "citation_match": 1.0, "truth_vs_truth": 1.0}, indent=2)})


def _edge_scores(members: list[str], edges: list[tuple[str, str]]) -> list[float]:
    scores = []
    for cut in edges:
        seen = {cut[0]}
        stack = [cut[0]]
        while stack:
            node = stack.pop()
            for a, b in edges:
                if {a, b} == set(cut):
                    continue
                other = b if a == node else (a if b == node else None)
                if other is not None and other not in seen:
                    seen.add(other)
                    stack.append(other)
        scores.append(len(seen) * (len(members) - len(seen)))
    high = max(scores) if scores else 1
    return [round(value / high, 6) for value in scores]


def _target_systems(ctx) -> None:
    definitions = [
        ("ts_energy", "Ilmaran energy system", "Provide electric power to Ilmaran civil and military users",
         ["inf_aldis_terminal", "inf_veyra_station", "inf_ilmara_grid_control", "loc_lisenne"]),
        ("ts_maritime", "Kestrel maritime access system", "Move shipping and naval forces through the Kestrel Strait",
         ["inf_kestrel_lane", "inf_kestrel_cable", "loc_kestrel_strait", "unit_tg_kestrel", "inf_dorne_radar"]),
        ("ts_strike", "Varenian coastal strike system", "Detect, control, and engage maritime forces",
         ["inf_dorne_radar", "unit_var_coastal_msl_bde", "sys_dorne_asm", "unit_var_directorate_nine"]),
        ("ts_sustainment", "Blue theater sustainment system", "Move and protect supplies from port to operating forces",
         ["loc_port_auberon", "inf_blue_logistics_network", "unit_meridian_log_group", "inf_auberon_halden_airbridge", "loc_halden_airfield"]),
    ]
    systems, components, members, links, characteristics = [], [], [], [], []
    entities = {row["entity_id"]: row for row in ctx.tables["entities"]}
    functions = ["node", "link", "control", "input", "output"]
    char_values = {
        "physical": "Observable physical location and condition",
        "functional": "Performs the assigned system function",
        "cognitive_control_informational": "Depends on reporting, control, or operator decisions",
        "environmental": "Affected by the fictional Meridian Sea operating environment",
        "temporal": "Availability and effect can change across inject batches",
    }
    for sid, name, purpose, entity_ids in definitions:
        systems.append({"system_id": sid, "name": name, "purpose": purpose, "kind": "target_system"})
        for index, function in enumerate(functions[:3], start=1):
            components.append({"component_id": f"{sid}_c{index}", "system_id": sid,
                               "name": f"{name} {function} component", "function": function})
        for index, entity_id in enumerate(entity_ids):
            members.append({"system_id": sid, "component_id": f"{sid}_c{index % 3 + 1}", "entity_id": entity_id})
            for char_type, value in char_values.items():
                characteristics.append({"system_id": sid, "entity_id": entity_id,
                    "characteristic_type": char_type,
                    "value": f"{entities[entity_id]['canonical_name']}: {value}"})
        raw_edges = list(zip(entity_ids, entity_ids[1:]))
        for index, ((left, right), score) in enumerate(zip(raw_edges, _edge_scores(entity_ids, raw_edges)), start=1):
            links.append({"link_id": f"{sid}_l{index}", "system_id": sid, "from_entity": left,
                          "to_entity": right, "relation": "supports", "criticality": score})
    schemas = {
        "systems": _schema(["system_id", "name", "purpose", "kind"], {"system_id": STR, "name": STR, "purpose": STR, "kind": {"const": "target_system"}}),
        "target_system_components": _schema(["component_id", "system_id", "name", "function"], {"component_id": STR, "system_id": STR, "name": STR, "function": {"enum": functions}}),
        "system_members": _schema(["system_id", "component_id", "entity_id"], {"system_id": STR, "component_id": STR, "entity_id": STR}),
        "system_links": _schema(["link_id", "system_id", "from_entity", "to_entity", "relation", "criticality"], {"link_id": STR, "system_id": STR, "from_entity": STR, "to_entity": STR, "relation": STR, "criticality": {"type": "number", "minimum": 0, "maximum": 1}}),
        "target_characteristics": _schema(["system_id", "entity_id", "characteristic_type", "value"], {"system_id": STR, "entity_id": STR, "characteristic_type": {"enum": list(char_values)}, "value": STR}),
    }
    result = {"truth_vs_truth": 1.0, "method": "tree edge betweenness normalized to the highest edge in each system"}
    _emit(ctx.dataset_dir, "target_systems",
          {"systems": systems, "target_system_components": components, "system_members": members,
           "system_links": links, "target_characteristics": characteristics}, schemas,
          "Target System Object Development",
          ["Four fictional systems connect base infrastructure, units, systems, and locations.",
           "Criticality is a computable edge-betweenness proxy; JP 3-60 target system analysis uses analyst judgment."],
          ["entities", "claims", "facts"], {"result.json": json.dumps(result, indent=2)})


def _owner(entity_id: str, entities: dict[str, dict]) -> str | None:
    current = entity_id
    while current in entities:
        if current in {"ent_blue", "ent_varenia"}:
            return current
        current = entities[current].get("parent_id")
        if current is None:
            return None
    return None


def _normalizer(predicate: str, value: float) -> dict:
    limits = {
        "readiness": (0, 1), "count": (0, max(10, value * 1.5)), "range_km": (0, 1000),
        "munitions_stock_days": (0, 60), "mobilization_days": (0, 60),
        "mobilized_brigades": (0, 4), "throughput_per_day": (0, max(150, value * 1.5)),
        "capacity_mw": (0, 1000), "displaced_persons": (0, 30000), "outage_hours": (0, 48),
        "mixing_bias": (-1, 1),
    }
    lo, hi = limits.get(predicate, (0, max(1, value * 1.5)))
    return {"lo": lo, "hi": hi}


def _score_area(area: dict, components: list[dict], cs: ClaimSet, as_of) -> float:
    values = []
    for component in components:
        claim = cs.current(component["subject_id"], component["predicate"], as_of)
        raw = _value(claim) if claim else component["normalizer"]["lo"]
        lo, hi = component["normalizer"]["lo"], component["normalizer"]["hi"]
        normalized = min(1.0, max(0.0, (float(raw) - lo) / (hi - lo)))
        values.append((normalized, component["weight"]))
    aggregation = area["aggregation"]
    if aggregation == "min":
        score = min(value for value, _ in values)
    elif aggregation == "sum":
        score = min(1.0, sum(value * weight for value, weight in values))
    else:
        score = sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
    return round(score, 6)


def _capability(ctx) -> None:
    entities = {row["entity_id"]: row for row in ctx.tables["entities"]}
    sources = {row["source_id"]: row for row in ctx.tables["sources"]}
    base_claims = [row for row in ctx.tables["claims"] if sources[row["source_id"]]["batch"] == 0 and isinstance(_value(row), (int, float))]
    candidates: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for claim in base_claims:
        owner = _owner(claim["subject_id"], entities)
        key = (owner, claim["subject_id"], claim["predicate"])
        if owner and key not in seen:
            candidates[owner].append(claim)
            seen.add(key)
    for rows in candidates.values():
        rows.sort(key=lambda row: (row["predicate"] not in {"readiness", "count", "range_km", "munitions_stock_days"}, row["subject_id"], row["predicate"]))

    names = ["Force readiness", "Operational reach", "Force capacity", "Sustainment depth", "Mobility", "Resilience"]
    aggregations = ["weighted_mean", "min", "sum", "weighted_mean", "min", "sum"]
    areas, components = [], []
    for actor in ("ent_blue", "ent_varenia"):
        pool = candidates[actor]
        for i, (name, aggregation) in enumerate(zip(names, aggregations), start=1):
            area_id = f"cap_{'blue' if actor == 'ent_blue' else 'red'}_{i}"
            areas.append({"area_id": area_id, "actor_id": actor, "name": name, "aggregation": aggregation})
            for j in range(2):
                claim = pool[(i - 1 + j * 6) % len(pool)]
                value = float(_value(claim))
                components.append({"component_id": f"{area_id}_c{j + 1}", "area_id": area_id,
                    "subject_id": claim["subject_id"], "predicate": claim["predicate"], "weight": 0.5,
                    "aggregation": aggregation, "normalizer": _normalizer(claim["predicate"], value)})

    by_area = defaultdict(list)
    for component in components:
        by_area[component["area_id"]].append(component)
    scores = []
    for version, day in [(0, 0), (1, S.BATCH_DAYS[1]), (2, S.BATCH_DAYS[2]), (3, S.BATCH_DAYS[3])]:
        as_of = ctx.day(day)
        visible = [row for row in ctx.tables["claims"] if sources[row["source_id"]]["batch"] <= version]
        cs = ClaimSet(visible)
        for area in areas:
            scores.append({"area_id": area["area_id"], "world_version": version,
                           "as_of": as_of.isoformat(), "score": _score_area(area, by_area[area["area_id"]], cs, as_of)})
    schemas = {
        "capability_areas": _schema(["area_id", "actor_id", "name", "aggregation"], {"area_id": STR, "actor_id": STR, "name": STR, "aggregation": {"enum": ["weighted_mean", "min", "sum"]}}),
        "capability_components": _schema(["component_id", "area_id", "subject_id", "predicate", "weight", "aggregation", "normalizer"], {"component_id": STR, "area_id": STR, "subject_id": STR, "predicate": STR, "weight": {"type": "number", "minimum": 0}, "aggregation": {"enum": ["weighted_mean", "min", "sum"]}, "normalizer": {"type": "object", "required": ["lo", "hi"], "properties": {"lo": NUM, "hi": NUM}, "additionalProperties": False}}),
        "capability_scores": _schema(["area_id", "world_version", "as_of", "score"], {"area_id": STR, "world_version": {"type": "integer", "minimum": 0, "maximum": 3}, "as_of": {"type": "string", "format": "date"}, "score": {"type": "number", "minimum": 0, "maximum": 1}}),
    }
    evaluator = '''"""Reference capability aggregation."""
def aggregate(values, aggregation):
    if aggregation == "min":
        return min(value for value, _ in values)
    if aggregation == "sum":
        return min(1.0, sum(value * weight for value, weight in values))
    return sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
'''
    _emit(ctx.dataset_dir, "capability",
          {"capability_areas": areas, "capability_components": components, "capability_scores": scores}, schemas,
          "Capability Assessment Visualization",
          ["Six areas per actor combine numeric readiness, count, range, and sustainment claims.",
           "Scores are normalized to 0–1 and recomputed for each inject world version."],
          ["entities", "claims", "sources"],
          {"capability.py": evaluator, "result.json": json.dumps({"truth_vs_truth": 1.0, "rows": len(scores)}, indent=2)})


def _authority(ctx) -> None:
    tiers = [
        {"tier_id": "tier_1", "name": "automatic", "approver_role": "rules engine", "max_reversibility_cost": 0.1},
        {"tier_id": "tier_2", "name": "J-staff analyst", "approver_role": "staff analyst", "max_reversibility_cost": 0.35},
        {"tier_id": "tier_3", "name": "J-2/J-5 director", "approver_role": "director", "max_reversibility_cost": 0.7},
        {"tier_id": "tier_4", "name": "commander", "approver_role": "commander", "max_reversibility_cost": 1.0},
    ]
    action = [
        {"tactic_class": "observe", "tier_id": "tier_1"}, {"tactic_class": "collect", "tier_id": "tier_2"},
        {"tactic_class": "reposition", "tier_id": "tier_3"}, {"tactic_class": "engage", "tier_id": "tier_4"},
    ]
    recommendation_types = ["strategy_restate", "requirement_submit", "claim_approve", "problem_set_alert"]
    recommendation = [{"recommendation_type": kind, "tier_id": "tier_3", "risk_level_threshold": "significant"}
                      for kind in recommendation_types]
    sources = {row["source_id"]: row for row in ctx.tables["sources"]}
    inject_claims = [row for row in ctx.tables["claims"]
                     if sources[row["source_id"]]["batch"] > 0 and row.get("truth_claim_id")]
    risk_levels = ["low", "moderate", "significant", "high"]
    examples = []
    for i in range(24):
        claim = inject_claims[i % len(inject_claims)]
        level = risk_levels[i % 4]
        tier = {"low": "tier_1", "moderate": "tier_2", "significant": "tier_3", "high": "tier_4"}[level]
        cost = round((i % 5) / 5, 2)
        impact = round(((i * 3) % 7) / 7, 2)
        examples.append({"decision_id": f"dec_ex_{i + 1:03d}",
            "recommendation_type": recommendation_types[i % 4], "object_id": claim["truth_claim_id"],
            "evidence_claim_ids": [claim["claim_id"]], "action_cost": cost, "objective_impact": impact,
            "risk_score": round(0.4 * cost + 0.6 * impact, 4), "risk_level": level, "tier_id": tier,
            "decided_by": next(row["approver_role"] for row in tiers if row["tier_id"] == tier),
            "decision": ["approved", "deferred", "denied"][i % 3],
            "decided_at": sources[claim["source_id"]]["published_at"], "resumed_from_decision_id": None})
    decision_props = {"decision_id": STR, "recommendation_type": {"enum": recommendation_types}, "object_id": STR,
        "evidence_claim_ids": {"type": "array", "items": STR}, "action_cost": {"type": "number", "minimum": 0, "maximum": 1},
        "objective_impact": {"type": "number", "minimum": 0, "maximum": 1}, "risk_score": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_level": {"enum": risk_levels}, "tier_id": STR, "decided_by": STR,
        "decision": {"enum": ["approved", "deferred", "denied"]}, "decided_at": {"type": "string", "format": "date"},
        "resumed_from_decision_id": NULL_STR}
    schemas = {
        "authority_tiers": _schema(["tier_id", "name", "approver_role", "max_reversibility_cost"], {"tier_id": STR, "name": {"enum": [row["name"] for row in tiers]}, "approver_role": STR, "max_reversibility_cost": {"type": "number", "minimum": 0, "maximum": 1}}),
        "action_authority": _schema(["tactic_class", "tier_id"], {"tactic_class": STR, "tier_id": STR}),
        "recommendation_authority": _schema(["recommendation_type", "tier_id", "risk_level_threshold"], {"recommendation_type": {"enum": recommendation_types}, "tier_id": STR, "risk_level_threshold": {"enum": risk_levels}}),
        "decision_log": _schema(list(decision_props), decision_props),
        "example_decisions": _schema(list(decision_props), decision_props),
    }
    evaluator = '''"""Reference authority routing."""
ORDER = {"low": 1, "moderate": 2, "significant": 3, "high": 4}
def route(risk_level):
    return f"tier_{ORDER[risk_level]}"
'''
    _emit(ctx.dataset_dir, "authority",
          {"authority_tiers": tiers, "action_authority": action, "recommendation_authority": recommendation,
           "decision_log": [], "example_decisions": examples}, schemas,
          "Mission Authority Broker",
          ["Four role-named tiers route actions and recommendations by reversibility and risk.",
           "The decision log ships empty; 24 inject-derived examples are provided separately."],
          ["claims", "harmful_events", "risk_assessments", "actions"],
          {"routing.py": evaluator, "result.json": json.dumps({"truth_vs_truth": 1.0, "examples": 24}, indent=2)})


def _collection_assets(ctx) -> None:
    disciplines = ["GEOINT", "SIGINT", "HUMINT", "OSINT", "MASINT"]
    assets = [
        {"asset_id": f"asset_{i + 1:02d}", "name": name, "owner_org": owner,
         "capacity_per_period": 1 + i % 2, "cost_per_task": round(0.1 + i * 0.05, 2)}
        for i, (name, owner) in enumerate([
            ("Northstar imaging section", "Meridian Surveillance Detachment"),
            ("Tern signals team", "Joint Task Force Meridian J-2"),
            ("Harbor liaison network", "Ilmaran partner cell"),
            ("Open-source watch", "Joint Task Force Meridian J-2"),
            ("Spectral survey flight", "Auberon Air Expeditionary Wing"),
            ("Kestrel patrol reporting", "Task Group Kestrel"),
            ("Halden observation team", "Halden Brigade"),
            ("Grid technical liaison", "Ilmaran partner cell"),
        ])
    ]
    requirements = ctx.tables["collection_requirements"]
    coverage = []
    for i, asset in enumerate(assets):
        for j in range(3):
            req = requirements[(i + j * 2) % len(requirements)]
            coverage.append({"coverage_id": f"cov_{i + 1:02d}_{j + 1}", "asset_id": asset["asset_id"],
                "subject_type": None, "entity_id": req["subject_id"], "predicate": req["predicate"],
                "discipline": disciplines[(i + j) % len(disciplines)], "p_success": round(0.45 + ((i + j) % 5) * 0.1, 2),
                "latency_periods": 1 + (i + j) % 3, "target_characteristics_match": (i + j) % 4 != 0,
                "range_ok": (i + j) % 5 != 0, "timeliness_ok": (i + j) % 3 != 0})
    priority = {row["req_id"]: float(row.get("priority") or 0.01) for row in requirements}
    req_for = {(row["subject_id"], row["predicate"]): row["req_id"] for row in requirements}
    choices = []
    for row in coverage:
        req_id = req_for[(row["entity_id"], row["predicate"])]
        value = priority[req_id] * row["p_success"]
        choices.append((value, row, req_id))
    capacity = {row["asset_id"]: row["capacity_per_period"] for row in assets}
    plan = []
    for value, row, req_id in sorted(choices, key=lambda item: (-item[0], item[1]["asset_id"], item[2])):
        if capacity[row["asset_id"]] <= 0:
            continue
        capacity[row["asset_id"]] -= 1
        plan.append({"period": 1, "asset_id": row["asset_id"], "req_id": req_id,
                     "coverage_id": row["coverage_id"], "objective_contribution": round(value, 9)})
    objective = round(sum(row["objective_contribution"] for row in plan), 9)
    task_props = {"period": {"type": "integer", "minimum": 1}, "asset_id": STR, "req_id": STR}
    schemas = {
        "assets": _schema(["asset_id", "name", "owner_org", "capacity_per_period", "cost_per_task"], {"asset_id": STR, "name": STR, "owner_org": STR, "capacity_per_period": {"type": "integer", "minimum": 1}, "cost_per_task": {"type": "number", "minimum": 0}}),
        "asset_coverage": _schema(["coverage_id", "asset_id", "subject_type", "entity_id", "predicate", "discipline", "p_success", "latency_periods", "target_characteristics_match", "range_ok", "timeliness_ok"], {"coverage_id": STR, "asset_id": STR, "subject_type": NULL_STR, "entity_id": NULL_STR, "predicate": STR, "discipline": {"enum": disciplines}, "p_success": {"type": "number", "minimum": 0, "maximum": 1}, "latency_periods": {"type": "integer", "minimum": 0}, "target_characteristics_match": BOOL, "range_ok": BOOL, "timeliness_ok": BOOL}),
        "tasking_plan": _schema(list(task_props), task_props),
    }
    baseline = '''"""Greedy collection baseline: select EVPI-times-success in descending order."""
def objective(plan):
    return sum(row["objective_contribution"] for row in plan)
'''
    _emit(ctx.dataset_dir, "collection_assets",
          {"assets": assets, "asset_coverage": coverage, "tasking_plan": []}, schemas,
          "Dynamic Collection Resource Optimization",
          ["Eight fictional assets offer overlapping multi-discipline coverage with capacity and cost limits.",
           "The greedy baseline maximizes requirement priority times success probability subject to asset capacity."],
          ["collection_requirements", "pirs", "entities", "assumptions"],
          {"baseline.py": baseline, "greedy_plan.jsonl": "\n".join(json.dumps(row, sort_keys=True) for row in plan),
           "result.json": json.dumps({"truth_vs_truth": 1.0, "objective_value": objective, "tasks": len(plan)}, indent=2)})


def _events(ctx) -> None:
    entities = [row["entity_id"] for row in ctx.tables["entities"] if row["entity_type"] in {"unit", "system", "infrastructure"}]
    locations = [row["entity_id"] for row in ctx.tables["entities"] if row["entity_type"] == "location"]
    streams = ["ais_like", "rf_like", "social_like"]
    start = datetime(2026, 9, 8, tzinfo=timezone.utc)
    events = []
    for i in range(600):
        truth = entities[(i * 7) % len(entities)]
        stream = streams[i % 3]
        events.append({"event_id": f"evt_{i + 1:04d}",
            "ts": (start + timedelta(minutes=i * 17)).isoformat().replace("+00:00", "Z"),
            "stream": stream, "entity_id": None if i % 5 in {0, 1} else truth,
            "location_id": locations[(i * 5) % len(locations)],
            "payload": {"sequence": i + 1, "signal": ["transit", "emission", "report"][i % 3], "quality": round(0.55 + (i % 10) * 0.04, 2)},
            "truth_entity_id": truth})
    schema = _schema(["event_id", "ts", "stream", "entity_id", "location_id", "payload", "truth_entity_id"],
        {"event_id": STR, "ts": {"type": "string", "format": "date-time"}, "stream": {"enum": streams},
         "entity_id": NULL_STR, "location_id": STR, "payload": {"type": "object"}, "truth_entity_id": STR})
    scorer = '''"""Entity-resolution accuracy for events with withheld observed IDs."""
def score(predictions, truth):
    expected = {row["event_id"]: row["truth_entity_id"] for row in truth}
    return sum(expected.get(row["event_id"]) == row.get("entity_id") for row in predictions) / max(1, len(expected))
'''
    _emit(ctx.dataset_dir, "events", {"events": events}, {"events": schema},
          "Multi-INT Fusion",
          ["Six hundred AIS-like, RF-like, and social-like events reference the fictional base entities.",
           "Observed entity IDs are withheld on 40 percent of rows; truth IDs support resolution scoring."],
          ["entities", "facts", "claims"],
          {"score.py": scorer, "result.json": json.dumps({"truth_vs_truth": 1.0, "events": 600}, indent=2)})


def build(ctx) -> None:
    _rag(ctx)
    _target_systems(ctx)
    _capability(ctx)
    _authority(ctx)
    _collection_assets(ctx)
    _events(ctx)
