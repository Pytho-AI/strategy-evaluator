"""Stage 2: the canonical world (facts) with valid-time intervals, backstory changes, future
projections and the three inject change clusters. Documents are rendered from these later."""
from __future__ import annotations

from datetime import timedelta

from eval.value import derived_confidence
from gen import scenario_data as S
from gen.context import Ctx
from gen.scaffold import slug
from gen.vocab import PREDICATES


def _vt(pred: str, v):
    vt = PREDICATES[pred][0]
    return vt, PREDICATES[pred][1]


class FactBuilder:
    def __init__(self, ctx: Ctx):
        self.ctx = ctx
        self.current: dict[tuple[str, str, str | None], dict] = {}  # (subject, predicate, object) -> open fact
        self.by_key: dict[tuple[str, str], list[dict]] = {}

    def add(self, subject, pred, value, from_day, estimative=False, likelihood=None, confidence="high", to_day=None, batch=0, supersedes=None):
        vt, unit = _vt(pred, value)
        row = {
            "fact_id": self.ctx.next_id("fct"), "subject_id": subject, "predicate": pred,
            "object_id": value if vt == "entity" else None, "value": None if vt == "entity" else value, "value_type": vt, "unit": unit,
            "valid_from": self.ctx.day(from_day), "valid_to": self.ctx.day(to_day) if to_day is not None else None,
            "estimative": estimative, "likelihood_icd203": likelihood, "confidence_icd203": confidence,
            "confidence": derived_confidence(estimative, likelihood, confidence),
            "supersedes_fact_id": supersedes, "first_asserted_batch": batch,
        }
        d = self.ctx.add("facts", row)
        self.by_key.setdefault((subject, pred), []).append(d)
        return d

    def latest(self, subject, pred):
        rows = self.by_key.get((subject, pred), [])
        return max(rows, key=lambda r: r["valid_from"]) if rows else None

    def change(self, subject, pred, new_value, from_day, batch, estimative=False, likelihood=None, confidence="high"):
        """Close the currently open fact the day before and open the new one (a change event)."""
        old = self.latest(subject, pred)
        if old is not None and old["valid_to"] is None:
            old["valid_to"] = (self.ctx.day(from_day) - timedelta(days=1)).isoformat()
        # An expired report followed by a gap is new information, not an adjacent change event.
        adjacent = old is not None and old["valid_to"] == (self.ctx.day(from_day) - timedelta(days=1)).isoformat()
        return self.add(subject, pred, new_value, from_day, estimative, likelihood, confidence, batch=batch,
                        supersedes=old["fact_id"] if adjacent else None)


def build(ctx: Ctx) -> None:
    fb = FactBuilder(ctx)
    ent = {e["entity_id"]: e for e in ctx.tables["entities"]}
    base_keys = {(s, p) for s, p, *_ in S.BASE_FACTS}
    unit_loc = {u[0]: u[4] for u in S.UNITS}
    unit_rdy = {u[0]: u[5] for u in S.UNITS}

    # 1. explicit base facts (backstory-valid)
    for subject, pred, value, est, lik, conf, from_day in S.BASE_FACTS:
        fb.add(subject, pred, value, from_day, est, lik, conf)
    for subject, pred, to_day in S.EXPIRES:
        fb.latest(subject, pred)["valid_to"] = ctx.day(to_day).isoformat()

    # 2. programmatic facts: locations/infrastructure/units/systems/problem sets
    def default(subject, pred, value, from_day=S.BACKSTORY_DAY, conf="high"):
        if (subject, pred) in base_keys:
            return
        fb.add(subject, pred, value, from_day, False, None, conf)

    for lid, *_ in S.LOCATIONS:
        default(lid, "status", "operational")
    for iid, name, aliases, loc, desc in S.INFRA:
        default(iid, "located_at", loc)
        default(iid, "status", "operational")
    for uid, name, aliases, parent, loc, rdy, desc in S.UNITS:
        default(uid, "located_at", loc, from_day=-45 if uid in ("unit_tg_kestrel", "unit_halden_brigade") else S.BACKSTORY_DAY)
        default(uid, "subordinate_to", parent)
        default(uid, "readiness", rdy, from_day=-30, conf="moderate")
        default(uid, "status", "operational", conf="moderate" if rdy < 0.6 else "high")
    i = 0
    for parent, subs in S.SUBUNITS.items():
        for name, alias in subs:
            uid = f"unit_{slug(name)}"
            i += 1
            jitter = ((i * 7) % 11 - 5) / 100.0  # deterministic, in [-0.05, 0.05]
            default(uid, "located_at", unit_loc[parent], from_day=-45 if parent == "unit_tg_kestrel" else S.BACKSTORY_DAY)
            default(uid, "subordinate_to", parent)
            default(uid, "readiness", round(min(0.98, max(0.3, unit_rdy[parent] + jitter)), 2), from_day=-30, conf="moderate")
            default(uid, "status", "operational", conf="moderate")
    for sid, name, aliases, unit, rng, cnt, desc in S.SYSTEMS:
        default(sid, "operated_by", unit)
        default(sid, "located_at", unit_loc[unit])
        if rng is not None:
            default(sid, "range_km", rng, conf="moderate" if sid.startswith("sys_dorne") or sid.startswith("sys_serath") else "high")
        if sid == "sys_dorne_asm":
            fb.add(sid, "count", 8, S.BACKSTORY_DAY, False, None, "moderate")  # superseded by the backstory change below
        else:
            default(sid, "count", cnt, conf="moderate")
        default(sid, "status", "operational", conf="moderate")
    for pid, name, aliases, loc in S.PROBLEM_SET_ENTITIES:
        default(pid, "located_at", loc, from_day=-30)

    # 3. backstory change events (pre-T0)
    for subject, pred, old, new, day in S.BACKSTORY_CHANGES:
        cur = fb.latest(subject, pred)
        if cur is None:
            fb.add(subject, pred, old, S.BACKSTORY_DAY, False, None, "moderate", to_day=day - 1)
        elif cur["value"] == new or cur["object_id"] == new:
            # the base fact already holds the new value: insert the older fact before it
            cur["valid_from"] = ctx.day(day).isoformat()
            older = fb.add(subject, pred, old, S.BACKSTORY_DAY, False, None, "moderate", to_day=day - 1)
            cur["supersedes_fact_id"] = older["fact_id"]
            continue
        else:
            cur["valid_to"] = ctx.day(day - 1).isoformat()
            if cur["value"] != old and cur["object_id"] != old:
                cur["value" if cur["value_type"] != "entity" else "object_id"] = old
        fb.add(subject, pred, new, day, False, None, "high", supersedes=fb.latest(subject, pred)["fact_id"] if fb.latest(subject, pred) is not None and fb.latest(subject, pred)["valid_to"] else None)

    # 4. future projections (estimative facts valid after T0)
    for subject, pred, value, from_day, lik, conf in S.FUTURE_FACTS:
        cur = fb.latest(subject, pred)
        if cur is not None and cur["valid_to"] is None:
            cur["valid_to"] = (ctx.day(from_day) - timedelta(days=1)).isoformat()
        fb.add(subject, pred, value, from_day, True, lik, conf, supersedes=cur["fact_id"] if cur else None)

    # 5. inject change events
    for batch, changes in sorted(S.INJECT_CHANGES.items()):
        for subject, pred, value, from_day, est, lik, conf in changes:
            fb.change(subject, pred, value, from_day, batch, est, lik, conf)
    ctx.fact_builder = fb  # later stages reuse the index
