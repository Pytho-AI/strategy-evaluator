"""The finite Bayesian game u(sigma, sigma', theta) for AMBER SHIELD. Structured, not random.

    u(sigma, sigma', theta)[o] = floor(sigma)[o] + sum_k theta_k * delta_k(sigma)[o]
                                 + resilience(sigma) * shift(sigma')[o]

with `delta_k(sigma)` nonzero exactly when assumption k is in that COA's `deps` (COA_LIB), and
`floor(sigma) = AUTHORED(sigma) - sum_k delta_k(sigma)` so that the all-assumptions-hold payoff is
exactly the authored table. No RNG anywhere: two builds are byte-identical by construction.

Objective mapping (the UI's five comparison criteria onto COA_LIB's authored constants)
---------------------------------------------------------------------------------------
`app/ui/src/app.logic.js::compute()` derives each criterion's JRAM risk level from one authored
constant, so the mapping is read straight off that function:

    rm  risk to mission     level(1 - pSuccess)  <- `s`     higher s is better  -> obj_mission
    rp  risk to personnel   level(cas90)         <- `cas`   lower cas is better -> obj_personnel
    re  escalation risk     level(pEsc)          <- `esc`   lower esc is better -> obj_escalation
    rt  risk to time        level(days)          <- `days`  fewer days better   -> obj_time
    rr  risk to resources   level(res)           <- `res`   lower res is better -> obj_resources

Each constant is mapped linearly onto [0.15, 0.85] over the range the five COAs span, with the
sense flipped for the four "lower is better" constants. That preserves the UI's authored ordering
on every criterion exactly while making the five criteria commensurate so the weight vector means
something. The resulting standing matches the UI's intent: COA 1 best on mission, COA 5 best on
personnel, escalation and resources, COA 4 best on time and worst on escalation, COA 1 worst on
resources, COA 5 worst on mission and time.
"""
from __future__ import annotations

from .scenario import COAS, RED_COAS

# COA_LIB's authored constants, verbatim: (s, cas, esc, days, res)
AUTHORED = {
    "str_coa_1": dict(s=0.72, cas=2.1, esc=0.34, days=60, res=88),
    "str_coa_2": dict(s=0.64, cas=1.4, esc=0.20, days=95, res=80),
    "str_coa_3": dict(s=0.58, cas=1.6, esc=0.26, days=80, res=75),
    "str_coa_4": dict(s=0.66, cas=1.5, esc=0.52, days=55, res=70),
    "str_coa_5": dict(s=0.41, cas=0.6, esc=0.10, days=120, res=60),
}
# objective -> (COA_LIB field, higher_is_better)
CRITERION_FIELD = {
    "obj_mission": ("s", True),
    "obj_personnel": ("cas", False),
    "obj_escalation": ("esc", False),
    "obj_time": ("days", False),
    "obj_resources": ("res", False),
}
U_LOW, U_HIGH = 0.15, 0.85

# How much each assumption bears on each criterion, as a profile over
# (mission, personnel, escalation, time, resources). Scaled by the per-COA magnitude below.
PROFILE = {
    0: {"obj_mission": 1.0, "obj_personnel": 0.1, "obj_escalation": 0.3, "obj_time": 0.2, "obj_resources": 0.0},
    1: {"obj_mission": 0.4, "obj_personnel": 0.1, "obj_escalation": 0.0, "obj_time": 1.0, "obj_resources": 0.4},
    2: {"obj_mission": 0.2, "obj_personnel": 0.5, "obj_escalation": 1.0, "obj_time": 0.0, "obj_resources": 0.1},
    3: {"obj_mission": 0.6, "obj_personnel": 0.2, "obj_escalation": 0.0, "obj_time": 1.0, "obj_resources": 0.6},
    4: {"obj_mission": 0.5, "obj_personnel": 0.2, "obj_escalation": 0.0, "obj_time": 0.7, "obj_resources": 1.0},
    5: {"obj_mission": 0.3, "obj_personnel": 0.6, "obj_escalation": 1.0, "obj_time": 0.0, "obj_resources": 0.0},
    6: {"obj_mission": 0.6, "obj_personnel": 0.6, "obj_escalation": 0.2, "obj_time": 0.5, "obj_resources": 0.0},
    7: {"obj_mission": 0.5, "obj_personnel": 0.2, "obj_escalation": 0.1, "obj_time": 0.6, "obj_resources": 0.2},
}
# Per-COA dependency magnitude. Keys are index_k; the set must equal COA_LIB `deps` minus one.
# The largest magnitude in each row is the COA's dominant dependency:
#   COA 1 on A4 (the C+21 closure the whole plan is built around)
#   COA 2 on A6 (nuclear signalling staying signalling across a long deliberate delay)
#   COA 3 on A7 (Belarusian forces staying uncommitted while the corridor is the main effort)
#   COA 4 on A3 (no horizontal escalation once Kaliningrad is struck)
#   COA 5 on A3 (the whole theory of victory is that Russia stays below the escalation ceiling)
MAGNITUDE = {
    "str_coa_1": {0: 0.06, 1: 0.08, 3: 0.20, 4: 0.10},
    "str_coa_2": {0: 0.16, 3: 0.06, 5: 0.20, 7: 0.05},
    "str_coa_3": {1: 0.10, 3: 0.08, 6: 0.24},
    "str_coa_4": {0: 0.07, 2: 0.20, 5: 0.16},
    "str_coa_5": {0: 0.10, 2: 0.22, 6: 0.10, 7: 0.06},
}
# What each Russian COA does to Blue's five criteria, and how exposed each Blue COA is to it.
OPPONENT_SHIFT = {
    "str_rus_ml": {"obj_mission": 0.02, "obj_personnel": 0.02, "obj_escalation": 0.01, "obj_time": -0.01, "obj_resources": 0.00},
    "str_rus_md": {"obj_mission": -0.08, "obj_personnel": -0.10, "obj_escalation": -0.06, "obj_time": -0.05, "obj_resources": -0.04},
    "str_rus_alt": {"obj_mission": -0.03, "obj_personnel": -0.04, "obj_escalation": -0.08, "obj_time": -0.02, "obj_resources": -0.03},
}
RESILIENCE = {"str_coa_1": 1.00, "str_coa_2": 0.90, "str_coa_3": 1.05, "str_coa_4": 1.30, "str_coa_5": 0.70}

# Red side. Two objectives; K = 1 (the single Red assumption on Allied munition stocks).
RED_BASE = {
    "str_rus_ml": {"obj_rus_territory": 0.62, "obj_rus_preserve": 0.70},
    "str_rus_md": {"obj_rus_territory": 0.74, "obj_rus_preserve": 0.44},
    "str_rus_alt": {"obj_rus_territory": 0.55, "obj_rus_preserve": 0.58},
}
# theta_0 = 1 means Allied stocks hold: worse for Russia.
RED_DELTA = {
    "str_rus_ml": {"obj_rus_territory": -0.08, "obj_rus_preserve": -0.04},
    "str_rus_md": {"obj_rus_territory": -0.14, "obj_rus_preserve": -0.10},
    "str_rus_alt": {"obj_rus_territory": -0.06, "obj_rus_preserve": -0.09},
}
# What each Blue COA costs Russia, applied to both Red objectives.
RED_OPPONENT_SHIFT = {"str_coa_1": -0.06, "str_coa_2": -0.04, "str_coa_3": -0.03, "str_coa_4": -0.09, "str_coa_5": 0.02}

BLUE_DEPS = {sid: sorted(d - 1 for d in deps) for sid, _ui, _n, _a, deps, *_ in COAS}
K_BLUE = 8
K_RED = 1


def authored_utility() -> dict[str, dict[str, float]]:
    """COA_LIB's constants mapped onto [0.15, 0.85] per criterion, sense-corrected."""
    out: dict[str, dict[str, float]] = {sid: {} for sid in AUTHORED}
    for oid, (field, higher_better) in CRITERION_FIELD.items():
        values = [AUTHORED[sid][field] for sid in AUTHORED]
        lo, hi = min(values), max(values)
        for sid in AUTHORED:
            x = AUTHORED[sid][field]
            frac = (x - lo) / (hi - lo) if higher_better else (hi - x) / (hi - lo)
            out[sid][oid] = U_LOW + (U_HIGH - U_LOW) * frac
    return out


def delta(sid: str, k: int) -> dict[str, float]:
    """delta_k(sigma): zero unless k is one of the COA's COA_LIB dependencies."""
    m = MAGNITUDE[sid].get(k)
    if m is None:
        return {oid: 0.0 for oid in CRITERION_FIELD}
    return {oid: m * PROFILE[k][oid] for oid in CRITERION_FIELD}


def floor_utility() -> dict[str, dict[str, float]]:
    """The payoff when every assumption the COA depends on has failed."""
    top = authored_utility()
    return {sid: {oid: top[sid][oid] - sum(delta(sid, k)[oid] for k in BLUE_DEPS[sid]) for oid in CRITERION_FIELD}
            for sid in AUTHORED}


def _world_bits(k: int) -> list[str]:
    from itertools import product
    return ["".join(str(b) for b in bits) for bits in product([0, 1], repeat=k)]


def build(objective_order_blue: list[str], objective_order_red: list[str]) -> list[dict]:
    """Every (strategy, opponent strategy, world) triple exactly once, utility in `objective_order`."""
    base = floor_utility()
    rows: list[dict] = []
    for sid in [c[0] for c in COAS]:
        for osid in [r[0] for r in RED_COAS]:
            for world in _world_bits(K_BLUE):
                u = dict(base[sid])
                for k, bit in enumerate(world):
                    if bit == "1":
                        d = delta(sid, k)
                        for oid in u:
                            u[oid] += d[oid]
                for oid in u:
                    u[oid] += RESILIENCE[sid] * OPPONENT_SHIFT[osid][oid]
                rows.append(dict(strategy_id=sid, opponent_strategy_id=osid, world=world,
                                 utility=[round(u[oid], 9) for oid in objective_order_blue]))
    for sid in [r[0] for r in RED_COAS]:
        for osid in [c[0] for c in COAS]:
            for world in _world_bits(K_RED):
                u = {oid: RED_BASE[sid][oid] + (RED_DELTA[sid][oid] if world == "1" else 0.0)
                        + RED_OPPONENT_SHIFT[osid] for oid in RED_BASE[sid]}
                rows.append(dict(strategy_id=sid, opponent_strategy_id=osid, world=world,
                                 utility=[round(u[oid], 9) for oid in objective_order_red]))
    return rows


__all__ = ["AUTHORED", "BLUE_DEPS", "CRITERION_FIELD", "K_BLUE", "K_RED", "MAGNITUDE",
           "authored_utility", "build", "delta", "floor_utility"]
