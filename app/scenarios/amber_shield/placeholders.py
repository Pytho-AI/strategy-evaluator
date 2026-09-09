"""The claim, risk and collection rows of AMBER SHIELD.

UNCLASSIFIED - SYNTHETIC. Fictional content in real doctrinal forms.

This module holds the three families of rows that are derived from evidence rather than authored
as part of the plan:

    claims / corpus   SOURCES, CLAIM_SPECS, facts(), claims()   -> the world model behind A1-A8
    risk (JRAM)       PROBLEM_SETS_SPEC, HARMFUL_EVENTS_SPEC, RISK_SOURCES_SPEC,
                      RISK_DRIVERS_SPEC, ESCALATION_EDGES_SPEC, MITIGATES
    collection        PIRS_SPEC, COLLECTION_REQUIREMENTS_SPEC

Every number the workbench shows now comes from one of these tables. `p_holds` is the derived
confidence of the approved claim that decides an assumption's tolerance; `p_raw` is `base_p` plus
the deltas of the drivers whose claims currently satisfy them, cascaded over the escalation DAG;
`priority` is the EVPI of the assumption a collection requirement resolves. Nothing below is a
constant chosen to make an output look right.

Ids: `clm_a1`..`clm_a8` ground the eight planning assumptions, `clm_rus_k0` grounds the Red
assumption, `clm_tov_*` are the theory-of-victory waypoints `build.py::_dependencies` wires, and
`clm_ev_*` are the remaining evidence claims that drive risk. Each has one `fct_*` counterpart.
"""
from __future__ import annotations

from datetime import date, timedelta

from . import corpus_docs
from ._dataset import gen_module
from .scenario import ASSUMPTIONS, AS_OF, BLUE, RED, RED_ASSUMPTION

# ---------------------------------------------------------------- corpus and claims
SOURCES = corpus_docs.sources()

#: Where a JSPS product is rendered in the corpus, so `guidance.source_id` points at real text.
GUIDANCE_SOURCE = dict(corpus_docs.GUIDANCE_SOURCE)

_C_PLUS_45 = AS_OF + timedelta(days=46)  # C-Day is 10 SEP 2026; the A4 window closes at C+45.

# Evidence, one row per claim. The span is located by searching the rendered document for
# `snippet`, so the offsets cannot drift from the text (invariant 02).
#
# (key, source_id, snippet, subject_id, predicate, value, estimative, likelihood_icd203,
#  confidence_icd203, valid_from, valid_to, likelihood_surface_term)
#
# The eight `a*` rows are the grounding claims of the OPORD's eight planning assumptions. The
# tolerance in `scenario.ASSUMPTIONS` is applied to the value below, and `p_holds` is the derived
# confidence of the row (SCHEMA.md §1): estimative rows take the ICD 203 band midpoint, factual
# rows take 0.97, and the confidence level shrinks the distance from 0.5. So the analyst's
# likelihood and confidence, kept as separate fields, are what set the world probabilities.
CLAIM_SPECS: list[tuple] = [
    # --- A1: Alliance consensus. Unanimous Article 5 endorsement, an A/2 source, and a judgement
    # about a decision already taken: very likely at high confidence.
    ("a1", "src_as_consensus",
     "The North Atlantic Council is very likely to sustain political consensus for the restoration "
     "of Estonian and Latvian territorial integrity by force if necessary, and its alignment is "
     "assessed as blue aligned for the duration of the operation.",
     "ent_nato", "alignment", "blue_aligned", True, "very_likely", "high",
     date(2026, 9, 6), None, "very likely"),
    # --- A2: host-nation transit and basing. The grant exists, but two mobility exceptions are
    # unresolved and the reporting is a single movement-control channel: very likely, low
    # confidence. Low confidence makes the assumption `stale` (SCHEMA.md §1), which is the point.
    ("a2", "src_mt_movement",
     "Poland grants unrestricted transit, overflight, basing and host-nation support for United "
     "States force flow, and the grant is assessed very likely to hold through Phase II.",
     "ent_poland", "basing_access", True, True, "very_likely", "low",
     date(2026, 9, 1), None, "very likely"),
    # --- A3: the reach of Russian sea-launched land-attack fires. A judgement about the range
    # achievable from the launch baskets Russia currently holds, not a catalogue figure.
    ("a3", "src_re_kalibr",
     "the maximum effective range of the Kalibr land-attack cruise missile against Allied "
     "territory is likely 2500 kilometres",
     "sys_kalibr", "range_km", 2500, True, "likely", "high",
     date(2026, 8, 20), None, "likely"),
    # --- A4: division closure. The issue rate has run below plan for three days, so the forecast
    # is held at low confidence; the claim expires at C+45, the gate the OPORD sets.
    ("a4", "src_st_reception",
     "Two armored brigade combat teams are assessed likely to be combat ready 21 days after C-Day.",
     "unit_1ad", "mobilization_days", 21, True, "likely", "low",
     date(2026, 9, 9), _C_PLUS_45, "likely"),
    # --- A5: the Baltic sea line of communication. A genuine coin flip at high confidence: the
    # clearance rate and the threat inventory are both well established, and they balance. This is
    # the roughly-even-chance estimate the JRAM forced-choice rule keys on.
    ("a5", "src_as_baltic",
     "There is a roughly even chance that the Baltic sea line of communication sustains 30 escorted "
     "transits per day through the Danish Straits into Klaipeda and Gdansk.",
     "inf_baltic_sea_lane", "throughput_per_day", 30, True, "roughly_even_chance", "high",
     date(2026, 9, 8), None, "roughly even chance"),
    # --- A6: Iskander brigade readiness. Dispersal seen, warhead handling not seen; two of three
    # sites imaged once, so moderate confidence.
    ("a6", "src_st_iskander",
     "The 152nd Guards Missile Brigade is likely at readiness of 78 percent.",
     "unit_rus_152_msl_bde", "readiness", 0.78, True, "likely", "moderate",
     date(2026, 9, 9), None, "likely"),
    # --- A7: Belarusian commitment. The count sits exactly on the tolerance and rests on vehicle
    # density plus one intercept, with subordination unconfirmed: low confidence.
    ("a7", "src_st_grodno",
     "Belarus is assessed likely to hold 2 brigades mobilized.",
     "ent_belarus", "mobilized_brigades", 2, True, "likely", "low",
     date(2026, 9, 8), None, "likely"),
    # --- A8: the mission partner network. An observed status, not a forecast, so the claim is
    # factual; moderate confidence because one of the three Allied divisions is not yet on.
    ("a8", "src_mt_movement",
     "The mission partner network is operational at the corps headquarters and at two of the three "
     "Allied divisions.",
     "inf_mpe_fmn", "status", "operational", False, None, "moderate",
     date(2026, 9, 8), None, None),

    # --- the single Red assumption: Allied precision munition stocks
    ("rus_k0", "src_st_reception",
     "United States European Command holds 45 days of supply of precision munitions across the theater.",
     "ent_useucom", "munitions_stock_days", 45, False, None, "high",
     date(2026, 9, 9), None, None),

    # --- theory-of-victory waypoints: action -enables-> claim -supports-> objective
    ("tov_mission", "src_opord_26_004",
     "United States European Command and Allied forces are likely to control Latgale and the "
     "international border at the close of Phase III.",
     BLUE, "controls", "loc_latgale", True, "likely", "moderate", date(2026, 9, 9), None, "likely"),
    ("tov_personnel", "src_st_reception",
     "The 1st Armored Division reports readiness at 85 percent across the closing force.",
     "unit_1ad", "readiness", 0.85, False, None, "high", date(2026, 9, 9), None, None),
    ("tov_escalation", "src_st_iskander",
     "Russia is very likely acting to coerce the Alliance rather than to prepare deliberate "
     "employment against Allied forces, and its intent is assessed as coercive.",
     RED, "intent", "coercive", True, "very_likely", "moderate", date(2026, 9, 9), None, "very likely"),
    ("tov_time", "src_st_reception",
     "The Powidz air port of debarkation is clearing 24 airframes per day against a planned rate of thirty.",
     "inf_powidz_apod", "throughput_per_day", 24, False, None, "high", date(2026, 9, 9), None, None),
    ("tov_resources", "src_st_reception",
     "The 21st Theater Sustainment Command holds 40 days of supply forward of the theater distribution centre.",
     "unit_21_tsc", "munitions_stock_days", 40, False, None, "high", date(2026, 9, 9), None, None),
    ("tov_rus_territory", "src_st_rezekne",
     "Russia controls Narva and the crossings over the Narva river.",
     RED, "controls", "loc_narva", False, None, "high", date(2026, 9, 5), None, None),
    ("tov_rus_preserve", "src_st_rezekne",
     "The 6th Combined Arms Army is likely at readiness of 70 percent after four days of consolidation.",
     "unit_rus_6_caa", "readiness", 0.70, True, "likely", "moderate", date(2026, 9, 8), None, "likely"),

    # --- the remaining evidence: risk drivers and the friendly posture factors the forced-choice
    # rule reads (JRAM Encl. C §4.d(2)).
    ("ev_germany_access", "src_mt_movement",
     "Germany has granted the same access across the reception corridor.",
     "ent_germany", "basing_access", True, False, None, "high", date(2026, 9, 1), None, None),
    ("ev_s400_range", "src_re_kalibr",
     "The longest-range interceptor of the S-400 surface-to-air missile system reaches 400 kilometres",
     "sys_s400", "range_km", 400, False, None, "high", date(2026, 8, 20), None, None),
    ("ev_klaipeda_posture", "src_as_baltic",
     "The Klaipeda sea port of debarkation is vulnerable.",
     "inf_klaipeda_spod", "posture_state", "vulnerable", False, None, "high", date(2026, 9, 8), None, None),
    ("ev_gdansk_posture", "src_as_baltic",
     "The Gdansk sea port of debarkation is postured to react, with two sweep teams and a "
     "shore-based escort cell held at short notice.",
     "inf_gdansk_spod", "posture_state", "postured_to_react", False, None, "high", date(2026, 9, 8), None, None),
    ("ev_mcm_hulls", "src_as_baltic",
     "The mine countermeasures group has 6 vessels in the Baltic",
     "unit_snmcmg1", "count", 6, False, None, "high", date(2026, 9, 8), None, None),
    ("ev_rgf_readiness", "src_st_grodno",
     "The Regional Grouping of Forces is likely at readiness of 65 percent.",
     "unit_blr_rgf", "readiness", 0.65, True, "likely", "moderate", date(2026, 9, 8), None, "likely"),
    ("ev_1gta_days", "src_st_rail",
     "The 1st Guards Tank Army is likely to complete movement and be ready to commit in 14 days.",
     "unit_rus_1_gta", "mobilization_days", 14, True, "likely", "moderate", date(2026, 9, 9), None, "likely"),
    ("ev_fleet_readiness", "src_st_baltiysk",
     "The Baltic Fleet is likely at readiness of 82 percent, its highest state since the spring exercise cycle.",
     "unit_rus_baltic_fleet", "readiness", 0.82, True, "likely", "moderate", date(2026, 9, 8), None, "likely"),
    ("ev_11ac_readiness", "src_st_baltiysk",
     "The 11th Army Corps is likely at readiness of 74 percent.",
     "unit_rus_11_ac", "readiness", 0.74, True, "likely", "moderate", date(2026, 9, 8), None, "likely"),
    ("ev_latgale_control", "src_st_rezekne",
     "The 76th Guards Air Assault Division controls Latgale forward of the Rezekne line",
     "unit_rus_76_gaad", "controls", "loc_latgale", False, None, "high", date(2026, 9, 6), None, None),
    ("ev_cable_status", "src_nw_cable",
     "Estlink 2 is degraded.",
     "inf_estlink2_cable", "status", "degraded", False, None, "moderate", date(2026, 9, 8), None, None),
]

#: index_k -> the claim that decides that assumption's tolerance.
GROUNDING_KEY = {k: f"a{k + 1}" for k in range(len(ASSUMPTIONS))}
RED_GROUNDING_KEY = "rus_k0"

TOV_OBJECTIVE = {
    "mission": "obj_mission", "personnel": "obj_personnel", "escalation": "obj_escalation",
    "time": "obj_time", "resources": "obj_resources",
    "rus_territory": "obj_rus_territory", "rus_preserve": "obj_rus_preserve",
}


def claim_id(key: str) -> str:
    return f"clm_{key}"


def fact_id(key: str) -> str:
    return f"fct_{key}"


def grounding_claim_id(index_k: int) -> str:
    return claim_id(GROUNDING_KEY[index_k])


def tov_claim_id(key: str) -> str:
    return claim_id(f"tov_{key}")


def _typing(predicate: str) -> tuple[str, str | None]:
    value_type, unit, _values, _meaning = gen_module("vocab").PREDICATES[predicate]
    return value_type, unit


def _core(spec: tuple) -> dict:
    (_key, _src, _snippet, subject_id, predicate, value, estimative, likelihood, confidence,
     valid_from, valid_to, _surface) = spec
    value_type, unit = _typing(predicate)
    row = dict(subject_id=subject_id, predicate=predicate, object_id=None, value=None,
               value_type=value_type, unit=unit, valid_from=valid_from.isoformat(),
               valid_to=valid_to.isoformat() if valid_to else None, estimative=estimative,
               likelihood_icd203=likelihood, confidence_icd203=confidence, confidence=0.0)
    if value_type == "entity":
        row["object_id"] = value
    else:
        row["value"] = value
    return row


def facts() -> list[dict]:
    """truth/ facts, one per claim. Every assumption's (subject, predicate) appears here
    (invariant 9) and every fact is instantiated by its claim (invariant 3)."""
    return [dict(fact_id=fact_id(spec[0]), supersedes_fact_id=None, first_asserted_batch=0, **_core(spec))
            for spec in CLAIM_SPECS]


def claims() -> list[dict]:
    """Claims with real character spans into the rendered corpus. `asserted_at` is the document's
    publication date (transaction time) and `valid_from`/`valid_to` are the world-time window the
    assertion covers, so the pair is bitemporal."""
    rows = []
    published = {s["source_id"]: s["published_at"] for s in SOURCES}
    for spec in CLAIM_SPECS:
        key, source_id, snippet = spec[0], spec[1], spec[2]
        start, end = corpus_docs.span(source_id, snippet)
        rows.append(dict(claim_id=claim_id(key), source_id=source_id, span_start=start, span_end=end,
                         asserted_at=published[source_id], likelihood_surface_term=spec[11],
                         status="approved", supersedes_claim_id=None, truth_claim_id=fact_id(key),
                         **_core(spec)))
    return rows


# ---------------------------------------------------------------- risk (JRAM, CJCSM 3105.01C)
# Eight tier-0 problem sets, one per assumption cluster in the UI's PROBLEM_SETS map. The six
# JRAM Fig. 3 risk-context paragraphs are the six fields per row: risk owner (para b), strategic
# context (a), scope and boundaries (c), risk tolerance (d), assumptions and constraints (e) and
# expected outputs (f).
#
# (problem_set_id, entity_id, name, thing_of_value_ids, risk_owner_role, tolerance,
#  strategic_context, scope_and_boundaries, assumptions_and_constraints, expected_outputs)
PROBLEM_SETS_SPEC = [
    ("ps_consensus", "ent_ps_consensus", "Alliance consensus", ["obj_mission"],
     "the Commander, United States European Command",
     "No loss of North Atlantic Council consensus for the restoration of Allied territory by force.",
     "Article 5 has been invoked and the political basis of the operation is the consensus that "
     "followed it. Consensus is the authority to execute the counteroffensive, not a supporting "
     "condition for it: without it the campaign has no legal or political route to the end state.",
     "Council decision-making, national caveats on the employment of Allied forces, and the "
     "information contest over the Russian pretext narrative. Excludes national force-generation "
     "shortfalls, which belong to the force flow problem set.",
     "Assumes Article 5 remains invoked (planning assumption one). Constrained by the restraint on "
     "collateral damage in Russophone urban terrain, which exists to deny the pretext narrative.",
     "A consensus indicator set reported to the commander weekly, and a strategic communication "
     "plan that names the two governments that asked for a review point before the counteroffensive.",
     ),
    ("ps_force_flow", "ent_ps_force_flow", "Force flow through Poland and Germany", ["obj_time"],
     "the Commander, United States European Command",
     "No slip in the reception, staging, onward movement and integration timeline beyond seven days.",
     "The whole campaign is a race between Allied closure and Russian consolidation. Every day of "
     "reception delay is a day of consolidation behind a mine, obstacle and electronic warfare belt.",
     "Host-nation transit, overflight and basing; the Polish and German rail and road network; "
     "military mobility procedures; rear-area security of the lines of communication. Excludes the "
     "sea leg, which belongs to the Baltic sea ports problem set.",
     "Assumes unrestricted host-nation transit and expedited military-mobility procedures "
     "(planning assumption two). Constrained by the requirement to retain combat power in Germany, "
     "Italy and the Balkans for other Alliance commitments.",
     "A daily closure trace against the reception timeline, and a named alternate routing for each "
     "of the two crossing points where rail gauge transfer is unresolved.",
     ),
    ("ps_iamd", "ent_ps_iamd", "Air and missile defence of the reception corridor", ["obj_personnel"],
     "the Commander, United States European Command",
     "No successful strike on a reception node that halts onward movement for more than 24 hours.",
     "Russian sea-launched and ground-launched fires range the whole reception corridor. Defending "
     "the corridor protects the force before it is combat-ready, which is when it is most exposed.",
     "Air and missile defence of air and sea ports of debarkation, staging areas and forward "
     "airfields in Poland and Germany, and the horizontal-escalation decision that a strike on "
     "those nodes would represent. Excludes air superiority over the Baltic States.",
     "Assumes strikes on Alliance territory outside the Baltic States remain possible and are "
     "covered by Alliance air and missile defence planning (planning assumption three). "
     "Constrained by counter-unmanned-aircraft coverage at all ports of debarkation by C+3.",
     "An engagement-priority list for the reception corridor and a standing horizontal-escalation "
     "response option held at the Council.",
     ),
    ("ps_closure", "ent_ps_closure", "Division closure and D-Day conditions", ["obj_time"],
     "the Commander, United States European Command",
     "Two armored brigade combat teams combat-ready in Poland not later than C+21.",
     "D-Day is set by the closure of the armored division and by the state of the reconnaissance-"
     "strike complex. The C+21 condition is the single date the rest of the plan is hung on.",
     "Strategic sealift, the prepositioned stock draw at Powidz, brigade issue and validation, and "
     "the D-Day go and no-go conditions. Excludes the counteroffensive itself.",
     "Assumes sealift and prepositioned stocks deliver two brigade combat teams by C+21 and the "
     "full division by C+45 (planning assumption four). Constrained by the advance-party dates in "
     "the operation order.",
     "A brigade-by-brigade closure forecast refreshed daily, and a written D-Day recommendation "
     "against the stated conditions.",
     ),
    ("ps_spod", "ent_ps_spod", "Baltic sea ports of debarkation", ["obj_resources"],
     "the Commander, United States European Command",
     "At least one Baltic sea port of debarkation open to Allied shipping throughout the operation.",
     "The sea leg carries the tonnage the air leg cannot. Losing every Baltic sea port throws the "
     "whole sustainment load onto Polish rail and turns a supply problem into a campaign problem.",
     "The Danish Straits transit, the escorted routes to Klaipeda and Gdansk, mine countermeasures "
     "and the coastal-missile threat to the ports. Excludes onward movement inland.",
     "Assumes the Baltic Sea is contested but not closed and that the two ports remain usable with "
     "mine countermeasures support (planning assumption five). Constrained by the number of mine "
     "countermeasures hulls the Alliance holds in the Baltic.",
     "A daily escorted-transit count against the sustainment floor, and a port-selection "
     "recommendation with the escort allocation each option requires.",
     ),
    ("ps_escalation", "ent_ps_escalation", "Escalation management", ["obj_escalation"],
     "the Commander, United States European Command",
     "No nuclear employment against Allied forces, and no Allied action that forecloses de-escalation.",
     "The operation exists to restore territory without converting a limited incursion into a "
     "general war. Escalation management is therefore an objective in its own right and not a "
     "constraint on the other objectives.",
     "Nuclear signalling and consequence management, the release of strike authorities beyond "
     "engaged forces, and the de-escalation channel. Excludes conventional targeting inside the "
     "Baltic States, which is an operational matter for the components.",
     "Assumes Russia employs non-strategic nuclear signalling and may conduct a demonstrative "
     "detonation, with deliberate employment planned for separately (planning assumption six). "
     "Constrained by the restraint on fires against Russian strategic nuclear forces and warning "
     "infrastructure.",
     "A signalling-response option set held at the Joint Staff, and a written authorities request "
     "that states what the shaping campaign cannot reach without it.",
     ),
    ("ps_suwalki", "ent_ps_suwalki", "Suwalki corridor and the Belarus front", ["obj_mission"],
     "the Commander, United States European Command",
     "The corridor remains open to Allied ground movement for at least one convoy serial per day.",
     "The corridor is the only land route into the Baltic States. Closing it isolates three Allied "
     "countries and forces every subsequent decision to be made under sustainment pressure.",
     "The corridor itself, the cavalry screen, the Belarusian staging areas opposite it and the "
     "forces in Kaliningrad Oblast that would converge on it. Excludes the Estonian front.",
     "Assumes Belarusian forces remain uncommitted absent a Russian decision to expand the war "
     "(planning assumption seven). Constrained by the requirement to move convoys under dedicated "
     "counter-unmanned-aircraft escort.",
     "A corridor status report tied to the decision point on reinforcing the screen, and a named "
     "counterattack force with its release authority.",
     ),
    ("ps_c2", "ent_ps_c2", "Coalition command and control", ["obj_personnel"],
     "the Commander, United States European Command",
     "United States forces remain interoperable under Alliance command from transfer of authority.",
     "Transfer of authority happens while the force is still closing. Command and control that "
     "works on paper but not on the night of the transfer costs tempo exactly when tempo decides "
     "the campaign.",
     "The mission partner network, liaison elements at the Allied headquarters, and the reporting "
     "chain from transfer of authority onward. Excludes national command channels.",
     "Assumes the mission partner network provides adequate interoperability (planning assumption "
     "eight). Constrained by the requirement to establish forward liaison elements by C-Day.",
     "A network availability report per headquarters, and a liaison manning statement for each of "
     "the three Allied divisions.",
     ),
]

# Harmful events (JRAM Pillar 1). MSR rows carry strategic value and degree of damage (Fig. 23);
# MR rows carry the risk subset plus the Fig. 28 row and cell (invariant 18). `base_p` is the
# probability before drivers and before the escalation cascade.
#
# (he_id, problem_set_id, statement, thing_of_value_id, risk_type, base_p, condition,
#  posture_subject_ids, type-specific fields)
HARMFUL_EVENTS_SPEC = [
    # --- Alliance consensus
    ("he_consensus_fracture", "ps_consensus",
     "North Atlantic Council consensus for the counteroffensive fractures", "obj_mission",
     "MSR", 0.18, "posture", [],
     dict(strategic_value="ally_global", damage_degree="considerable")),
    ("he_consensus_narrative", "ps_consensus",
     "the Russian pretext narrative constrains Allied national force contributions", "obj_mission",
     "MR", 0.26, "action", [],
     dict(risk_subset="operational", fig28_row="Messaging", fig28_cell="modest")),
    # --- force flow
    ("he_flow_rail_slip", "ps_force_flow",
     "reception and onward movement through Poland slips more than seven days", "obj_time",
     "MR", 0.24, "plan", [],
     dict(risk_subset="projected_mission", fig28_row="Resources Meet Required Timelines", fig28_cell="major")),
    ("he_flow_host_nation", "ps_force_flow",
     "a host nation restricts transit, overflight or basing and the reception corridor is rerouted", "obj_time",
     "MR", 0.14, "plan", [],
     dict(risk_subset="operational", fig28_row="Authorities", fig28_cell="major")),
    ("he_flow_rail_sabotage", "ps_force_flow",
     "sabotage of the rail and undersea infrastructure interrupts the lines of communication", "obj_time",
     "MR", 0.22, "action", [],
     dict(risk_subset="operational", fig28_row="Achieve Objectives (CCMD Daily Ops)", fig28_cell="modest")),
    # --- air and missile defence of the reception corridor
    ("he_iamd_node_strike", "ps_iamd",
     "a cruise-missile strike on a reception node halts onward movement", "obj_personnel",
     "MR", 0.20, "action", [],
     dict(risk_subset="operational", fig28_row="Achieve Objectives (CCMD Daily Ops)", fig28_cell="major")),
    ("he_iamd_horizontal", "ps_iamd",
     "Russia widens the war to Alliance territory outside the Baltic States", "obj_personnel",
     "MSR", 0.14, "action", [],
     dict(strategic_value="ally_global", damage_degree="catastrophic")),
    # --- division closure
    ("he_closure_c21", "ps_closure",
     "the armored division fails to make two brigade combat teams combat-ready by C+21", "obj_time",
     "MR", 0.22, "plan", [],
     dict(risk_subset="projected_mission", fig28_row="Achieve Plan Objectives", fig28_cell="major")),
    ("he_closure_aps2", "ps_closure",
     "the prepositioned stock issue rate at Powidz falls behind the brigade issue schedule", "obj_time",
     "MR", 0.22, "plan", [],
     dict(risk_subset="force_management", fig28_row="Readiness (DRRS)", fig28_cell="modest")),
    # --- Baltic sea ports of debarkation
    ("he_spod_closed", "ps_spod",
     "mining and coastal-missile fires close every Baltic sea port of debarkation", "obj_resources",
     "MR", 0.36, "plan", [],
     dict(risk_subset="projected_mission", fig28_row="Resources Meet Required Timelines", fig28_cell="extreme")),
    ("he_spod_throughput", "ps_spod",
     "escorted throughput on the Baltic sea line of communication falls below the sustainment floor",
     "obj_resources", "MR", 0.30, "plan", ["inf_klaipeda_spod", "inf_gdansk_spod"],
     dict(risk_subset="operational", fig28_row="Capability: DOTMLPF-P vs Threat", fig28_cell="modest")),
    ("he_spod_straits", "ps_spod",
     "the Danish Straits are closed to Allied military transit", "obj_resources",
     "MSR", 0.12, "action", [],
     dict(strategic_value="partner_regional", damage_degree="considerable")),
    # --- escalation management
    ("he_esc_demonstration", "ps_escalation",
     "Russia conducts a demonstrative nuclear detonation", "obj_escalation",
     "MSR", 0.14, "action", [],
     dict(strategic_value="homeland_vital", damage_degree="considerable")),
    ("he_esc_employment", "ps_escalation",
     "Russia employs a non-strategic nuclear weapon against Allied forces", "obj_escalation",
     "MSR", 0.05, "action", [],
     dict(strategic_value="homeland_vital", damage_degree="catastrophic")),
    ("he_esc_authority", "ps_escalation",
     "strike authorities beyond engaged forces are withheld and the deep fight cannot be shaped",
     "obj_escalation", "MR", 0.30, "plan", [],
     dict(risk_subset="operational", fig28_row="Authorities", fig28_cell="major")),
    # --- Suwalki corridor
    ("he_suwalki_closed", "ps_suwalki",
     "the Suwalki corridor is closed to Allied ground movement", "obj_mission",
     "MR", 0.20, "action", [],
     dict(risk_subset="projected_mission", fig28_row="Achieve Plan Objectives", fig28_cell="major")),
    ("he_suwalki_belarus", "ps_suwalki",
     "Belarusian forces are committed and a second front opens on the Lithuanian border", "obj_mission",
     "MR", 0.18, "action", [],
     dict(risk_subset="operational", fig28_row="Achieve Objectives (CCMD Daily Ops)", fig28_cell="modest")),
    # --- coalition command and control
    ("he_c2_network", "ps_c2",
     "the mission partner network fails to carry Allied command and control at transfer of authority",
     "obj_personnel", "MR", 0.20, "posture", [],
     dict(risk_subset="force_management", fig28_row="Readiness (DRRS)", fig28_cell="modest")),
    ("he_c2_liaison", "ps_c2",
     "liaison and reporting between the corps and the Allied divisions break down", "obj_personnel",
     "MR", 0.18, "posture", [],
     dict(risk_subset="operational", fig28_row="Partnerships", fig28_cell="modest")),
]

# Sources of risk: the threat or hazard behind each harmful event (JRAM Encl. B §3.b(2)).
# (rs_id, he_id, source_kind, entity_id, description)
RISK_SOURCES_SPEC = [
    ("rs_consensus_caveats", "he_consensus_fracture", "hazard", "ent_nato",
     "divergent national caveats on the employment of Allied forces outside their own territory"),
    ("rs_consensus_messaging", "he_consensus_narrative", "threat", "ent_rus",
     "Russian state messaging aimed at the Allied publics furthest from the fighting"),
    ("rs_flow_rail", "he_flow_rail_slip", "hazard", "inf_polish_rail_corridor",
     "unresolved rail gauge transfer and customs clearance on the Polish reception network"),
    ("rs_flow_hn", "he_flow_host_nation", "hazard", "ent_poland",
     "national decisions on transit, overflight and basing that the command does not control"),
    ("rs_flow_sabotage", "he_flow_rail_sabotage", "threat", "unit_socceur",
     "intelligence-service and proxy networks positioned against the rail and undersea infrastructure"),
    ("rs_iamd_kalibr", "he_iamd_node_strike", "threat", "sys_kalibr",
     "sea-launched land-attack cruise missiles ranging the reception corridor"),
    ("rs_iamd_horizontal", "he_iamd_horizontal", "threat", "unit_rus_baltic_fleet",
     "fleet shooters at sea able to strike Alliance territory beyond the Baltic States"),
    ("rs_closure_sealift", "he_closure_c21", "hazard", "inf_aps2_powidz",
     "prepositioned stock issue and validation rate at the Powidz site"),
    ("rs_closure_apod", "he_closure_aps2", "hazard", "inf_powidz_apod",
     "airfield clearance rate at the principal air port of debarkation"),
    ("rs_spod_mines", "he_spod_closed", "threat", "unit_rus_baltic_fleet",
     "minelaying and coastal-missile fires against the Baltic sea ports of debarkation"),
    ("rs_spod_mcm", "he_spod_throughput", "hazard", "unit_snmcmg1",
     "the number of mine countermeasures hulls available for the Q-route clearance task"),
    ("rs_spod_straits", "he_spod_straits", "threat", "unit_rus_baltic_fleet",
     "submarine and corvette activity astride the Danish Straits transit lane"),
    ("rs_esc_iskander", "he_esc_demonstration", "threat", "unit_rus_152_msl_bde",
     "dual-capable Iskander launch units dispersed from the Chernyakhovsk garrison"),
    ("rs_esc_employment", "he_esc_employment", "threat", "sys_oreshnik",
     "non-strategic and intermediate-range systems associated with nuclear signalling"),
    ("rs_esc_authority", "he_esc_authority", "hazard", "role_nac",
     "the political approval the deep fight requires and does not yet have"),
    ("rs_suwalki_11ac", "he_suwalki_closed", "threat", "unit_rus_11_ac",
     "a converging attack on the corridor from Kaliningrad Oblast"),
    ("rs_suwalki_belarus", "he_suwalki_belarus", "threat", "unit_blr_rgf",
     "the Regional Grouping of Forces staging in the Grodno area"),
    ("rs_c2_network", "he_c2_network", "hazard", "inf_mpe_fmn",
     "federated network interoperability between United States and Allied headquarters"),
    ("rs_c2_liaison", "he_c2_liaison", "hazard", "unit_mnc_ne",
     "liaison manning and reporting discipline across the transfer of authority"),
]

# Drivers of risk (JRAM Encl. B §3.b(3)). Each names a (subject, predicate) in the claim table and
# a comparison; the delta is added to P_raw when the approved claim valid in the horizon window
# satisfies it. A driver whose claim does not satisfy it is carried anyway - it is what the
# assessment is watching for, and flipping the claim moves the probability.
#
# (driver_id, he_id, subject, predicate, driver_kind, locus, op, value, delta, horizons, label)
RISK_DRIVERS_SPEC = [
    ("rd_cons_align", "he_consensus_fracture", "ent_nato", "alignment", "response", "external",
     "!=", "blue_aligned", 0.20, None, "loss of Council alignment"),
    ("rd_cons_latgale", "he_consensus_fracture", "unit_rus_76_gaad", "controls", "recognition", "external",
     "==", "loc_latgale", 0.12, None, "Russian consolidation of Latgale"),
    ("rd_cons_intent", "he_consensus_fracture", RED, "intent", "frequency", "external",
     "==", "coercive", 0.08, None, "coercive Russian messaging"),
    ("rd_narr_intent", "he_consensus_narrative", RED, "intent", "recognition", "external",
     "==", "coercive", 0.14, None, "coercive Russian messaging"),

    ("rd_flow_mobility", "he_flow_rail_slip", "ent_poland", "basing_access", "accessibility", "external",
     "==", False, 0.22, None, "host-nation transit exceptions"),
    ("rd_flow_cable", "he_flow_rail_slip", "inf_estlink2_cable", "status", "recognition", "external",
     "==", "degraded", 0.10, None, "rear-area interference with the lines of communication"),
    ("rd_hn_poland", "he_flow_host_nation", "ent_poland", "basing_access", "accessibility", "external",
     "==", False, 0.24, None, "Polish transit and basing decision"),
    ("rd_hn_germany", "he_flow_host_nation", "ent_germany", "basing_access", "accessibility", "external",
     "==", False, 0.16, None, "German transit and basing decision"),
    ("rd_sab_cable", "he_flow_rail_sabotage", "inf_estlink2_cable", "status", "accessibility", "external",
     "==", "degraded", 0.16, None, "undersea and rail interference"),

    ("rd_iamd_kalibr", "he_iamd_node_strike", "sys_kalibr", "range_km", "accessibility", "external",
     ">=", 2000, 0.16, None, "cruise-missile reach over the reception corridor"),
    ("rd_iamd_fleet", "he_iamd_node_strike", "unit_rus_baltic_fleet", "readiness", "frequency", "external",
     ">=", 0.80, 0.10, None, "fleet shooters at sea"),
    ("rd_horiz_kalibr", "he_iamd_horizontal", "sys_kalibr", "range_km", "accessibility", "external",
     ">=", 2000, 0.14, None, "cruise-missile reach beyond the Baltic States"),

    ("rd_closure_days", "he_closure_c21", "unit_1ad", "mobilization_days", "resources", "internal",
     ">=", 21, 0.20, None, "division closure sitting on the C+21 condition"),
    ("rd_closure_1gta", "he_closure_c21", "unit_rus_1_gta", "mobilization_days", "response", "external",
     "<=", 21, 0.08, None, "Russian reserve closing faster than the division"),
    ("rd_aps2_powidz", "he_closure_aps2", "inf_powidz_apod", "throughput_per_day", "resources", "internal",
     "<=", 24, 0.14, None, "air port of debarkation clearance rate"),

    ("rd_spod_fleet", "he_spod_closed", "unit_rus_baltic_fleet", "readiness", "accessibility", "external",
     ">=", 0.80, 0.24, None, "Baltic Fleet sortied and at high readiness"),
    ("rd_spod_lane", "he_spod_closed", "inf_baltic_sea_lane", "throughput_per_day", "criticality", "external",
     "<=", 30, 0.14, None, "escorted throughput at the sustainment floor"),
    ("rd_spod_channel", "he_spod_closed", "inf_klaipeda_spod", "posture_state", "vulnerability", "internal",
     "==", "vulnerable", 0.10, None, "unswept approach channel at Klaipeda"),
    ("rd_thr_lane", "he_spod_throughput", "inf_baltic_sea_lane", "throughput_per_day", "criticality", "external",
     "<=", 30, 0.20, None, "escorted throughput at the sustainment floor"),
    ("rd_thr_mcm", "he_spod_throughput", "unit_snmcmg1", "count", "resources", "internal",
     "<=", 6, 0.06, None, "mine countermeasures hulls available"),
    ("rd_straits_fleet", "he_spod_straits", "unit_rus_baltic_fleet", "readiness", "frequency", "external",
     ">=", 0.80, 0.08, None, "submarine and corvette activity in the transit lane"),

    ("rd_demo_readiness", "he_esc_demonstration", "unit_rus_152_msl_bde", "readiness", "frequency", "external",
     ">=", 0.75, 0.16, None, "Iskander brigade dispersal and readiness"),
    ("rd_demo_alert", "he_esc_demonstration", "unit_rus_152_msl_bde", "readiness", "impact", "external",
     ">=", 0.90, 0.20, None, "Iskander brigade at launch-ready alert"),
    ("rd_empl_alert", "he_esc_employment", "unit_rus_152_msl_bde", "readiness", "impact", "external",
     ">=", 0.90, 0.14, None, "Iskander brigade at launch-ready alert"),
    ("rd_auth_1gta", "he_esc_authority", "unit_rus_1_gta", "mobilization_days", "criticality", "external",
     "<=", 21, 0.18, None, "Russian reserve inside the shaping window"),
    ("rd_auth_s400", "he_esc_authority", "sys_s400", "range_km", "accessibility", "external",
     ">=", 350, 0.10, None, "air defence umbrella over Kaliningrad Oblast"),

    ("rd_suw_11ac", "he_suwalki_closed", "unit_rus_11_ac", "readiness", "frequency", "external",
     ">=", 0.70, 0.16, None, "11th Army Corps readiness"),
    ("rd_blr_brigades", "he_suwalki_belarus", "ent_belarus", "mobilized_brigades", "response", "external",
     ">=", 2, 0.20, None, "Belarusian brigades mobilized"),
    ("rd_blr_commitment", "he_suwalki_belarus", "ent_belarus", "mobilized_brigades", "impact", "external",
     ">=", 3, 0.14, None, "Belarusian mobilization beyond the planning tolerance"),
    ("rd_blr_readiness", "he_suwalki_belarus", "unit_blr_rgf", "readiness", "frequency", "external",
     ">=", 0.60, 0.10, None, "Regional Grouping readiness"),

    ("rd_c2_status", "he_c2_network", "inf_mpe_fmn", "status", "reliance", "internal",
     "!=", "operational", 0.24, None, "mission partner network status"),
    ("rd_liaison_align", "he_c2_liaison", "ent_nato", "alignment", "reliance", "external",
     "!=", "blue_aligned", 0.18, None, "Alliance alignment"),
]

# The escalation cascade (invariant 8: a DAG). Noisy-OR over these edges is what makes one problem
# set's evidence move another problem set's risk level.
# (edge_id, from_he_id, to_he_id, lift, mechanism, evidence claim keys)
ESCALATION_EDGES_SPEC = [
    ("ee_belarus_suwalki", "he_suwalki_belarus", "he_suwalki_closed", 0.40,
     "Belarusian commitment gives the attack on the corridor a second axis from the east, so the "
     "cavalry screen can no longer be reinforced from one direction",
     ["ev_rgf_readiness", "a7"]),
    ("ee_suwalki_flow", "he_suwalki_closed", "he_flow_rail_slip", 0.35,
     "closing the corridor removes the only land route into the Baltic States and pushes the whole "
     "onward movement onto the air and sea legs",
     ["ev_11ac_readiness"]),
    ("ee_spod_flow", "he_spod_closed", "he_flow_rail_slip", 0.30,
     "losing the sea ports throws the tonnage the air leg cannot carry back onto Polish rail",
     ["ev_fleet_readiness", "a5"]),
    ("ee_iamd_flow", "he_iamd_node_strike", "he_flow_rail_slip", 0.28,
     "a successful strike on a reception node stops onward movement while the node is repaired and "
     "the corridor is re-secured",
     ["a3"]),
    ("ee_flow_closure", "he_flow_rail_slip", "he_closure_c21", 0.45,
     "a reception slip is a closure slip: the brigades cannot be validated until they have moved",
     ["a4"]),
    ("ee_demo_consensus", "he_esc_demonstration", "he_consensus_fracture", 0.55,
     "a demonstrative detonation puts every Allied government's own risk calculus above the "
     "collective decision and is the single event most able to break the consensus",
     ["a6"]),
]

# The harmful events each course of action mitigates (JP 5-0 Ch. III §(q)3: the acceptable test).
# Derived from the actions in the COA's policy, not asserted: a COA mitigates an event only where
# one of its own actions bears on that event.
#
#   COA 1 has no mine countermeasures and no maritime pressure, so it does not mitigate the closure
#         of the Baltic sea ports - the one High Military Risk event on the board.
#   COA 3 is the same on the sea line and has no closure action either.
#   COA 4 buys the sea line with maritime pressure and buys strike authorities by asking for them,
#         but it aggravates horizontal escalation and nuclear signalling and mitigates neither, and
#         it has no ground scheme for the corridor.
MITIGATES = {
    "str_coa_1": [
        "he_consensus_fracture", "he_consensus_narrative",
        "he_flow_rail_slip",
        "he_iamd_node_strike", "he_iamd_horizontal",
        "he_closure_c21", "he_closure_aps2",
        "he_suwalki_closed", "he_suwalki_belarus",
    ],
    "str_coa_2": [
        "he_consensus_fracture", "he_consensus_narrative",
        "he_flow_rail_slip", "he_flow_rail_sabotage",
        "he_iamd_horizontal",
        "he_closure_c21",
        "he_spod_closed", "he_spod_throughput", "he_spod_straits",
        "he_suwalki_closed", "he_suwalki_belarus",
        "he_c2_network",
    ],
    "str_coa_3": [
        "he_consensus_fracture", "he_consensus_narrative",
        "he_flow_rail_slip", "he_flow_rail_sabotage",
        "he_suwalki_closed", "he_suwalki_belarus",
    ],
    "str_coa_4": [
        "he_consensus_fracture", "he_consensus_narrative",
        "he_flow_rail_slip",
        "he_iamd_node_strike",
        "he_closure_c21", "he_closure_aps2",
        "he_spod_closed", "he_spod_throughput", "he_spod_straits",
        "he_esc_authority",
    ],
    "str_coa_5": [
        "he_consensus_fracture", "he_consensus_narrative",
        "he_flow_rail_sabotage",
        "he_iamd_node_strike", "he_iamd_horizontal",
        "he_spod_closed", "he_spod_throughput", "he_spod_straits",
        "he_esc_demonstration", "he_esc_employment",
        "he_suwalki_closed", "he_suwalki_belarus",
        "he_c2_network",
    ],
}


def problem_sets() -> list[dict]:
    return [dict(problem_set_id=pid, entity_id=eid, name=name, tier=0, thing_of_value_ids=tov,
                 risk_owner_role=owner, risk_context_source_id=None, tolerance_statement=tol,
                 strategic_context=ctx, scope_and_boundaries=scope,
                 assumptions_and_constraints=asm, expected_outputs=out)
            for pid, eid, name, tov, owner, tol, ctx, scope, asm, out in PROBLEM_SETS_SPEC]


def harmful_events() -> list[dict]:
    rows = []
    for hid, pid, stmt, tov, rt, base_p, cond, posture, extra in HARMFUL_EVENTS_SPEC:
        row = dict(he_id=hid, problem_set_id=pid, statement=stmt, thing_of_value_id=tov, risk_type=rt,
                   risk_subset=None, strategic_value=None, damage_degree=None, fig28_row=None,
                   fig28_cell=None, base_p=base_p, condition=cond, posture_subject_ids=list(posture),
                   beneficial_counterpart_he_id=None, beneficial_statement=None, key_actions=None)
        row.update(extra)
        rows.append(row)
    return rows


def risk_sources() -> list[dict]:
    return [dict(rs_id=r, he_id=h, source_kind=k, entity_id=e, description=d)
            for r, h, k, e, d in RISK_SOURCES_SPEC]


def risk_drivers() -> list[dict]:
    return [dict(driver_id=d, he_id=h, claim_subject_id=s, claim_predicate=p, driver_kind=k, locus=loc,
                 op=op, value=v, delta=delta, horizons=list(horizons or ["near", "mid", "long"]), label=label)
            for d, h, s, p, k, loc, op, v, delta, horizons, label in RISK_DRIVERS_SPEC]


def escalation_edges() -> list[dict]:
    return [dict(edge_id=e, from_he_id=a, to_he_id=b, lift=lift, mechanism=mech,
                 evidence_claim_ids=[claim_id(k) for k in keys])
            for e, a, b, lift, mech, keys in ESCALATION_EDGES_SPEC]


def all_he_ids() -> list[str]:
    return [h[0] for h in HARMFUL_EVENTS_SPEC]


# ---------------------------------------------------------------- collection (JP 2-01)
# The seven priority intelligence requirements of OPORD 26-004 paragraph 4, verbatim. The decision
# points reference these ids; `decision_point_ids` is filled by build.py from the decision-point
# table. `priority_rank` is the commander's stated order, which is not the same thing as the
# analytic value of answering them - that is what the JIPCL rank below computes.
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
PIR_COMMANDER_ROLE = "the Commander, United States European Command"

# Collection requirements. Every requirement resolves the grounding claim of one planning
# assumption, so `priority` is that assumption's EVPI and the JIPCL rank is the order in which
# answering the question changes which course of action is best. Requirements whose assumption
# prices at zero are not worthless - they are questions whose answer does not move the decision,
# which is exactly what the board needs to be told.
#
# (req_id, pir_id, index_k, eei, indicators, sir, gap_type, subject_id, predicate,
#  rfi_disposition, routing, ltiov offset days, status)
COLLECTION_REQUIREMENTS_SPEC = [
    ("req_01", "pir_04", 5,
     "Readiness state and warhead handling of the 152nd Guards Missile Brigade in Kaliningrad Oblast",
     ["Transporter erector launchers dispersed from the Chernyakhovsk garrison",
      "Warhead handling equipment at a dispersal site",
      "Movement from a national-level storage site",
      "Announced exclusion zones over the Baltic"],
     "Report the readiness state of the 152nd Guards Missile Brigade and whether warhead handling has been observed.",
     "low_confidence", "unit_rus_152_msl_bde", "readiness", "gap_confirmed", "JIOC", 5, "submission"),
    ("req_02", "pir_05", 2,
     "Effective reach of Russian sea-launched land-attack fires from current launch baskets",
     ["Corvette and submarine launch baskets held west of the Danish Straits",
      "Instrumented launch telemetry",
      "Basing changes that extend the reach beyond the reception corridor"],
     "Determine the maximum effective range of the Kalibr land-attack cruise missile from the baskets currently held.",
     "low_confidence", "sys_kalibr", "range_km", "gap_confirmed",
     "United States Air Forces in Europe J-2", 9, "validation"),
    ("req_03", "pir_07", 0,
     "Russian influence activity directed at Allied political cohesion",
     ["Intelligence-service and proxy messaging aimed at Allied publics",
      "National caveats added or withdrawn after a Council session",
      "Calls for a review point before the counteroffensive"],
     "Report changes in North Atlantic Council alignment and in the national caveats behind it.",
     "stale", "ent_nato", "alignment", "gap_confirmed", "JCMB", 14, "research"),
    ("req_04", "pir_06", 4,
     "Escorted throughput of the Baltic sea line of communication under the mine threat",
     ["Daily escorted transits into Klaipeda and Gdansk",
      "Minelaying in the Gulf of Finland and the Gulf of Riga",
      "Coastal-missile battery activation",
      "Q-route clearance progress"],
     "Report daily escorted transits through the Danish Straits into Klaipeda and Gdansk.",
     "low_confidence", "inf_baltic_sea_lane", "throughput_per_day", "gap_confirmed",
     "Combined Task Force Baltic J-2", 7, "submission"),
    ("req_05", "pir_01", 3,
     "Prepositioned stock issue rate and armored division closure against the C+21 condition",
     ["Brigade combat teams issued and validated at Powidz",
      "Daily issue rate against the planned rate",
      "Sealift arrivals at Gdansk against the closure trace"],
     "Report brigade combat teams issued from prepositioned stocks and combat-ready by date.",
     "low_confidence", "unit_1ad", "mobilization_days", "gap_confirmed", "V Corps J-2", 10, "validation"),
    ("req_06", "pir_02", 6,
     "Belarusian mobilization and Regional Grouping order of battle in the Grodno area",
     ["Belarusian brigades departing garrison",
      "Bridging and river-crossing assets in the Grodno staging area",
      "Subordination of Belarusian formations to the Regional Grouping of Forces"],
     "Report the number of Belarusian brigades mobilized and their subordination.",
     "missing", "ent_belarus", "mobilized_brigades", "gap_confirmed", "JIOC", 4, "research"),
    ("req_07", "pir_07", 1,
     "Host-nation transit, overflight and basing clearances across the reception corridor",
     ["Signed clearances for each convoy serial",
      "Rail gauge transfer capacity at the two unresolved crossing points",
      "Customs exceptions raised by a host nation"],
     "Confirm that transit, overflight and basing clearances hold for the whole reception corridor through Phase II.",
     "low_confidence", "ent_poland", "basing_access", "gap_confirmed", "JCMB", 6, "validation"),
    ("req_08", "pir_03", 7,
     "Mission partner network availability at each Allied headquarters before transfer of authority",
     ["Terminal availability at the corps and at each Allied division",
      "Federated network spiral testing completed",
      "Liaison manning at each Allied division"],
     "Report mission partner network availability at each headquarters that takes United States forces.",
     "low_confidence", "inf_mpe_fmn", "status", "gap_confirmed", "V Corps J-2", 12, "research"),
]


def pirs() -> list[dict]:
    return [dict(pir_id=p, statement=s, commander_role=PIR_COMMANDER_ROLE,
                 priority_rank=rank, decision_point_ids=[]) for p, s, rank in PIRS_SPEC]


def collection_requirements() -> list[dict]:
    rows = []
    for (req, pir, k, eei, indicators, sir, gap, subject, predicate, disposition, routing,
         ltiov_days, status) in COLLECTION_REQUIREMENTS_SPEC:
        assumption_id = None
        if k is not None:
            assumption_id = f"{ASSUMPTIONS[k][1]}_coa_1"  # rebound by build.py to a real assumption row
        rows.append(dict(req_id=req, pir_id=pir, eei=eei, indicators=list(indicators), sir=sir,
                         gap_type=gap, subject_id=subject, predicate=predicate, assumption_id=assumption_id,
                         rfi_disposition=disposition, routing=routing,
                         ltiov=(AS_OF + timedelta(days=ltiov_days)).isoformat(), created_at=AS_OF.isoformat(),
                         status=status, answered_by_source_id=None, priority=None, jipcl_rank=None))
    return rows
