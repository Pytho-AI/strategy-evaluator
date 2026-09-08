"""JP 5-0 Ch. III §(q) validity tests, made mechanical (v2 §2.2), and distinguishability."""
from __future__ import annotations

from typing import Optional

DIMS = ["main_effort", "scheme", "sequencing", "mechanism", "task_org", "reserves"]


def reachable_from(starts: set[str], edges: list[tuple[str, str]]) -> set[str]:
    seen = set(starts)
    frontier = list(starts)
    succ: dict[str, list[str]] = {}
    for a, b in edges:
        succ.setdefault(a, []).append(b)
    while frontier:
        n = frontier.pop()
        for m in succ.get(n, []):
            if m not in seen:
                seen.add(m)
                frontier.append(m)
    return seen


def test_suitable(strategy: dict, guidance: Optional[dict], deps_by_id: dict[str, dict], rules: list[dict]) -> tuple[bool, str]:
    """Every objective stated by guidance_source is reachable from the COA's actions along the
    theory-of-victory chain edges (action -enables-> claim -supports-> objective -supports-> ...)."""
    if guidance is None:
        return False, "no guidance_source: cannot show the COA accomplishes the mission within the commander's guidance"
    chain = [deps_by_id[e] for e in strategy.get("theory_of_victory", []) if e in deps_by_id]
    missing_edges = [e for e in strategy.get("theory_of_victory", []) if e not in deps_by_id]
    if missing_edges:
        return False, f"theory_of_victory references unknown edges {missing_edges}"
    edges = [(f"{d['from_type']}:{d['from_id']}", f"{d['to_type']}:{d['to_id']}") for d in chain]
    starts = {f"action:{r['action_id']}" for r in rules}
    reach = reachable_from(starts, edges)
    goals = [f"objective:{o}" for o in guidance.get("objective_ids", [])]
    unreached = [g.split(":", 1)[1] for g in goals if g not in reach]
    if not goals:
        return False, "guidance_source states no objectives"
    if unreached:
        return False, f"guidance objectives not reached by the theory-of-victory chain: {unreached}"
    return True, f"all {len(goals)} guidance objectives reached via {len(chain)} chain edges from {len(starts)} actions"


def worst_case_cost(rules: list[dict], actions_by_id: dict[str, dict], horizon: int) -> dict[str, float]:
    """Per resource, sum over periods of the maximum cost among rules active in that period
    (every trajectory the policy can generate costs at most this)."""
    total: dict[str, float] = {}
    for t in range(1, horizon + 1):
        active = [r for r in rules if not r.get("periods") or t in r["periods"]]
        per_res: dict[str, float] = {}
        for r in active:
            for res, c in actions_by_id[r["action_id"]].get("cost", {}).items():
                per_res[res] = max(per_res.get(res, 0.0), float(c))
        for res, c in per_res.items():
            total[res] = total.get(res, 0.0) + c
    return total


def test_feasible(strategy: dict, rules: list[dict], actions_by_id: dict[str, dict], budgets: dict[str, float], horizon: int) -> tuple[bool, str]:
    need = worst_case_cost(rules, actions_by_id, horizon)
    short = {r: (need[r], budgets.get(r, 0.0)) for r in need if need[r] > budgets.get(r, 0.0) + 1e-9}
    if short:
        txt = "; ".join(f"{r}: needs {n:g} > budget {b:g}" for r, (n, b) in short.items())
        return False, f"worst-case cumulative cost exceeds budget: {txt}"
    if not need:
        return True, "no resource costs on any trajectory"
    return True, "worst-case cumulative cost within budget for every resource: " + ", ".join(f"{r} {need[r]:g}/{budgets.get(r, 0.0):g}" for r in sorted(need))


def test_acceptable(value: float, aspiration: float, unmitigated_high: list[str]) -> tuple[bool, str]:
    if value < aspiration - 1e-12:
        return False, f"V = {value:.4f} below aspiration w·τ = {aspiration:.4f}"
    if unmitigated_high:
        return False, f"V = {value:.4f} >= aspiration {aspiration:.4f} but High Military Risk events not mitigated by this COA: {unmitigated_high}"
    return True, f"V = {value:.4f} >= aspiration w·τ = {aspiration:.4f}; no unmitigated High Military Risk event"


def dims_differing(sa: dict, sb: dict, rules_a: list[dict], rules_b: list[dict], actions_by_id: dict[str, dict]) -> list[str]:
    def classes(rules):
        return {actions_by_id[r["action_id"]]["tactic_class"] for r in rules}

    def mechs(rules):
        return {actions_by_id[r["action_id"]]["mechanism"] for r in rules}

    out = []
    if sa["main_effort"] != sb["main_effort"]:
        out.append("main_effort")
    if classes(rules_a) != classes(rules_b):
        out.append("scheme")
    if sa["sequencing"] != sb["sequencing"]:
        out.append("sequencing")
    if mechs(rules_a) != mechs(rules_b):
        out.append("mechanism")
    if set(sa.get("task_org", [])) != set(sb.get("task_org", [])):
        out.append("task_org")
    if sa["reserve_policy"] != sb["reserve_policy"]:
        out.append("reserves")
    return out


def test_distinguishable(strategy: dict, others: list[dict], rules_by_strategy: dict[str, list[dict]], actions_by_id: dict[str, dict]) -> tuple[bool, str, list[dict]]:
    rows = []
    worst = None
    for o in others:
        d = dims_differing(strategy, o, rules_by_strategy.get(strategy["strategy_id"], []), rules_by_strategy.get(o["strategy_id"], []), actions_by_id)
        rows.append({"strategy_a": strategy["strategy_id"], "strategy_b": o["strategy_id"], "dims_differing": d, "pass": len(d) >= 2})
        if worst is None or len(d) < len(worst[1]):
            worst = (o["strategy_id"], d)
    if not others:
        return True, "no alternative COA for this actor; distinguishability is vacuous", rows
    ok = all(r["pass"] for r in rows)
    if ok:
        return True, "differs from every other COA in >= 2 of {main effort, scheme, sequencing, mechanism, task organization, reserves}; " + "; ".join(f"vs {r['strategy_b']}: {r['dims_differing']}" for r in rows), rows
    return False, f"differs from {worst[0]} only in {worst[1]}", rows


def test_complete(strategy: dict, rules: list[dict], decision_points: list[dict]) -> tuple[bool, str]:
    fields = ["mission_who", "mission_what", "mission_when", "mission_where", "mission_why"]
    empty = [f for f in fields if not str(strategy.get(f, "")).strip()]
    if empty:
        return False, f"mission statement fields empty: {empty}"
    if not rules:
        return False, "no policy rules (no 'how')"
    if not strategy.get("end_state_objective_id"):
        return False, "no military end state"
    rule_ids = {r["rule_id"] for r in rules}
    bad = [dp["dp_id"] for dp in decision_points if not dp.get("branch_rule_ids") or not set(dp["branch_rule_ids"]) <= rule_ids]
    if bad:
        return False, f"decision points without a branch rule: {bad}"
    return True, f"who/what/when/where/why present, end state set, {len(rules)} rules cover how, {len(decision_points)} decision points each have a rule"
