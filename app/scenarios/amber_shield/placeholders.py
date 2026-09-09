"""PLACEHOLDER rows for the tables three other agents own.

Everything in this module is a stand-in that exists only so `build.py` runs end to end and the
dataset invariants have something to check. Each block names the agent that replaces it and the
exact contract it must keep. Nothing outside this module needs to change when they land.

    claims / corpus agent -> SOURCES, GROUNDING_EVIDENCE, TOV_CLAIMS, facts()
    risk agent            -> PROBLEM_SETS, HARMFUL_EVENTS, RISK_SOURCES, RISK_DRIVERS, ESCALATION_EDGES
    collection agent      -> PIRS, COLLECTION_REQUIREMENTS

See README.md for the full hand-off contract.
"""
from __future__ import annotations

from datetime import date, timedelta

from ._dataset import gen_module
from .scenario import ASSUMPTIONS, AS_OF, BLUE, RED, RED_ASSUMPTION

PLACEHOLDER = "PLACEHOLDER"

# ---------------------------------------------------------------- claims / corpus agent
# One stand-in document. The claims agent replaces this with the rendered corpus and repoints
# every claim's source_id, span_start and span_end at real text.
SOURCES = [
    dict(source_id="src_ph_amber_baseline", doc_type="assessment",
         title="PLACEHOLDER baseline assessment, Operation AMBER SHIELD",
         published_at=AS_OF.isoformat(), author_org="the United States European Command intelligence directorate",
         reliability="B", credibility="2", real_world=False, public_reference=None,
         path="PLACEHOLDER_baseline_assessment.md", batch=0,
         text_sha256="0" * 64, perturbations=[]),
]

# Evidence behind each planning assumption, keyed by index_k. The value satisfies the assumption's
# tolerance, so `p_holds` = the derived confidence of this claim. The likelihood/confidence pair is
# chosen so p_holds tracks the confidence percentage the UI shows for that assumption:
#   A1 85 -> 0.875   A2 75 -> 0.74375   A3 65 -> 0.675    A4 55 -> 0.61375
#   A5 50 -> 0.5     A6 60 -> 0.64875   A7 55 -> 0.64875  A8 80 -> 0.81875
# (index_k, value, estimative, likelihood_icd203, confidence_icd203)
GROUNDING_EVIDENCE = [
    (0, "blue_aligned", True, "very_likely", "high"),
    (1, True, True, "very_likely", "low"),
    (2, 2500, True, "likely", "high"),
    (3, 21, True, "likely", "low"),
    (4, 30, True, "roughly_even_chance", "high"),
    (5, 0.78, True, "likely", "moderate"),
    (6, 2, True, "likely", "moderate"),
    (7, "operational", True, "very_likely", "moderate"),
]
RED_GROUNDING_EVIDENCE = (45, False, None, "high")

# Waypoint claims on the theory-of-victory chain: action -enables-> claim -supports-> objective.
# Every (subject, predicate) pair here is distinct from every other claim (invariant 4).
# (claim_key, subject_id, predicate, value_or_object, estimative, likelihood, confidence)
TOV_CLAIMS = [
    ("mission", BLUE, "controls", "loc_latgale", True, "likely", "moderate"),
    ("personnel", "unit_1ad", "readiness", 0.85, False, None, "high"),
    ("escalation", RED, "intent", "coercive", True, "very_likely", "moderate"),
    ("time", "inf_powidz_apod", "throughput_per_day", 24, False, None, "high"),
    ("resources", "unit_21_tsc", "munitions_stock_days", 40, False, None, "high"),
    ("rus_territory", RED, "controls", "loc_narva", False, None, "high"),
    ("rus_preserve", "unit_rus_6_caa", "readiness", 0.7, True, "likely", "moderate"),
]
TOV_OBJECTIVE = {
    "mission": "obj_mission", "personnel": "obj_personnel", "escalation": "obj_escalation",
    "time": "obj_time", "resources": "obj_resources",
    "rus_territory": "obj_rus_territory", "rus_preserve": "obj_rus_preserve",
}


def _typing(predicate: str) -> tuple[str, str | None]:
    value_type, unit, _values, _meaning = gen_module("vocab").PREDICATES[predicate]
    return value_type, unit


def _core(subject_id: str, predicate: str, value, estimative: bool, likelihood: str | None,
          confidence: str, valid_from: date) -> dict:
    value_type, unit = _typing(predicate)
    row = dict(subject_id=subject_id, predicate=predicate, object_id=None, value=None, value_type=value_type,
               unit=unit, valid_from=valid_from.isoformat(), valid_to=None, estimative=estimative,
               likelihood_icd203=likelihood, confidence_icd203=confidence, confidence=0.0)
    if value_type == "entity":
        row["object_id"] = value
    else:
        row["value"] = value
    return row


def _evidence_rows() -> list[tuple[str, dict]]:
    """(key, ClaimCore payload) for every grounding and theory-of-victory claim, in a fixed order."""
    out: list[tuple[str, dict]] = []
    start = AS_OF - timedelta(days=30)
    for k, value, estimative, likelihood, confidence in GROUNDING_EVIDENCE:
        _k, _aid, subject, predicate, _op, _val, _role, _origin, _stmt = ASSUMPTIONS[k]
        out.append((f"a{k + 1}", _core(subject, predicate, value, estimative, likelihood, confidence, start)))
    value, estimative, likelihood, confidence = RED_GROUNDING_EVIDENCE
    _k, subject, predicate, *_ = RED_ASSUMPTION
    out.append(("rus_k0", _core(subject, predicate, value, estimative, likelihood, confidence, start)))
    for key, subject, predicate, value, estimative, likelihood, confidence in TOV_CLAIMS:
        out.append((f"tov_{key}", _core(subject, predicate, value, estimative, likelihood, confidence, start)))
    return out


def facts() -> list[dict]:
    """truth/ facts. Every assumption's (subject, predicate) must appear here (invariant 9), and
    every fact must be instantiated by at least one claim (invariant 3)."""
    rows = []
    for key, core in _evidence_rows():
        rows.append(dict(fact_id=f"fct_ph_{key}", supersedes_fact_id=None, first_asserted_batch=0, **core))
    return rows


def claims() -> list[dict]:
    """PLACEHOLDER claim rows over the single stand-in source. Spans are synthetic; the claims
    agent replaces them with offsets into rendered corpus text."""
    rows = []
    for i, (key, core) in enumerate(_evidence_rows()):
        rows.append(dict(claim_id=f"clm_ph_{key}", source_id=SOURCES[0]["source_id"],
                         span_start=i * 200, span_end=i * 200 + 160, asserted_at=AS_OF.isoformat(),
                         likelihood_surface_term=None, status="approved", supersedes_claim_id=None,
                         truth_claim_id=f"fct_ph_{key}", **core))
    return rows


# ---------------------------------------------------------------- risk agent
# Eight problem sets, one per assumption cluster in the UI's PROBLEM_SETS map, each with one
# harmful event so every problem set aggregates to something. Consequence levels are deliberately
# kept below the (extreme, very likely) cell so no placeholder MR event is assessed High: a High MR
# event would make the JP 5-0 acceptable test fail for every COA that does not list it in
# mitigates_he_ids, which is the risk agent's call to make, not this module's.
# (problem_set_id, entity_id, name, thing_of_value_ids, tolerance)
PROBLEM_SETS_SPEC = [
    ("ps_consensus", "ent_ps_consensus", "Alliance consensus", ["obj_mission"],
     "No loss of North Atlantic Council consensus for the restoration of Allied territory."),
    ("ps_force_flow", "ent_ps_force_flow", "Force flow through Poland and Germany", ["obj_time"],
     "No slip in the reception, staging, onward movement and integration timeline beyond C+7."),
    ("ps_iamd", "ent_ps_iamd", "Air and missile defense of the reception corridor", ["obj_personnel"],
     "No successful strike on a reception node that halts onward movement."),
    ("ps_closure", "ent_ps_closure", "Division closure and D-Day conditions", ["obj_time"],
     "Two armored brigade combat teams combat-ready not later than C+21."),
    ("ps_spod", "ent_ps_spod", "Baltic sea ports of debarkation", ["obj_resources"],
     "At least one Baltic sea port of debarkation open throughout."),
    ("ps_escalation", "ent_ps_escalation", "Escalation management", ["obj_escalation"],
     "No nuclear employment against Allied forces."),
    ("ps_suwalki", "ent_ps_suwalki", "Suwalki corridor and the Belarus front", ["obj_mission"],
     "The corridor remains open to Allied ground movement."),
    ("ps_c2", "ent_ps_c2", "Coalition command and control", ["obj_personnel"],
     "United States forces remain interoperable under NATO command from transfer of authority."),
]
# (he_id, problem_set_id, statement, thing_of_value_id, risk_type, base_p, condition, type fields)
HARMFUL_EVENTS_SPEC = [
    ("he_ph_consensus", "ps_consensus", "Alliance political consensus for a counteroffensive fractures", "obj_mission",
     "MSR", 0.22, "posture", dict(strategic_value="ally_global", damage_degree="considerable")),
    ("he_ph_force_flow", "ps_force_flow", "reception and onward movement through Poland slips past C+7", "obj_time",
     "MR", 0.30, "plan", dict(risk_subset="projected_mission", fig28_row="Resources Meet Required Timelines", fig28_cell="major")),
    ("he_ph_iamd", "ps_iamd", "a strike on a reception node halts onward movement", "obj_personnel",
     "MR", 0.20, "action", dict(risk_subset="operational", fig28_row="Achieve Objectives (CCMD Daily Ops)", fig28_cell="modest")),
    ("he_ph_closure", "ps_closure", "the armored division fails to close two brigade combat teams by C+21", "obj_time",
     "MR", 0.28, "plan", dict(risk_subset="projected_mission", fig28_row="Achieve Plan Objectives", fig28_cell="major")),
    ("he_ph_spod", "ps_spod", "every Baltic sea port of debarkation is closed by mining or strike", "obj_resources",
     "MR", 0.18, "action", dict(risk_subset="operational", fig28_row="Capability: DOTMLPF-P vs Threat", fig28_cell="modest")),
    ("he_ph_escalation", "ps_escalation", "Russia conducts a demonstrative nuclear detonation", "obj_escalation",
     "MSR", 0.12, "action", dict(strategic_value="homeland_vital", damage_degree="considerable")),
    ("he_ph_suwalki", "ps_suwalki", "the Suwalki corridor is closed to Allied ground movement", "obj_mission",
     "MR", 0.24, "action", dict(risk_subset="operational", fig28_row="Achieve Objectives (CCMD Daily Ops)", fig28_cell="major")),
    ("he_ph_c2", "ps_c2", "the mission partner network fails to carry Allied command and control", "obj_personnel",
     "MR", 0.15, "posture", dict(risk_subset="force_management", fig28_row="Readiness (DRRS)", fig28_cell="modest")),
]
# (rs_id, he_id, source_kind, entity_id, description)
RISK_SOURCES_SPEC = [
    ("rs_ph_consensus", "he_ph_consensus", "hazard", "ent_nato", "PLACEHOLDER: divergent national caveats inside the Alliance"),
    ("rs_ph_force_flow", "he_ph_force_flow", "threat", "unit_blr_rgf", "PLACEHOLDER: sabotage and unmanned-aircraft pressure on the rail corridor"),
    ("rs_ph_iamd", "he_ph_iamd", "threat", "sys_kalibr", "PLACEHOLDER: cruise-missile strikes on reception nodes"),
    ("rs_ph_closure", "he_ph_closure", "hazard", "inf_aps2_powidz", "PLACEHOLDER: prepositioned stock issue rate"),
    ("rs_ph_spod", "he_ph_spod", "threat", "unit_rus_baltic_fleet", "PLACEHOLDER: mining and coastal-missile threat to the ports"),
    ("rs_ph_escalation", "he_ph_escalation", "threat", "unit_rus_152_msl_bde", "PLACEHOLDER: non-strategic nuclear signalling"),
    ("rs_ph_suwalki", "he_ph_suwalki", "threat", "unit_rus_11_ac", "PLACEHOLDER: converging attack on the corridor"),
    ("rs_ph_c2", "he_ph_c2", "hazard", "inf_mpe_fmn", "PLACEHOLDER: federated network interoperability"),
]
# (driver_id, he_id, subject, predicate, driver_kind, locus, op, value, delta, label)
RISK_DRIVERS_SPEC = [
    ("rd_ph_consensus", "he_ph_consensus", "ent_nato", "alignment", "recognition", "external", "!=", "blue_aligned", 0.18,
     "PLACEHOLDER: Alliance alignment"),
    ("rd_ph_force_flow", "he_ph_force_flow", "ent_poland", "basing_access", "accessibility", "external", "==", False, 0.20,
     "PLACEHOLDER: host-nation transit and basing"),
    ("rd_ph_closure", "he_ph_closure", "unit_1ad", "mobilization_days", "resources", "internal", ">", 21, 0.22,
     "PLACEHOLDER: division closure timeline"),
    ("rd_ph_escalation", "he_ph_escalation", "unit_rus_152_msl_bde", "readiness", "frequency", "external", ">=", 0.75, 0.14,
     "PLACEHOLDER: Iskander brigade readiness"),
    ("rd_ph_suwalki", "he_ph_suwalki", "ent_belarus", "mobilized_brigades", "frequency", "external", ">=", 2, 0.16,
     "PLACEHOLDER: Belarusian mobilization"),
    ("rd_ph_c2", "he_ph_c2", "inf_mpe_fmn", "status", "reliance", "internal", "!=", "operational", 0.20,
     "PLACEHOLDER: mission partner network status"),
]
# (edge_id, from_he_id, to_he_id, lift, mechanism) - a DAG (invariant 8)
ESCALATION_EDGES_SPEC = [
    ("ee_ph_suwalki_flow", "he_ph_suwalki", "he_ph_force_flow", 0.35,
     "PLACEHOLDER: closing the corridor pushes the whole force flow onto sea and air lines"),
    ("ee_ph_spod_flow", "he_ph_spod", "he_ph_force_flow", 0.30,
     "PLACEHOLDER: losing the sea ports throws reception back onto Polish rail"),
    ("ee_ph_flow_closure", "he_ph_force_flow", "he_ph_closure", 0.45,
     "PLACEHOLDER: a reception slip becomes a closure slip"),
    ("ee_ph_iamd_flow", "he_ph_iamd", "he_ph_force_flow", 0.25,
     "PLACEHOLDER: a successful strike on a reception node halts onward movement"),
]


def problem_sets() -> list[dict]:
    return [dict(problem_set_id=pid, entity_id=eid, name=name, tier=0, thing_of_value_ids=tov,
                 risk_owner_role="the Commander, United States European Command", risk_context_source_id=None,
                 tolerance_statement=tol,
                 strategic_context=f"{PLACEHOLDER}: strategic context for {name} pending the risk agent.",
                 scope_and_boundaries=f"{PLACEHOLDER}: scope and boundaries for {name} pending the risk agent.",
                 assumptions_and_constraints=f"{PLACEHOLDER}: assumptions and constraints for {name} pending the risk agent.",
                 expected_outputs=f"{PLACEHOLDER}: expected outputs for {name} pending the risk agent.")
            for pid, eid, name, tov, tol in PROBLEM_SETS_SPEC]


def harmful_events() -> list[dict]:
    rows = []
    for hid, pid, stmt, tov, rt, base_p, cond, extra in HARMFUL_EVENTS_SPEC:
        row = dict(he_id=hid, problem_set_id=pid, statement=stmt, thing_of_value_id=tov, risk_type=rt,
                   risk_subset=None, strategic_value=None, damage_degree=None, fig28_row=None, fig28_cell=None,
                   base_p=base_p, condition=cond, posture_subject_ids=[], beneficial_counterpart_he_id=None,
                   beneficial_statement=None, key_actions=None)
        row.update(extra)
        rows.append(row)
    return rows


def risk_sources() -> list[dict]:
    return [dict(rs_id=r, he_id=h, source_kind=k, entity_id=e, description=d) for r, h, k, e, d in RISK_SOURCES_SPEC]


def risk_drivers() -> list[dict]:
    return [dict(driver_id=d, he_id=h, claim_subject_id=s, claim_predicate=p, driver_kind=k, locus=loc,
                 op=op, value=v, delta=delta, horizons=["near", "mid", "long"], label=label)
            for d, h, s, p, k, loc, op, v, delta, label in RISK_DRIVERS_SPEC]


def escalation_edges() -> list[dict]:
    return [dict(edge_id=e, from_he_id=a, to_he_id=b, lift=lift, mechanism=mech, evidence_claim_ids=[])
            for e, a, b, lift, mech in ESCALATION_EDGES_SPEC]


def all_he_ids() -> list[str]:
    return [h[0] for h in HARMFUL_EVENTS_SPEC]


# ---------------------------------------------------------------- collection agent
# The seven priority intelligence requirements of OPORD 26-004 paragraph 4, kept here because the
# decision points reference them by id. The collection agent owns the collection requirements that
# hang off them, and may rewrite these statements.
PIRS_SPEC = [
    ("pir_01", "Will Russia expand the incursion beyond Ida-Viru and Latgale, and commit 1st Guards Tank Army or "
               "20th Guards Combined Arms Army toward the Pskov axis?", 1),
    ("pir_02", "Will 11th Army Corps or Belarus-based forces attack to close the Suwalki corridor?", 2),
    ("pir_03", "Will Russian forces in Estonia and Latgale shift to maneuver defense, or seize Tartu, Daugavpils or "
               "the Daugava crossings before Alliance closure?", 3),
    ("pir_04", "Is Russia preparing to employ or demonstrate a non-strategic nuclear weapon?", 4),
    ("pir_05", "Where are the S-400 and S-300 batteries, electronic warfare complexes and Iskander launch units, and "
               "has the reconnaissance-strike complex been degraded enough for the D-Day air superiority condition?", 5),
    ("pir_06", "Will the Baltic Fleet sortie, mine the approaches, or strike Allied sea ports of debarkation?", 6),
    ("pir_07", "Are special operations, intelligence service or proxy networks positioning against lines of "
               "communication, ports of debarkation, undersea cables or the Klaipeda liquefied natural gas terminal?", 7),
]
# (req_id, pir_id, assumption index_k or None, eei, sir, gap_type, subject, predicate, ltiov offset days, status)
COLLECTION_REQUIREMENTS_SPEC = [
    ("req_ph_01", "pir_01", 3, "Armored division closure rate against the C+21 condition",
     "Report brigade combat teams issued from Army Prepositioned Stocks 2 and combat-ready by date.",
     "low_confidence", "unit_1ad", "mobilization_days", 10, "validation"),
    ("req_ph_02", "pir_06", 4, "Baltic sea line of communication throughput under mine threat",
     "Report daily escorted transits into Klaipeda and Gdansk.", "low_confidence",
     "inf_baltic_sea_lane", "throughput_per_day", 14, "submission"),
    ("req_ph_03", "pir_02", 6, "Belarusian mobilization in the Grodno area",
     "Report Belarusian and Regional Grouping brigades mobilized.", "missing",
     "ent_belarus", "mobilized_brigades", 4, "research"),
    ("req_ph_04", "pir_04", 5, "Iskander brigade readiness and warhead handling in Kaliningrad Oblast",
     "Report readiness state of the 152nd Guards Missile Brigade.", "low_confidence",
     "unit_rus_152_msl_bde", "readiness", 7, "submission"),
    ("req_ph_05", "pir_03", None, "Russian control of Latgale",
     "Report the forward line of Russian troops in eastern Latvia.", "stale",
     "ent_rus", "controls", 21, "research"),
]


def pirs() -> list[dict]:
    return [dict(pir_id=p, statement=s, commander_role="the Commander, United States European Command",
                 priority_rank=rank, decision_point_ids=[]) for p, s, rank in PIRS_SPEC]


def collection_requirements() -> list[dict]:
    rows = []
    for req, pir, k, eei, sir, gap, subject, predicate, ltiov_days, status in COLLECTION_REQUIREMENTS_SPEC:
        assumption_id = None
        if k is not None:
            assumption_id = f"{ASSUMPTIONS[k][1]}_coa_1"  # rebound by build.py to a real assumption row
        rows.append(dict(req_id=req, pir_id=pir, eei=eei,
                         indicators=[f"{PLACEHOLDER}: indicators pending the collection agent"], sir=sir,
                         gap_type=gap, subject_id=subject, predicate=predicate, assumption_id=assumption_id,
                         rfi_disposition="gap_confirmed", routing="JIOC",
                         ltiov=(AS_OF + timedelta(days=ltiov_days)).isoformat(), created_at=AS_OF.isoformat(),
                         status=status, answered_by_source_id=None, priority=None, jipcl_rank=None))
    return rows
