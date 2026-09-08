"""Stage 3: the document plan. For each document: type, title, publication day, author, reliability,
credibility, the facts it asserts, the perturbations it carries. Every T0 fact is assigned to >= 1
document; assumption-grounding facts to >= 2 documents of different types. Products (risk context,
risk assessments, collection plans, COA statements, guidance) are planned by plan_products() once
strategies and risk exist."""
from __future__ import annotations

from dataclasses import dataclass, field

from gen import scenario_data as S
from gen.context import Ctx

INTEL_TYPES = ("reference_entry", "sitrep", "news", "message_traffic", "tabular", "assessment")

# facts whose (subject, predicate) ground an assumption: must appear in >= 2 docs of different types
KEY_FACTS = [("sys_dorne_asm", "range_km"), ("ent_varenia", "mobilization_days"), ("ent_corvane", "basing_access"),
             ("inf_kestrel_lane", "throughput_per_day"), ("ent_varenia", "cyber_capacity"), ("unit_meridian_log_group", "munitions_stock_days")]


@dataclass
class DocPlan:
    doc_id: str
    doc_type: str
    title: str
    published_day: int
    author_org: str
    reliability: str
    credibility: str
    batch: int = 0
    facts: list[str] = field(default_factory=list)          # current facts asserted (fact ids)
    echo_facts: list[str] = field(default_factory=list)     # superseded facts quoted as older reports (stale_echo)
    proposed: list[dict] = field(default_factory=list)      # unsupported claims (status proposed)
    perturbations: list[str] = field(default_factory=list)
    focus: list[str] = field(default_factory=list)          # entity ids the document is about
    extra: dict = field(default_factory=dict)


def _t0_facts(ctx: Ctx) -> list[dict]:
    t0 = ctx.t0.isoformat()
    out = []
    for f in ctx.tables["facts"]:
        if f["first_asserted_batch"] != 0:
            continue
        if f["subject_id"].startswith("ent_rps"):
            continue
        out.append(f)
    return out


def _current(ctx: Ctx, facts: list[dict]) -> list[dict]:
    """T0-current facts (valid at T0) plus future projections; superseded/expired ones are echoed."""
    t0 = ctx.t0.isoformat()
    return [f for f in facts if (f["valid_to"] is None or f["valid_to"] >= t0)]


def _superseded(ctx: Ctx, facts: list[dict]) -> list[dict]:
    t0 = ctx.t0.isoformat()
    return [f for f in facts if f["valid_to"] is not None and f["valid_to"] < t0]


def sel(facts, subjects=None, predicates=None, exclude_predicates=()):
    return [f["fact_id"] for f in facts if (subjects is None or f["subject_id"] in subjects) and (predicates is None or f["predicate"] in predicates)
            and f["predicate"] not in exclude_predicates]


def plan_intel(ctx: Ctx) -> list[DocPlan]:
    facts = _t0_facts(ctx)
    cur = _current(ctx, facts)
    old = _superseded(ctx, facts)
    ent = {e["entity_id"]: e for e in ctx.tables["entities"]}
    children = {}
    for e in ctx.tables["entities"]:
        if e.get("parent_id"):
            children.setdefault(e["parent_id"], []).append(e["entity_id"])
    by_key = {}
    for f in cur:
        by_key.setdefault((f["subject_id"], f["predicate"]), []).append(f["fact_id"])
    old_by_key = {(f["subject_id"], f["predicate"]): f["fact_id"] for f in old}
    future = [f["fact_id"] for f in cur if f["valid_from"] > ctx.t0.isoformat()]
    present = [f for f in cur if f["valid_from"] <= ctx.t0.isoformat()]
    plans: list[DocPlan] = []

    def add(doc_type, title, day, author, rel, cred, facts_, perts, focus, echo=(), proposed=(), **extra):
        plans.append(DocPlan(ctx.next_id("src"), doc_type, title, day, author, rel, cred, 0, list(dict.fromkeys(facts_)), list(echo), list(proposed), list(perts), list(focus), dict(extra)))

    def ent_facts(eid, preds=None, exclude=()):
        return sel(present, subjects=[eid], predicates=preds, exclude_predicates=exclude)

    J2 = "the supported combatant command J-2"
    # ---- reference entries (one per key entity; regenerated reference products)
    ref = [
        ("sys_dorne_asm", ["unit_var_coastal_msl_bde", "inf_dorne_radar"], ["paraphrase", "alias"], -3),
        ("sys_serath_lrs", ["unit_var_serath_regt", "loc_serath_complex"], ["paraphrase"], -5),
        ("unit_var_northern_fleet", ["sys_talon_frigate", "sys_sable_submarine", "loc_novak_base"], ["alias", "implicit"], -2),
        ("unit_tg_kestrel", ["sys_vigil_frigate", "loc_corvane_island"], ["alias", "paraphrase"], -4),
        ("loc_kestrel_strait", ["inf_kestrel_lane", "inf_kestrel_cable", "inf_southern_passage"], ["unit_drift", "paraphrase"], -6),
        ("loc_port_auberon", ["inf_aldis_terminal", "inf_blue_logistics_network", "unit_meridian_log_group"], ["alias"], -1),
        ("inf_veyra_station", ["inf_ilmara_grid_control", "loc_lisenne"], ["paraphrase", "implicit"], -7),
        ("ent_varenia", ["unit_var_12_mech_bde", "unit_var_14_mech_bde", "unit_var_21_reserve_bde", "loc_kessary_plain"], ["alias", "distractor"], -2),
        ("ent_corvane", ["loc_halden_airfield", "unit_corvane_coastal_authority", "inf_auberon_halden_airbridge"], ["distractor"], -3),
        ("ent_sondria", ["loc_sondria_camps", "unit_son_border_guard", "loc_ravel_crossing"], ["paraphrase", "alias"], -4),
        ("unit_var_directorate_nine", [], ["paraphrase"], -5),
        ("unit_var_coastal_msl_bde", children.get("unit_var_coastal_msl_bde", []), ["implicit", "alias"], -1),
    ]
    for eid, extras, perts, day in ref:
        fs = ent_facts(eid) + [fid for x in extras for fid in ent_facts(x)]
        add("reference_entry", f"Reference Entry: {ent[eid]['canonical_name']}", day, J2, "B", "2", fs, perts, [eid] + extras)

    # ---- situation reports (Blue and partner units; cover sub-unit facts)
    sit = [
        ("unit_tg_kestrel", "B", "1", ["alias", "hedge_drift"], -1),
        ("unit_halden_brigade", "B", "1", ["typo", "alias"], -2),
        ("unit_auberon_wing", "B", "2", ["paraphrase"], -1),
        ("unit_meridian_log_group", "A", "1", ["unit_drift", "alias"], 0),
        ("unit_cyber_protection_team", "B", "2", ["implicit"], -1),
        ("unit_meridian_isr_det", "B", "2", ["alias", "distractor"], 0),
        ("unit_ilm_coastal_div", "C", "3", ["alias", "typo", "hedge_drift"], -2),
    ]
    isr_observed = sel(present, subjects=["sys_kite_uav", "sys_varen_strike_ac", "unit_var_air_brigade", "inf_dorne_radar"]) + sel(present, subjects=["sys_dorne_asm"], predicates=["count", "status", "located_at"])
    for uid, rel, cred, perts, day in sit:
        subs = children.get(uid, [])
        fs = ent_facts(uid) + [fid for x in subs for fid in ent_facts(x)]
        if uid == "unit_meridian_isr_det":
            fs += isr_observed
        if uid == "unit_ilm_coastal_div":
            fs += ent_facts("unit_ilm_border_guard") + [fid for x in children.get("unit_ilm_border_guard", []) for fid in ent_facts(x)] + ent_facts("loc_ravel_crossing") + ent_facts("inf_ilmara_coastal_road")
        if uid == "unit_tg_kestrel":
            fs += ent_facts("unit_ilm_patrol_sqn") + [fid for x in children.get("unit_ilm_patrol_sqn", []) for fid in ent_facts(x)] + ent_facts("sys_gull_patrol_boat")
        echo = [old_by_key[("unit_tg_kestrel", "located_at")]] if uid == "unit_tg_kestrel" else []
        add("sitrep", f"Situation report {ent[uid]['canonical_name']}", day, ent[uid]["canonical_name"], rel, cred, fs, perts, [uid] + subs, echo=echo)

    # ---- news (narrative, sometimes vague; may carry stale echoes and rumours)
    news = [
        ("Shipping through the Kestrel narrows steady despite Varenian patrols", -2, "Lisenne Courier", "C", "3", ent_facts("inf_kestrel_lane") + ent_facts("loc_kestrel_strait") + ent_facts("inf_southern_passage", ["throughput_per_day"]), ["unit_drift", "alias", "distractor"], [], [], {}),
        ("Varenian brigades exercise on the Kessary Plain", -4, "Meridian Wire Service", "C", "3", ent_facts("ent_varenia", ["mobilized_brigades", "intent"]) + ent_facts("unit_var_12_mech_bde", ["located_at", "status"]) + ent_facts("unit_var_14_mech_bde", ["located_at", "status"]), ["hedge_drift", "alias"], [], [], {}),
        ("Camps beyond Ravel Crossing fill as families leave the coast", -3, "Lisenne Courier", "C", "4", ent_facts("ent_sondria", ["displaced_persons"]) + ent_facts("loc_sondria_camps") + ent_facts("unit_son_border_guard", ["status"]), ["stale_echo", "paraphrase"], [old_by_key[("ent_sondria", "displaced_persons")]], [], {}),
        ("Corvane assembly debates Halden request", -1, "Corvane Observer", "D", "4", ent_facts("loc_halden_airfield") + ent_facts("ent_corvane", ["alignment"]), ["distractor", "alias"], [], [{"subject_id": "ent_corvane", "predicate": "basing_access", "value": False, "text": "officials close to the assembly say Corvane will not grant basing at Halden"}], {}),
        ("Satellite images show construction at the Serath complex", -6, "Meridian Wire Service", "C", "3", ent_facts("loc_serath_complex") + ent_facts("sys_serath_lrs", ["count", "located_at"]) + ent_facts("unit_var_serath_regt", ["located_at"]), ["paraphrase", "hedge_drift"], [], [], {}),
        ("Veyra outages ease after July repairs", -5, "Lisenne Courier", "C", "3", ent_facts("inf_veyra_station", ["outage_hours", "capacity_mw", "status"]) + ent_facts("inf_aldis_terminal"), ["stale_echo", "unit_drift"], [old_by_key[("inf_veyra_station", "outage_hours")]], [], {}),
        ("Northern Fleet sortie from Novak draws Ilmaran protest", -3, "Meridian Wire Service", "C", "3", ent_facts("unit_var_northern_fleet", ["located_at", "readiness", "intent"]) + ent_facts("loc_novak_base") + ent_facts("sys_talon_frigate", ["count"]), ["alias", "hedge_drift", "distractor"], [], [], {}),
        ("Coastal battery count doubled since spring, officials say", -2, "Lisenne Courier", "C", "3", ent_facts("sys_dorne_asm", ["count"]) + ent_facts("unit_var_coastal_msl_bde", ["located_at"]), ["stale_echo", "paraphrase"], [old_by_key[("sys_dorne_asm", "count")]], [], {}),
    ]
    for title, day, author, rel, cred, fs, perts, echo, prop, extra in news:
        add("news", title, day, author, rel, cred, fs, perts, [], echo=echo, proposed=prop, **extra)

    # ---- message traffic (short, unit shorthand)
    msgs = [
        ("Munitions stock report", 0, "Meridian Logistics Group", "A", "1", ent_facts("unit_meridian_log_group", ["munitions_stock_days"]) + ent_facts("ent_blue", ["munitions_stock_days"]) + ent_facts("sys_meridian_standoff_munition", ["count"]), ["typo", "alias"]),
        ("Network posture report", -1, "Meridian Cyber Protection Team", "A", "1", ent_facts("inf_blue_logistics_network") + ent_facts("unit_cyber_protection_team", ["posture_state"]), ["typo"]),
        ("Lantern Battery status", -1, "Lantern Battery", "A", "1", ent_facts("unit_lantern_battery") + ent_facts("sys_halyard_sam") + [fid for x in children.get("unit_lantern_battery", []) for fid in ent_facts(x)], ["alias", "implicit"]),
        ("Surveillance summary Cape Dorne", 0, "Meridian Surveillance Detachment", "B", "2", ent_facts("inf_dorne_radar") + ent_facts("sys_dorne_asm", ["count", "located_at", "operated_by"]) + ent_facts("sys_lark_isr_uav"), ["typo", "unit_drift"]),
        ("Combined patrol readiness", -2, "Task Group Kestrel", "B", "2", ent_facts("unit_ilm_patrol_sqn", ["readiness", "status"]) + ent_facts("sys_gull_patrol_boat") + ent_facts("unit_tg_kestrel", ["posture_state", "located_at"]), ["alias", "typo"]),
        ("Border report Ravel Crossing", -1, "Ilmaran Border Guard", "C", "3", ent_facts("loc_ravel_crossing") + ent_facts("unit_ilm_border_guard") + ent_facts("ent_sondria", ["displaced_persons"]), ["typo", "hedge_drift"]),
        ("Task group position report", 0, "Task Group Kestrel", "A", "1", ent_facts("unit_tg_kestrel", ["located_at", "readiness"]) + ent_facts("sys_vigil_frigate", ["count", "readiness", "status"]) + ent_facts("ent_blue", ["posture_state"]), ["alias", "implicit"]),
        ("Air bridge sortie report", -1, "Auberon Air Expeditionary Wing", "A", "1", ent_facts("inf_auberon_halden_airbridge") + ent_facts("sys_skylark_strike", ["count", "range_km"]) + [fid for x in children.get("unit_auberon_wing", []) for fid in ent_facts(x, ["readiness"])], ["typo", "unit_drift"]),
    ]
    for title, day, author, rel, cred, fs, perts in msgs:
        add("message_traffic", title, day, author, rel, cred, fs, perts, [])

    # ---- tabular (bulk: order of battle, systems, infrastructure, readiness)
    units_all = [e["entity_id"] for e in ctx.tables["entities"] if e["entity_type"] == "unit"]
    systems_all = [e["entity_id"] for e in ctx.tables["entities"] if e["entity_type"] == "system"]
    infra_all = [e["entity_id"] for e in ctx.tables["entities"] if e["entity_type"] == "infrastructure"]
    locs_all = [e["entity_id"] for e in ctx.tables["entities"] if e["entity_type"] == "location"]
    add("tabular", "Order of battle table", -1, J2, "B", "2", sel(present, subjects=units_all, predicates=["located_at", "subordinate_to", "status"]), ["alias", "typo"], [])
    add("tabular", "Unit readiness table", 0, J2, "B", "2", sel(present, subjects=units_all, predicates=["readiness", "posture_state"]), ["typo"], [])
    add("tabular", "Systems table", -2, J2, "B", "2", sel(present, subjects=systems_all), ["unit_drift", "alias"], [])
    add("tabular", "Infrastructure and locations table", -1, J2, "B", "2", sel(present, subjects=infra_all + locs_all) + sel(present, subjects=[p for p, *_ in S.PROBLEM_SET_ENTITIES]), ["typo", "alias"], [])

    # ---- intelligence assessments (J-2; estimative language; projections; one mixed_scale negative example)
    add("assessment", "Assessment: Varenian intent and mobilization", -1, J2, "B", "2",
        ent_facts("ent_varenia", ["intent", "mobilized_brigades", "controls"]) + ent_facts("unit_var_coastal_msl_bde", ["intent"]) + ent_facts("unit_var_northern_fleet", ["intent"]) + ent_facts("unit_var_21_reserve_bde", ["status"]),
        ["stale_echo", "paraphrase"], ["ent_varenia"], echo=[old_by_key[("ent_varenia", "mobilization_days")]])
    add("assessment", "Assessment: Varenian cyber capacity against sustainment", -2, J2, "B", "2",
        ent_facts("ent_varenia", ["cyber_capacity"]) + ent_facts("unit_var_directorate_nine", ["intent", "located_at"]) + ent_facts("inf_ilmara_grid_control") + ent_facts("inf_kestrel_cable"),
        ["paraphrase", "alias"], ["ent_varenia", "unit_var_directorate_nine"])
    add("assessment", "Assessment: Sondrian alignment and displacement", -3, J2, "C", "3",
        ent_facts("ent_sondria", ["alignment", "basing_access"]) + ent_facts("ent_ilmara") + ent_facts("ent_corvane", ["alignment"]) + ent_facts("ent_blue", ["controls", "posture_state"]),
        ["mixed_scale", "alias"], ["ent_sondria"])
    add("assessment", "Assessment: Varenian missile force projections", -1, J2, "B", "2",
        future + ent_facts("sys_dorne_asm", ["range_km", "count"]) + ent_facts("sys_serath_lrs", ["range_km", "count"]),
        ["paraphrase"], ["sys_dorne_asm", "sys_serath_lrs"])

    # ---- length caps (1A.15): message traffic <= 8 facts, reference entries <= 24 facts; overflow to tables
    ob = plans[[i for i, p in enumerate(plans) if p.title == "Order of battle table"][0]]
    rd = plans[[i for i, p in enumerate(plans) if p.title == "Unit readiness table"][0]]
    it = plans[[i for i, p in enumerate(plans) if p.title == "Infrastructure and locations table"][0]]
    fact_by_id = {f["fact_id"]: f for f in cur}
    for p in plans:
        capn = {"message_traffic": 6, "reference_entry": 24, "sitrep": 30}.get(p.doc_type)
        if capn and len(p.facts) > capn:
            overflow, p.facts = p.facts[capn:], p.facts[:capn]
            for fid in overflow:
                f = fact_by_id[fid]
                target = rd if f["predicate"] in ("readiness", "posture_state") else (ob if f["subject_id"].startswith("unit_") else it)
                target.facts.append(fid)
    # ---- coverage: every current fact in >= 1 doc; key facts in >= 2 doc types
    covered = {fid for p in plans for fid in p.facts}
    for f in cur:
        if f["fact_id"] in covered:
            continue
        target = rd if f["predicate"] in ("readiness", "posture_state") else (ob if f["subject_id"].startswith("unit_") else it)
        target.facts.append(f["fact_id"])
    for key in KEY_FACTS:
        for fid in by_key.get(key, []):
            types = {p.doc_type for p in plans if fid in p.facts}
            assert len(types) >= 2 or key == ("ent_corvane", "basing_access"), (key, types)
    ctx.doc_plans = plans
    return plans


def build(ctx: Ctx) -> None:
    plan_intel(ctx)
