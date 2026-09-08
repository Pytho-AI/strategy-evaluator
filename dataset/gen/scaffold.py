"""Stage 1: entities, geography, resources, actions, objectives, games (theater), guidance, PIRs."""
from __future__ import annotations

import re

from gen import scenario_data as S
from gen.context import Ctx


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build(ctx: Ctx) -> None:
    for eid, et, name, aliases, parent, desc in S.ACTORS + S.POLITIES:
        ctx.add("entities", {"entity_id": eid, "entity_type": et, "canonical_name": name, "aliases": aliases, "parent_id": parent, "description": desc})
    for lid, name, aliases, desc in S.LOCATIONS:
        ctx.add("entities", {"entity_id": lid, "entity_type": "location", "canonical_name": name, "aliases": aliases, "parent_id": None, "description": desc})
    for iid, name, aliases, loc, desc in S.INFRA:
        ctx.add("entities", {"entity_id": iid, "entity_type": "infrastructure", "canonical_name": name, "aliases": aliases, "parent_id": None, "description": desc})
    for uid, name, aliases, parent, loc, rdy, desc in S.UNITS:
        ctx.add("entities", {"entity_id": uid, "entity_type": "unit", "canonical_name": name, "aliases": aliases, "parent_id": parent, "description": desc})
    for parent, subs in S.SUBUNITS.items():
        for name, alias in subs:
            ctx.add("entities", {"entity_id": f"unit_{slug(name)}", "entity_type": "unit", "canonical_name": name, "aliases": [alias], "parent_id": parent,
                                 "description": f"element of {ctx.get('entities', entity_id=parent)['canonical_name']}"})
    for sid, name, aliases, unit, rng, cnt, desc in S.SYSTEMS:
        ctx.add("entities", {"entity_id": sid, "entity_type": "system", "canonical_name": name, "aliases": aliases, "parent_id": None, "description": desc})
    for rid, name, aliases, desc in S.ROLES:
        ctx.add("entities", {"entity_id": rid, "entity_type": "organization_role", "canonical_name": name, "aliases": aliases, "parent_id": None, "description": desc})
    for pid, name, aliases, loc in S.PROBLEM_SET_ENTITIES:
        ctx.add("entities", {"entity_id": pid, "entity_type": "problem_set", "canonical_name": name, "aliases": aliases, "parent_id": None, "description": f"JRAM problem set centred on {ctx.get('entities', entity_id=loc)['canonical_name']}"})

    # game form
    ctx.add("games", {"game_id": "meridian", "name": "Meridian Sea theater", "actor_ids": ["ent_blue", "ent_varenia"], "horizon": 6,
                      "horizon_map": S.HORIZON_MAP, "state_variables": S.STATE_VARIABLES, "observables": S.OBSERVABLES})
    for rid, name, unit in S.RESOURCES:
        ctx.add("resources", {"resource_id": rid, "game_id": "meridian", "name": name, "unit": unit})
    for aid, actor, name, tc, loe, mech, cost, effects in S.ACTIONS:
        ctx.add("actions", {"action_id": aid, "game_id": "meridian", "actor_id": actor, "name": name, "tactic_class": tc, "line_of_effort": loe,
                            "mechanism": mech, "cost": cost, "preconditions": True, "effects": effects})
    # guidance chain first (objectives reference it), objectives after
    for gid, ptype, title, role, parent, objs in S.GUIDANCE:
        ctx.add("guidance", {"guidance_id": gid, "product_type": ptype, "title": title, "issuing_role": role, "parent_guidance_id": parent, "objective_ids": objs, "source_id": None})
    for oid, actor, name, kind, gid, parent, metric, asp, stmt in S.OBJECTIVES:
        ctx.add("objectives", {"objective_id": oid, "game_id": "meridian", "actor_id": actor, "name": name, "kind": kind, "guidance_id": gid,
                               "parent_objective_id": parent, "metric": metric, "direction": "max", "aspiration": asp, "statement": stmt})
    for pid, stmt, role, rank in S.PIRS:
        ctx.add("pirs", {"pir_id": pid, "statement": stmt, "commander_role": role, "priority_rank": rank, "decision_point_ids": []})
