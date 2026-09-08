"""Strategy value, sensitivity, robustness, EVPI, assumption probability/status, derived confidence.

Definitions (SCHEMA.md §computed):
  worlds theta in {0,1}^K, P(theta) = prod_k p_k^theta_k (1-p_k)^(1-theta_k)
  V(sigma)          = rho over (theta ~ P, sigma' ~ Sigma_-i) of w.u(sigma, sigma', theta)
  Sensitivity_k     = V(sigma | theta_k=1) - V(sigma | theta_k=0)
  Robustness(sigma) = min_theta E_{sigma'}[w.u]
  EVPI_k            = E_{theta_k}[max_sigma V(sigma|theta_k)] - max_sigma E_{theta_k}[V(sigma|theta_k)]
rho: expected | cvar (mean of the worst alpha probability mass of w.u) | minimax (min over support).
"""
from __future__ import annotations

from datetime import date
from itertools import product
from typing import Optional

from eval.claimset import ClaimSet, satisfies

# ---------------------------------------------------------------- ICD 203 derived confidence
ICD203_MID = {
    "almost_no_chance": 0.03, "very_unlikely": 0.125, "unlikely": 0.325, "roughly_even_chance": 0.50,
    "likely": 0.675, "very_likely": 0.875, "almost_certain": 0.97,
}
SHRINK = {"high": 0.0, "moderate": 0.15, "low": 0.35}
FACTUAL_BASE = 0.97


def derived_confidence(estimative: bool, likelihood_icd203: Optional[str], confidence_icd203: str) -> float:
    """confidence = 0.5 + (1 - s) * (mid - 0.5); mid = ICD band midpoint (estimative) or 0.97 (factual);
    s = shrink factor by confidence level (high 0.0, moderate 0.15, low 0.35)."""
    mid = ICD203_MID[likelihood_icd203] if estimative else FACTUAL_BASE
    s = SHRINK[confidence_icd203]
    return round(0.5 + (1.0 - s) * (mid - 0.5), 6)


# ---------------------------------------------------------------- worlds
def world_bits(K: int) -> list[str]:
    return ["".join(str(b) for b in bits) for bits in product([0, 1], repeat=K)]


def world_prob(world: str, p: list[float]) -> float:
    pr = 1.0
    for ch, pk in zip(world, p):
        pr *= pk if ch == "1" else (1.0 - pk)
    return pr


def conditioned_world_probs(p: list[float], K: int, cond: Optional[dict[int, int]] = None) -> dict[str, float]:
    """P(theta | theta_k = b for (k,b) in cond); independence makes this a product with fixed bits."""
    cond = cond or {}
    out: dict[str, float] = {}
    for w in world_bits(K):
        if any(int(w[k]) != b for k, b in cond.items()):
            continue
        pr = 1.0
        for k, ch in enumerate(w):
            if k in cond:
                continue
            pr *= p[k] if ch == "1" else (1.0 - p[k])
        out[w] = pr
    return out


def rho_apply(outcomes: list[tuple[float, float]], rho: str, alpha: Optional[float]) -> float:
    """outcomes: (probability, scalar payoff). Probabilities sum to 1."""
    if rho == "expected":
        return sum(pr * x for pr, x in outcomes)
    if rho == "minimax":
        return min(x for pr, x in outcomes if pr > 0)
    if rho == "cvar":
        a = alpha if alpha is not None else 0.2
        if not 0 < a <= 1:
            raise ValueError("CVaR alpha must be in (0, 1]")
        xs = sorted(outcomes, key=lambda t: t[1])
        mass, acc = 0.0, 0.0
        for pr, x in xs:
            if pr <= 0:
                continue
            take = min(pr, a - mass)
            if take <= 0:
                break
            acc += take * x
            mass += take
        return acc / mass if mass > 0 else min(x for _, x in xs)
    raise ValueError(rho)


class PayoffIndex:
    def __init__(self, payoffs: list[dict]):
        self.u: dict[tuple[str, str, str], list[float]] = {}
        for r in payoffs:
            self.u[(r["strategy_id"], r["opponent_strategy_id"], r["world"])] = r["utility"]

    def get(self, sid: str, osid: str, world: str) -> list[float]:
        return self.u[(sid, osid, world)]


def dot(w: list[float], u: list[float]) -> float:
    return sum(a * b for a, b in zip(w, u))


def outcomes_for(sid: str, idx: PayoffIndex, w: list[float], opp: dict[str, float], p: list[float], K: int,
                 cond: Optional[dict[int, int]] = None) -> list[tuple[float, float]]:
    wp = conditioned_world_probs(p, K, cond)
    out = []
    for world, pw in wp.items():
        for osid, q in opp.items():
            out.append((pw * q, dot(w, idx.get(sid, osid, world))))
    return out


def value(sid: str, idx: PayoffIndex, w: list[float], opp: dict[str, float], p: list[float], K: int,
          rho: str = "expected", alpha: Optional[float] = None, cond: Optional[dict[int, int]] = None) -> float:
    return rho_apply(outcomes_for(sid, idx, w, opp, p, K, cond), rho, alpha)


def sensitivity(sid: str, k: int, idx: PayoffIndex, w, opp, p, K, rho="expected", alpha=None) -> float:
    return value(sid, idx, w, opp, p, K, rho, alpha, {k: 1}) - value(sid, idx, w, opp, p, K, rho, alpha, {k: 0})


def robustness(sid: str, idx: PayoffIndex, w, opp, K) -> float:
    worst = None
    for world in world_bits(K):
        e = sum(q * dot(w, idx.get(sid, osid, world)) for osid, q in opp.items())
        worst = e if worst is None else min(worst, e)
    return worst


def value_range(sid: str, idx: PayoffIndex, w, opp, p, K) -> list[float]:
    """[min, max] over the opponent's strategies of E_theta[w.u]: the stated uncertainty of V."""
    wp = conditioned_world_probs(p, K)
    vals = [sum(pw * dot(w, idx.get(sid, osid, world)) for world, pw in wp.items()) for osid in opp]
    return [min(vals), max(vals)]


def evpi(k: int, strategies: list[dict], idx: PayoffIndex, weights: dict[str, list[float]],
         opps: dict[str, dict[str, float]], p: list[float], K: int) -> float:
    """strategies: candidate strategy rows of one actor (each with risk_functional/risk_alpha)."""
    if not strategies:
        return 0.0
    def v(s, b):
        return value(s["strategy_id"], idx, weights[s["strategy_id"]], opps[s["strategy_id"]], p, K,
                     s["risk_functional"], s.get("risk_alpha"), {k: b})
    pk = p[k]
    learn = pk * max(v(s, 1) for s in strategies) + (1 - pk) * max(v(s, 0) for s in strategies)
    now = max(pk * v(s, 1) + (1 - pk) * v(s, 0) for s in strategies)
    return max(0.0, learn - now)


# ---------------------------------------------------------------- assumptions
def assumption_state(cs: ClaimSet, a: dict, as_of: date) -> tuple[float, str, Optional[dict]]:
    """Returns (p_holds, status, grounding claim). Rules (v2 §2.4, §2.5):
    unknown: no approved claim -> p = 0.5
    holds/violated: predicate satisfied or not by the current claim; p = confidence if satisfied else 1 - confidence
    stale: current claim's valid_to has passed (no claim valid at as_of but an approved one existed
           earlier) or confidence_icd203 == low; p computed from the latest claim."""
    c = cs.current(a["subject_id"], a["predicate"], as_of)
    if c is None:
        past = [r for r in cs.all(a["subject_id"], a["predicate"], known_at=as_of) if date.fromisoformat(r["valid_from"]) <= as_of]
        if not past:
            return 0.5, "unknown", None
        c = max(past, key=lambda r: r["valid_from"])
        sat = satisfies(cs.value_of(c), a["tolerance"]["op"], a["tolerance"]["value"])
        p = c["confidence"] if sat else 1.0 - c["confidence"]
        return round(p, 6), "stale", c
    sat = satisfies(cs.value_of(c), a["tolerance"]["op"], a["tolerance"]["value"])
    p = c["confidence"] if sat else 1.0 - c["confidence"]
    if c.get("confidence_icd203") == "low":
        return round(p, 6), "stale", c
    return round(p, 6), ("holds" if sat else "violated"), c
