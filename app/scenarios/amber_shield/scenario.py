"""AMBER SHIELD authored scenario model, in the frozen dataset's vocabulary.

UNCLASSIFIED - SYNTHETIC. Fictional content in real doctrinal forms. Every name below is either
a real doctrinal role/product type (used as a form, never as an assertion about a real plan) or
fictional detail invented for the exercise. Nothing here describes a real operation.

Source of truth for the wording: `docs/demo/USEUCOM_OPORD_26-004_AMBER_SHIELD.txt` (assumptions,
mission, end state, PIRs) and `app/ui/src/app.logic.js` (`COA_LIB`, `state.constraints`,
`state.weights`, `PROBLEM_SETS`). Where the two differ the OPORD wins for assumption text and the
UI wins for COA names, approaches and concepts.

Id scheme
    ent_   actor / polity / problem-set entity      loc_  location
    inf_   infrastructure                           unit_ unit
    sys_   weapon or sensor system                  role_ organization role
    obj_   objective / end state / effect           str_  strategy (COA)
    asm_   assumption        act_  action           res_  resource
    rule_  policy rule       dp_   decision point   om_   opponent model
    gd_    guidance          dep_  dependency edge

This module holds authored rows only. Payoffs are in `payoffs.py`; rows owned by the claims,
risk and collection agents are stubbed in `placeholders.py`; `build.py` assembles and computes.
"""
from __future__ import annotations

from datetime import date

GAME_ID = "amber_shield"
BLUE = "ent_useucom"
RED = "ent_rus"
AS_OF = date(2026, 9, 9)
WORLD_VERSION = 0
HORIZON = 6

# ---------------------------------------------------------------- entities
# (entity_id, entity_type, canonical_name, aliases, parent_id, description)
ACTORS = [
    ("ent_useucom", "actor", "United States European Command", ["USEUCOM", "EUCOM", "the supported command", "Blue"], None,
     "Blue: the supported combatant command for Operation AMBER SHIELD"),
    ("ent_rus", "actor", "Russian Federation Armed Forces", ["Russia", "Russian forces", "Red"], None,
     "Red: the Russian Federation Armed Forces in the Baltic Region"),
]
POLITIES = [
    ("ent_nato", "polity", "North Atlantic Treaty Organization", ["NATO", "the Alliance", "the North Atlantic Council"], None,
     "the Alliance whose Article 5 invocation frames the operation"),
    ("ent_estonia", "polity", "Estonia", ["Republic of Estonia", "the Estonians"], None, "Baltic ally with occupied territory in Ida-Viru County"),
    ("ent_latvia", "polity", "Latvia", ["Republic of Latvia", "the Latvians"], None, "Baltic ally with occupied territory in eastern Latgale"),
    ("ent_lithuania", "polity", "Lithuania", ["Republic of Lithuania", "the Lithuanians"], None, "Baltic ally astride the Suwalki corridor"),
    ("ent_poland", "polity", "Poland", ["Republic of Poland", "the Poles"], None, "reception, staging, onward movement and integration host nation"),
    ("ent_germany", "polity", "Germany", ["Federal Republic of Germany", "the Germans"], None, "principal transit and basing host nation"),
    ("ent_denmark", "polity", "Denmark", ["Kingdom of Denmark", "the Danes"], None, "host nation controlling access to the Danish Straits"),
    ("ent_finland", "polity", "Finland", ["Republic of Finland", "the Finns"], None, "Allied host nation on the northern flank"),
    ("ent_sweden", "polity", "Sweden", ["Kingdom of Sweden", "the Swedes"], None, "Allied host nation controlling Baltic transit routes"),
    ("ent_belarus", "polity", "Belarus", ["Republic of Belarus", "the Belarusians"], None, "co-belligerent territory used by Russia for basing and fires"),
]
# (entity_id, canonical_name, aliases, description)
LOCATIONS = [
    ("loc_narva", "Narva", ["the Narva crossings", "Narva city"], "Estonian border city and river crossing seized on 05 SEP 2026"),
    ("loc_ida_viru", "Ida-Viru County", ["Ida-Viru", "north-eastern Estonia"], "occupied Estonian county east of the Narva river"),
    ("loc_latgale", "Latgale", ["eastern Latgale", "the Latgale salient"], "occupied region of eastern Latvia"),
    ("loc_daugavpils", "Daugavpils", ["the Daugavpils crossings"], "Latvian city on the Daugava and a Russian objective"),
    ("loc_rezekne", "Rezekne", ["Rēzekne", "Rezekne axis"], "Latgale town on the counteroffensive axis"),
    ("loc_daugava", "Daugava river line", ["the Daugava", "the Daugava crossings"], "river line and the principal defensive and attack axis in Latvia"),
    ("loc_tartu", "Tartu", ["southern Estonia"], "Estonian city on the Pskov approach"),
    ("loc_tapa", "Tapa", ["the Tapa line"], "Estonian garrison town and defensive line"),
    ("loc_suwalki", "Suwalki corridor", ["Suwałki corridor", "the Suwalki gap", "the corridor"], "land corridor between Kaliningrad and Belarus linking Poland to Lithuania"),
    ("loc_kaliningrad", "Kaliningrad Oblast", ["Kaliningrad", "the oblast"], "Russian exclave hosting the 11th Army Corps and the Baltic Fleet"),
    ("loc_orzysz", "Orzysz", ["Orzysz-Bemowo Piskie", "the Orzysz area"], "Polish assembly area for the armored division"),
    ("loc_powidz", "Powidz", ["Poznan-Powidz", "the Powidz area"], "Polish reception node and Army Prepositioned Stocks site"),
    ("loc_klaipeda", "Klaipeda", ["Klaipėda", "the Klaipeda port"], "Lithuanian sea port of debarkation"),
    ("loc_gdansk", "Gdansk", ["Gdańsk", "Gdansk-Gdynia", "the Tricity ports"], "Polish sea port of debarkation"),
    ("loc_baltic_sea", "Baltic Sea", ["the Baltic", "the Baltic Region approaches"], "the contested sea area of the operation"),
    ("loc_danish_straits", "Danish Straits", ["the Straits", "the Kattegat and Great Belt"], "maritime access to the Baltic Sea"),
    ("loc_pskov", "Pskov support zone", ["Pskov", "the Pskov axis"], "Russian support zone and reinforcement axis toward Estonia"),
    ("loc_grodno", "Grodno area", ["Grodno", "the Grodno staging area"], "Belarusian staging area opposite the Suwalki corridor"),
]
# (entity_id, canonical_name, aliases, description)
INFRA = [
    ("inf_powidz_apod", "Powidz air port of debarkation", ["Powidz APOD"], "principal air port of debarkation for advance parties and enablers"),
    ("inf_klaipeda_spod", "Klaipeda sea port of debarkation", ["Klaipeda SPOD"], "Lithuanian sea port of debarkation requiring mine countermeasures support"),
    ("inf_gdansk_spod", "Gdansk sea port of debarkation", ["Gdansk SPOD", "Gdynia SPOD"], "Polish sea port of debarkation"),
    ("inf_aps2_powidz", "Army Prepositioned Stocks 2 site at Powidz", ["APS-2 Powidz", "the Powidz stocks"], "armored brigade combat team equipment set held forward"),
    ("inf_rail_baltica", "Rail Baltica corridor", ["Rail Baltica"], "rail line of communication from Poland into the Baltic States"),
    ("inf_polish_rail_corridor", "Polish rail line of communication", ["the Polish rail corridor"], "rail reception and onward movement network through Poland"),
    ("inf_baltic_sea_lane", "Baltic sea line of communication", ["the Baltic sea lane", "the sea line of communication"], "sea line of communication from the Danish Straits to the Baltic ports"),
    ("inf_danish_straits_lane", "Danish Straits transit lane", ["the Straits lane"], "escorted transit lane through the Danish Straits"),
    ("inf_klaipeda_lng", "Klaipeda liquefied natural gas terminal", ["the Klaipeda LNG terminal"], "energy terminal and named rear-area threat objective"),
    ("inf_estlink2_cable", "Estlink 2 undersea cable", ["Estlink 2", "the undersea cable"], "undersea power interconnector in the Gulf of Finland"),
    ("inf_mpe_fmn", "Mission Partner Environment and Federated Mission Networking", ["MPE", "FMN", "the mission partner network"],
     "command and control network providing Alliance interoperability for United States forces"),
]
# (entity_id, canonical_name, aliases, parent actor/polity, description)
UNITS = [
    ("unit_v_corps", "V Corps (Forward)", ["V Corps"], "ent_useucom", "the United States land component headquarters in Poland"),
    ("unit_1ad", "1st Armored Division", ["1AD", "the armored division"], "ent_useucom", "the armored division that closes on Poland from Army Prepositioned Stocks and sealift"),
    ("unit_1ad_1abct", "1st Armored Brigade Combat Team, 1st Armored Division", ["1/1AD", "the first ABCT"], "unit_1ad", "armored brigade combat team drawing Army Prepositioned Stocks at Powidz"),
    ("unit_1ad_2abct", "2nd Armored Brigade Combat Team, 1st Armored Division", ["2/1AD", "the second ABCT"], "unit_1ad", "armored brigade combat team drawing Army Prepositioned Stocks at Powidz"),
    ("unit_1ad_3abct", "3rd Armored Brigade Combat Team, 1st Armored Division", ["3/1AD", "the third ABCT"], "unit_1ad", "armored brigade combat team closing by strategic sealift"),
    ("unit_2cr", "2d Cavalry Regiment", ["2CR", "the cavalry regiment"], "ent_useucom", "Stryker cavalry regiment screening the Suwalki corridor"),
    ("unit_173_abn", "173rd Airborne Brigade", ["173rd ABN", "the airborne brigade"], "ent_useucom", "airborne brigade delivered by airlift as a time-critical enabler"),
    ("unit_56_arty", "56th Artillery Command", ["56th Artillery"], "ent_useucom", "theater long-range fires command"),
    ("unit_21_tsc", "21st Theater Sustainment Command", ["21st TSC"], "ent_useucom", "theater sustainment command running reception, staging, onward movement and integration"),
    ("unit_405_afsb", "405th Army Field Support Brigade", ["405th AFSB"], "ent_useucom", "brigade issuing Army Prepositioned Stocks 2 to arriving units"),
    ("unit_usafe_wing", "United States Air Forces in Europe expeditionary wing", ["the USAFE wing", "the expeditionary wing"], "ent_useucom", "theater air component wing conducting counter-air and suppression missions"),
    ("unit_ctf_baltic", "Combined Task Force Baltic", ["CTF Baltic"], "ent_useucom", "Allied maritime task force for the Baltic sea lines of communication"),
    ("unit_snmcmg1", "Standing NATO Mine Countermeasures Group One", ["SNMCMG1", "the mine countermeasures group"], "ent_nato", "Allied mine countermeasures group clearing the Q-routes"),
    ("unit_socceur", "Special Operations Command Europe", ["SOCEUR"], "ent_useucom", "theater special operations command conducting special reconnaissance and counter-sabotage"),
    ("unit_mnd_n", "Multinational Division North", ["MND-N"], "ent_nato", "Allied division responsible for Estonia and northern Latvia"),
    ("unit_mnd_ne", "Multinational Division North East", ["MND-NE"], "ent_nato", "Allied division responsible for Lithuania and the Suwalki corridor"),
    ("unit_mnc_ne", "Multinational Corps North East", ["MNC-NE"], "ent_nato", "Allied corps headquarters to which forces transfer on closure"),
    ("unit_rus_6_caa", "6th Combined Arms Army", ["6th CAA"], "ent_rus", "Russian army that seized the Narva crossings and Ida-Viru County"),
    ("unit_rus_76_gaad", "76th Guards Air Assault Division", ["76th GAAD"], "ent_rus", "Russian air assault division holding blocking positions in eastern Latgale"),
    ("unit_rus_11_ac", "11th Army Corps", ["11th AC"], "ent_rus", "Russian corps in Kaliningrad Oblast threatening the Suwalki corridor"),
    ("unit_rus_1_gta", "1st Guards Tank Army", ["1st GTA"], "ent_rus", "Russian operational reserve assessed to reinforce through the Pskov axis"),
    ("unit_rus_20_caa", "20th Guards Combined Arms Army", ["20th Guards CAA"], "ent_rus", "Russian army available for reinforcement toward the Pskov axis"),
    ("unit_rus_baltic_fleet", "Baltic Fleet", ["the Baltic Fleet"], "ent_rus", "Russian fleet at Baltiysk able to mine the approaches and strike the sea ports of debarkation"),
    ("unit_rus_152_msl_bde", "152nd Guards Missile Brigade", ["152nd Missile Brigade"], "ent_rus", "Russian Iskander-M brigade in Kaliningrad Oblast"),
    ("unit_blr_rgf", "Regional Grouping of Forces", ["the Regional Grouping", "RGF"], "ent_belarus", "Belarusian and Russian grouping staging in the Grodno area"),
]
# (entity_id, canonical_name, aliases, description)
SYSTEMS = [
    ("sys_s400", "S-400 surface-to-air missile system", ["S-400"], "long-range Russian surface-to-air missile system forming the Snow Dome"),
    ("sys_iskander_m", "Iskander-M missile system", ["Iskander-M", "Iskander"], "Russian dual-capable short-range ballistic missile system"),
    ("sys_kalibr", "Kalibr land-attack cruise missile", ["Kalibr"], "Russian sea-launched land-attack cruise missile"),
    ("sys_oreshnik", "Oreshnik intermediate-range system", ["Oreshnik"], "Russian intermediate-range missile system associated with nuclear signalling"),
    ("sys_patriot", "Patriot air and missile defense system", ["Patriot"], "Allied air and missile defense system protecting reception nodes"),
    ("sys_tomahawk", "Tomahawk land-attack missile", ["Tomahawk"], "United States sea-launched land-attack cruise missile"),
]
# (entity_id, canonical_name, aliases, description)
ROLES = [
    ("role_saceur", "Supreme Allied Commander Europe", ["SACEUR"], "Allied commander approving strikes on sovereign territory"),
    ("role_cdrusucom", "Commander, United States European Command", ["the supported combatant commander", "CDRUSEUCOM"], "risk owner and issuing authority for the operation order"),
    ("role_nac", "the North Atlantic Council", ["the NAC"], "Alliance political authority for Article 5 and escalation decisions"),
    ("role_eucom_j2", "the United States European Command intelligence directorate", ["the EUCOM J-2", "the theater J-2"], "directorate owning the priority intelligence requirements"),
    ("role_jcmb", "the joint collection management board", ["the JCMB"], "board prioritizing requirements into the collection list"),
]
# JRAM problem-set entities, one per assumption cluster in the UI's PROBLEM_SETS map.
# (entity_id, canonical_name, aliases, description)
PROBLEM_SET_ENTITIES = [
    ("ent_ps_consensus", "Alliance consensus problem set", ["the consensus problem set"], "Alliance consensus, Article 5 credibility and strategic communication"),
    ("ent_ps_force_flow", "Force flow problem set", ["the force flow problem set"], "force flow through Poland and Germany, military mobility and reception infrastructure"),
    ("ent_ps_iamd", "Air and missile defense problem set", ["the IAMD problem set"], "integrated air and missile defense over the reception corridor and horizontal escalation"),
    ("ent_ps_closure", "Division closure problem set", ["the closure problem set"], "armored division closure timeline, D-Day conditions and the Army Prepositioned Stocks draw"),
    ("ent_ps_spod", "Baltic sea ports problem set", ["the sea port problem set"], "Baltic sea ports of debarkation, mine countermeasures, escort and the sustainment line"),
    ("ent_ps_escalation", "Escalation management problem set", ["the escalation problem set"], "escalation management, nuclear consequence management and strike authorities"),
    ("ent_ps_suwalki", "Suwalki corridor problem set", ["the corridor problem set"], "the Suwalki corridor, the Belarus front and the cavalry screen"),
    ("ent_ps_c2", "Coalition command and control problem set", ["the coalition C2 problem set"], "coalition command and control, liaison and reporting"),
]


def entities() -> list[dict]:
    rows = [dict(entity_id=e, entity_type=t, canonical_name=n, aliases=a, parent_id=p, description=d)
            for e, t, n, a, p, d in ACTORS + POLITIES]
    for eid, name, aliases, desc in LOCATIONS:
        rows.append(dict(entity_id=eid, entity_type="location", canonical_name=name, aliases=aliases, parent_id=None, description=desc))
    for eid, name, aliases, desc in INFRA:
        rows.append(dict(entity_id=eid, entity_type="infrastructure", canonical_name=name, aliases=aliases, parent_id=None, description=desc))
    for eid, name, aliases, parent, desc in UNITS:
        rows.append(dict(entity_id=eid, entity_type="unit", canonical_name=name, aliases=aliases, parent_id=parent, description=desc))
    for eid, name, aliases, desc in SYSTEMS:
        rows.append(dict(entity_id=eid, entity_type="system", canonical_name=name, aliases=aliases, parent_id=None, description=desc))
    for eid, name, aliases, desc in ROLES:
        rows.append(dict(entity_id=eid, entity_type="organization_role", canonical_name=name, aliases=aliases, parent_id=None, description=desc))
    for eid, name, aliases, desc in PROBLEM_SET_ENTITIES:
        rows.append(dict(entity_id=eid, entity_type="problem_set", canonical_name=name, aliases=aliases, parent_id=None, description=desc))
    return rows


# ---------------------------------------------------------------- guidance chain (JSPS)
# Real product types, fictional content. (guidance_id, product_type, title, issuing_role, parent, objective_ids)
GUIDANCE = [
    ("gd_nss", "NSS", "National Security Strategy (fictional extract): defend Allied territory and the credibility of collective defense",
     "the President", None, []),
    ("gd_nds", "NDS", "National Defense Strategy (fictional extract): integrated deterrence against acute Russian aggression in Europe",
     "the Secretary of War", "gd_nss", []),
    ("gd_nms", "NMS", "National Military Strategy (fictional extract): restore Allied territory while holding escalation below the nuclear threshold",
     "the Chairman of the Joint Chiefs of Staff", "gd_nds", []),
    ("gd_jscp", "JSCP", "Joint Strategic Campaign Plan (fictional extract): European contingency planning tasks and plan levels",
     "the Chairman of the Joint Chiefs of Staff", "gd_nms", []),
    ("gd_oplan_2026_bal", "contingency_plan", "SACEUR OPLAN 2026-BAL (fictional): deterrence and defense of the Baltic Region",
     "the Supreme Allied Commander Europe", "gd_jscp", []),
    ("gd_opord_26_004", "OPORD", "USEUCOM OPORD 26-004, Operation AMBER SHIELD (fictional)",
     "the Commander, United States European Command", "gd_oplan_2026_bal",
     ["obj_mission", "obj_personnel", "obj_escalation", "obj_time", "obj_resources"]),
    ("gd_rus_directive", "contingency_plan", "Russian theater campaign directive (fictional)",
     "the Russian theater commander", None, ["obj_rus_territory", "obj_rus_preserve"]),
]

# ---------------------------------------------------------------- objectives
# The five UI comparison criteria are the five `objective` rows for Blue; the utility vector is
# ordered by objective_id (eval/engine.py::objective_order), which is why payoffs.py builds it
# from a dict keyed by these ids rather than by position.
CRITERIA = ["obj_mission", "obj_personnel", "obj_escalation", "obj_time", "obj_resources"]

# UI weights {mission 4, personnel 3, escalation 4, time 2, resources 1} normalized to sum 1.
UI_WEIGHTS_RAW = {"obj_mission": 4, "obj_personnel": 3, "obj_escalation": 4, "obj_time": 2, "obj_resources": 1}
_W_TOTAL = sum(UI_WEIGHTS_RAW.values())
BLUE_WEIGHTS = {k: v / _W_TOTAL for k, v in UI_WEIGHTS_RAW.items()}

# Aspiration tau per criterion. w.tau = (4*.54 + 3*.39 + 4*.44 + 2*.39 + 1*.29)/14 = 0.44 exactly,
# which sits between the third and fourth strategy value: the acceptable test separates the COAs
# instead of passing or failing all five.
ASPIRATION = {"obj_mission": 0.54, "obj_personnel": 0.39, "obj_escalation": 0.44, "obj_time": 0.39, "obj_resources": 0.29}

# (objective_id, actor, name, kind, guidance_id, parent, metric, aspiration, statement)
OBJECTIVES = [
    ("obj_end_state", BLUE,
     "Russian forces expelled from Estonia and Latvia, the Suwalki corridor and Baltic ports open, escalation contained below the nuclear threshold",
     "end_state", "gd_opord_26_004", None, "end state conditions of OPORD 26-004 paragraph 3 met", None,
     "Restore the international border and contain escalation"),
    ("obj_mission", BLUE, "restoration of Estonian and Latvian territorial integrity", "objective", "gd_opord_26_004", "obj_end_state",
     "probability the military end state is achieved", ASPIRATION["obj_mission"], "Restore Estonian and Latvian territorial integrity"),
    ("obj_personnel", BLUE, "preservation of the force", "objective", "gd_opord_26_004", "obj_end_state",
     "combat power retained; ninetieth-percentile casualties held low", ASPIRATION["obj_personnel"], "Preserve the force"),
    ("obj_escalation", BLUE, "escalation contained below the nuclear threshold", "objective", "gd_opord_26_004", "obj_end_state",
     "probability the operation stays below the nuclear threshold", ASPIRATION["obj_escalation"], "Contain escalation below the nuclear threshold"),
    ("obj_time", BLUE, "force closure and D-Day on time", "objective", "gd_opord_26_004", "obj_end_state",
     "days from C-Day to the achieved end state", ASPIRATION["obj_time"], "Close the force and reach D-Day on time"),
    ("obj_resources", BLUE, "operation conducted inside force and sustainment limits", "objective", "gd_opord_26_004", "obj_end_state",
     "share of theater force and sustainment capacity consumed", ASPIRATION["obj_resources"], "Stay inside force and sustainment limits"),
    # effects (JP 5-0 Fig. IV-9), each nested under the objective it supports
    ("obj_eff_closure", BLUE, "two armored brigade combat teams combat-ready in Poland not later than C+21", "effect",
     "gd_opord_26_004", "obj_time", "brigade combat teams combat-ready by C+21", None, None),
    ("obj_eff_snow_dome", BLUE, "the Russian reconnaissance-strike complex degraded enough for the D-Day air superiority condition", "effect",
     "gd_opord_26_004", "obj_mission", "surface-to-air and fires nodes serviced against the D-Day condition", None, None),
    ("obj_eff_suwalki", BLUE, "the Suwalki corridor held open to Allied ground movement", "effect",
     "gd_opord_26_004", "obj_mission", "corridor open to convoy movement", None, None),
    ("obj_eff_spod", BLUE, "Baltic sea ports of debarkation and the Danish Straits open under Allied escort", "effect",
     "gd_opord_26_004", "obj_resources", "sea line of communication transits per day", None, None),
    ("obj_eff_nuclear", BLUE, "Russian nuclear use held to signalling", "effect",
     "gd_opord_26_004", "obj_escalation", "absence of nuclear employment against Allied forces", None, None),
    ("obj_eff_c2", BLUE, "United States forces interoperable under NATO command from transfer of authority", "effect",
     "gd_opord_26_004", "obj_personnel", "mission partner network availability", None, None),
    # Red
    ("obj_rus_end_state", RED, "a consolidated position on Alliance territory without general war", "end_state", "gd_rus_directive", None,
     "position consolidated and the Alliance divided", None, "Consolidate gains without general war"),
    ("obj_rus_territory", RED, "retention of the seized Estonian and Latvian territory", "objective", "gd_rus_directive", "obj_rus_end_state",
     "territory retained at the end of the operation", 0.35, "Retain the seized territory"),
    ("obj_rus_preserve", RED, "preservation of Russian forces and escalation control", "objective", "gd_rus_directive", "obj_rus_end_state",
     "combat power retained without crossing the nuclear threshold", 0.35, "Preserve the force and keep escalation control"),
]
RED_WEIGHTS = {"obj_rus_territory": 0.6, "obj_rus_preserve": 0.4}


def objectives() -> list[dict]:
    return [dict(objective_id=o, game_id=GAME_ID, actor_id=a, name=n, kind=k, guidance_id=g, parent_objective_id=p,
                 metric=m, direction="max", aspiration=asp, statement=st)
            for o, a, n, k, g, p, m, asp, st in OBJECTIVES]


def guidance() -> list[dict]:
    return [dict(guidance_id=g, product_type=t, title=ti, issuing_role=r, parent_guidance_id=p, objective_ids=o, source_id=None)
            for g, t, ti, r, p, o in GUIDANCE]


# ---------------------------------------------------------------- game form
STATE_VARIABLES = [
    {"name": "force_flow", "domain": ["behind", "on_track", "ahead"]},
    {"name": "suwalki", "domain": ["secure", "threatened", "contested"]},
    {"name": "strike_authority", "domain": ["engaged_forces_only", "kaliningrad_released", "deep_released"]},
    {"name": "nuclear_signal", "domain": ["none", "signalling", "demonstration"]},
    {"name": "spod_status", "domain": ["open", "contested", "closed"]},
    {"name": "alliance_consensus", "domain": ["solid", "strained", "fractured"]},
    {"name": "red_axis", "domain": ["hold", "pskov", "suwalki", "horizontal"]},
    {"name": "d_day", "domain": ["not_set", "c25", "c30", "c60", "none"]},
]
OBSERVABLES = ([{"actor_id": BLUE, "variable": v["name"]} for v in STATE_VARIABLES]
               + [{"actor_id": RED, "variable": v} for v in ("force_flow", "suwalki", "strike_authority", "d_day")])
HORIZON_MAP = [{"period": 1, "jsps_horizon": "near"}, {"period": 2, "jsps_horizon": "near"},
               {"period": 3, "jsps_horizon": "mid"}, {"period": 4, "jsps_horizon": "mid"},
               {"period": 5, "jsps_horizon": "long"}, {"period": 6, "jsps_horizon": "long"}]


def games() -> list[dict]:
    return [dict(game_id=GAME_ID, name="Operation AMBER SHIELD, Baltic Region", actor_ids=[BLUE, RED], horizon=HORIZON,
                 horizon_map=HORIZON_MAP, state_variables=STATE_VARIABLES, observables=OBSERVABLES)]


# ---------------------------------------------------------------- resources and actions
# (resource_id, name, unit)
RESOURCES = [
    ("res_airlift", "strategic airlift", "C-17 equivalent sorties"),
    ("res_sealift", "strategic sealift and Army Prepositioned Stocks draw", "ship equivalents and equipment sets"),
    ("res_sorties", "combat air sorties", "sorties"),
    ("res_munitions", "precision munitions", "rounds"),
    ("res_sustain_days", "sustainment days of supply", "days"),
]
# (action_id, actor, name, tactic_class, line_of_effort, mechanism, cost)
ACTIONS = [
    ("act_close_2cr", BLUE, "move 2d Cavalry Regiment to attack positions in Lithuania", "posture", "force flow", "deter_by_denial",
     {"res_airlift": 6, "res_sustain_days": 3}),
    ("act_draw_aps2", BLUE, "draw Army Prepositioned Stocks 2 at Powidz and issue to arriving brigades", "logistics", "force flow", "sustain",
     {"res_sealift": 14, "res_sustain_days": 4}),
    ("act_sealift_division", BLUE, "close the armored division by strategic sealift through Gdansk", "logistics", "force flow", "sustain",
     {"res_sealift": 22, "res_sustain_days": 6}),
    ("act_airlift_173", BLUE, "deliver the 173rd Airborne Brigade and time-critical enablers by airlift", "logistics", "force flow", "sustain",
     {"res_airlift": 18, "res_sustain_days": 3}),
    ("act_establish_iamd", BLUE, "establish integrated air and missile defense over the reception corridor", "posture", "protection", "deny",
     {"res_munitions": 12, "res_sustain_days": 2}),
    ("act_secure_loc", BLUE, "secure the lines of communication with counter-unmanned-aircraft and rear-area security", "posture", "protection", "deny",
     {"res_sustain_days": 3}),
    ("act_sead_dead", BLUE, "suppress and destroy Russian air defenses in Latgale and Ida-Viru", "strike", "shaping fires", "defeat",
     {"res_sorties": 26, "res_munitions": 34}),
    ("act_deep_fires_pskov", BLUE, "engage the Pskov support zone with theater long-range fires", "strike", "shaping fires", "defeat",
     {"res_sorties": 12, "res_munitions": 28}),
    ("act_strike_kaliningrad", BLUE, "strike Kaliningrad air defenses, cruise-missile shooters and coastal batteries", "strike", "shaping fires", "defeat",
     {"res_sorties": 20, "res_munitions": 40}),
    ("act_mcm_qroute", BLUE, "clear and hold the mine countermeasures Q-routes to Klaipeda and Riga", "logistics", "sea lines", "sustain",
     {"res_sustain_days": 4, "res_sorties": 4}),
    ("act_maritime_pressure", BLUE, "hold the Baltic and Northern Fleets at risk with the carrier strike group and maritime patrol", "posture", "maritime pressure", "deter_by_denial",
     {"res_sorties": 16, "res_sustain_days": 3}),
    ("act_counteroffensive", BLUE, "attack along the Daugava-Rezekne axis to restore the international border", "posture", "counteroffensive", "defeat",
     {"res_sorties": 18, "res_munitions": 30, "res_sustain_days": 8}),
    ("act_defend_line", BLUE, "defend the Daugava, Tapa and Suwalki lines at brigade-plus strength", "posture", "forward defense", "deny",
     {"res_munitions": 14, "res_sustain_days": 6}),
    ("act_persistent_isr", BLUE, "run persistent collection against the priority intelligence requirements", "isr", "intelligence", "inform",
     {"res_sorties": 8}),
    ("act_stratcom", BLUE, "sustain Alliance consensus and deny the Russian pretext narrative", "information", "strategic communication", "influence",
     {}),
    ("act_request_nac_approval", BLUE, "request North Atlantic Council and national approval for strikes beyond engaged forces", "diplomatic", "authorities", "enable",
     {}),
    ("act_deescalation_channel", BLUE, "open a Joint Staff-led de-escalation channel", "diplomatic", "escalation management", "influence",
     {}),
    ("act_nuclear_posture_response", BLUE, "execute the nuclear signalling response: disperse, consult and message", "signal", "escalation management", "deter_by_denial",
     {"res_sustain_days": 2}),
    ("act_cyber_defend_loc", BLUE, "defend the mission partner network and the rail lines of communication in cyberspace", "cyber", "protection", "deny",
     {"res_sustain_days": 1}),
    ("act_hold_reserve", BLUE, "hold the armored division as the theater reserve", "posture", "reserve", "delay",
     {"res_sustain_days": 2}),
    # Red
    ("act_rus_consolidate", RED, "consolidate Narva and Latgale behind a mine, obstacle and electronic warfare belt", "posture", "consolidation", "deny",
     {"res_sustain_days": 5}),
    ("act_rus_expand", RED, "reinforce through Pskov and expand the incursion toward Tartu", "posture", "expansion", "defeat",
     {"res_sustain_days": 9, "res_sorties": 14}),
    ("act_rus_close_suwalki", RED, "attack to close the Suwalki corridor from Kaliningrad and Grodno", "posture", "expansion", "seize",
     {"res_sustain_days": 8, "res_sorties": 12}),
    ("act_rus_mine_baltic", RED, "mine the Baltic approaches and strike the sea ports of debarkation", "strike", "maritime interdiction", "deny",
     {"res_munitions": 24}),
    ("act_rus_horizontal_strike", RED, "strike Polish and German reception nodes and sabotage the undersea cables", "strike", "horizontal escalation", "coerce",
     {"res_munitions": 30}),
    ("act_rus_nuclear_signal", RED, "signal non-strategic nuclear readiness and prepare a demonstrative detonation", "signal", "nuclear signalling", "coerce",
     {}),
    ("act_rus_hold", RED, "hold in place and wait out the Alliance build-up", "posture", "consolidation", "delay",
     {}),
]


def resources() -> list[dict]:
    return [dict(resource_id=r, game_id=GAME_ID, name=n, unit=u) for r, n, u in RESOURCES]


def actions() -> list[dict]:
    return [dict(action_id=a, game_id=GAME_ID, actor_id=actor, name=n, tactic_class=tc, line_of_effort=loe,
                 mechanism=mech, cost=cost, preconditions=True, effects=[])
            for a, actor, n, tc, loe, mech, cost in ACTIONS]


# ---------------------------------------------------------------- assumptions (the UI's A1-A8)
# index_k is the UI's 0-based assumption index; COA_LIB `deps` are 1-based, so deps = index_k + 1.
# Each row is grounded in a (subject_id, predicate) claim plus a tolerance, so `p_holds` is
# computed from evidence rather than typed.
#
# jp50_realistic is False for exactly one assumption: A3 (index_k 2). JP 5-0 Ch. III (6) requires
# an assumption to be realistic - reasonable to hold given what the adversary can do. A3 assumes
# Russia will not conduct conventional strikes against the continental United States. That assumes
# away a capability Russia demonstrably holds (sea-launched land-attack cruise missiles inside
# range of the homeland) rather than a capability it lacks, and nothing USEUCOM does can influence
# the decision. A6 is deliberately NOT the unrealistic one: it acknowledges the nuclear capability
# and plans for it in Annex C Appendix 4, which is what realistic means.
#
# (index_k, assumption_id, subject_id, predicate, op, value, role, origin, statement)
ASSUMPTIONS = [
    (0, "asm_a1", "ent_nato", "alignment", "==", "blue_aligned", "state", "higher_hq",
     "Article 5 remains invoked and the North Atlantic Council sustains political consensus for the "
     "restoration of Estonian and Latvian territorial integrity by force if necessary."),
    (1, "asm_a2", "ent_poland", "basing_access", "==", True, "means", "higher_hq",
     "Germany, Poland, Denmark, the Netherlands, Belgium, Finland and Sweden grant unrestricted transit, "
     "overflight, basing and host-nation support for United States force flow, and European Union "
     "military-mobility procedures are expedited."),
    (2, "asm_a3", "sys_kalibr", "range_km", "<=", 2500, "opponent", "higher_hq",
     "Russia does not conduct conventional strikes against the continental United States; strikes against "
     "NATO territory outside the Baltic States remain possible and are covered under Alliance air and "
     "missile defense planning."),
    (3, "asm_a4", "unit_1ad", "mobilization_days", "<=", 21, "means", "own",
     "Strategic sealift and Army Prepositioned Stocks 2 are sufficient to deliver 1st Armored Division with "
     "two armored brigade combat teams combat-ready in Poland not later than C+21 and the full division not "
     "later than C+45."),
    (4, "asm_a5", "inf_baltic_sea_lane", "throughput_per_day", ">=", 30, "state", "own",
     "The Baltic Sea will be contested but not closed; Danish Straits transit remains possible under Allied "
     "escort, and Klaipeda and Gdansk remain usable as sea ports of debarkation with mine countermeasures support."),
    (5, "asm_a6", "unit_rus_152_msl_bde", "readiness", "<=", 0.80, "opponent", "higher_hq",
     "Russia will employ non-strategic nuclear signaling and may conduct a demonstrative detonation; deliberate "
     "nuclear employment against Allied forces is less likely but is planned for in Annex C Appendix 4."),
    (6, "asm_a7", "ent_belarus", "mobilized_brigades", "<=", 2, "opponent", "own",
     "Belarusian forces remain uncommitted absent a Russian decision to expand the war, while Belarusian "
     "territory will be used by Russia for basing and fires."),
    (7, "asm_a8", "inf_mpe_fmn", "status", "==", "operational", "transition", "own",
     "The Mission Partner Environment and NATO Federated Mission Networking provide adequate command and "
     "control interoperability for United States forces under NATO command."),
]
UNREALISTIC_INDEX_K = 2  # A3; see the note above.

# One Red assumption, index_k 0, shared by all three Russian COAs (invariant 9: a shared index_k
# must carry the same proposition).
RED_ASSUMPTION = (0, "ent_useucom", "munitions_stock_days", ">=", 30, "opponent", "own",
                  "Allied precision munition stocks cover at least thirty days of high-intensity combat.")

# ---------------------------------------------------------------- strategies (COA_LIB, verbatim)
# COA_LIB fields carried over unchanged: title -> name, approach + concept -> summary,
# deps -> assumption index_k + 1, s/cas/esc/days/res -> payoffs.AUTHORED.
CONSTRAINTS = [
    "2d Cavalry Regiment in attack positions in Lithuania not later than C+4; 1st Armored Division advance "
    "parties at Poznan and Powidz not later than C+7; two armored brigade combat teams combat-ready not later than C+21",
    "Establish forward liaison elements at Joint Force Command Brunssum, Multinational Corps North East and "
    "Combined Task Force Baltic not later than C-Day",
    "Counter-unmanned-aircraft coverage at all air and sea ports of debarkation and forward airfields not later "
    "than C+3; force protection condition CHARLIE or higher at staging installations",
    "Retain combat power in Germany, Italy and the Balkans sufficient for other Alliance commitments; the carrier "
    "strike group remains in the North Atlantic and Norwegian Sea",
]
RESTRAINTS = [
    "Strikes on Russian or Belarusian sovereign territory require Supreme Allied Commander Europe approval; "
    "Kaliningrad and targets beyond the Pskov and Leningrad support zone require North Atlantic Council and national approval",
    "No fires against Russian strategic nuclear forces, nuclear command and control, or early-warning "
    "infrastructure without Presidential authorization",
    "No independent de-escalation channels with the Russian General Staff below the Joint Staff or the "
    "United States European Command operations directorate",
    "Minimize collateral damage in Russophone urban terrain at Narva and Daugavpils to deny the Russian pretext narrative",
]

# (strategy_id, ui_index, name, approach, concept, deps (1-based), main_effort, sequencing,
#  task_org, reserve_policy, own_constraint, actions in policy order)
COAS = [
    ("str_coa_1", 0, "Rapid Reinforcement, Hold and Restore", "Base plan · LOE 1-3", [1, 2, 4, 5],
     "armored counteroffensive along the Daugava-Rezekne axis", "sequential",
     ["unit_1ad", "unit_1ad_1abct", "unit_1ad_2abct", "unit_2cr", "unit_v_corps", "unit_usafe_wing", "unit_mnd_n"],
     "the third armored brigade combat team is the theater reserve, released on D-Day",
     "Two armored brigade combat teams combat-ready at Orzysz not later than C+21",
     ["act_close_2cr", "act_draw_aps2", "act_establish_iamd", "act_persistent_isr",
      "act_sead_dead", "act_deep_fires_pskov", "act_counteroffensive", "act_stratcom"]),
    ("str_coa_2", 1, "Defend Forward, Delay D-Day", "Conditions-first", [1, 4, 6, 8],
     "conditions-setting shaping fires and full division closure", "sequential",
     ["unit_1ad", "unit_1ad_1abct", "unit_1ad_2abct", "unit_1ad_3abct", "unit_v_corps", "unit_snmcmg1", "unit_mnd_n"],
     "no reserve released before the full division closes; D-Day is held until conditions are met",
     "Hold D-Day until three armored brigade combat teams have closed and the Q-routes are cleared",
     ["act_defend_line", "act_sealift_division", "act_mcm_qroute", "act_persistent_isr",
      "act_sead_dead", "act_cyber_defend_loc", "act_counteroffensive", "act_stratcom"]),
    ("str_coa_3", 2, "Suwałki-First Economy of Force", "Secure the LOC", [2, 4, 7],
     "defense of the Suwalki corridor", "simultaneous",
     ["unit_1ad", "unit_1ad_1abct", "unit_2cr", "unit_173_abn", "unit_mnd_ne", "unit_56_arty"],
     "the armored division is committed as the counterattack force against the corridor, not held as reserve",
     "Convoys through the Suwalki corridor move under dedicated counter-unmanned-aircraft escort",
     ["act_close_2cr", "act_airlift_173", "act_secure_loc", "act_persistent_isr",
      "act_deep_fires_pskov", "act_defend_line", "act_stratcom"]),
    ("str_coa_4", 3, "Deep Strike and Maritime Pressure", "Fires-led shaping", [1, 3, 6],
     "deep fires and maritime pressure", "simultaneous",
     ["unit_56_arty", "unit_usafe_wing", "unit_ctf_baltic", "unit_1ad", "unit_1ad_1abct", "unit_1ad_2abct"],
     "no ground reserve; the reserve is fires capacity retained for the compressed D-Day",
     "Request North Atlantic Council approval for strikes into Kaliningrad Oblast in Phase II",
     ["act_request_nac_approval", "act_strike_kaliningrad", "act_maritime_pressure", "act_persistent_isr",
      "act_sead_dead", "act_draw_aps2", "act_counteroffensive", "act_stratcom"]),
    ("str_coa_5", 4, "Restrained Defense and Negotiated Withdrawal", "Deter, defend, negotiate", [1, 3, 7, 8],
     "forward defense and negotiated withdrawal", "sequential",
     ["unit_2cr", "unit_173_abn", "unit_mnd_n", "unit_mnd_ne", "unit_ctf_baltic", "unit_socceur"],
     "the armored division is held intact as leverage and is never committed to an attack",
     "Maintain a brigade-plus defensive posture in each Baltic State throughout",
     ["act_defend_line", "act_establish_iamd", "act_mcm_qroute", "act_persistent_isr",
      "act_deescalation_channel", "act_nuclear_posture_response", "act_cyber_defend_loc", "act_stratcom"]),
]

# COA concepts, verbatim from COA_LIB (kept apart so the long strings stay readable).
CONCEPTS = {
    "str_coa_1": "2CR forward to Lithuania and the Daugava by C+4; 1AD draws APS-2 and closes two ABCTs at Orzysz by C+21; joint SEAD/DEAD campaign degrades the Snow Dome in Estonia, Latgale and the Pskov support zone; D-Day counteroffensive along the Daugava–Rēzekne axis at C+30 with 1AD as the armored main effort.",
    "str_coa_2": "Complete full 1AD closure (three ABCTs, C+45) and finish MCM clearance to Riga before attacking; Phase II extended to D-Day at roughly C+60. Accepts a longer Russian consolidation window and a frozen-conflict narrative risk in exchange for overmatch and lower casualties.",
    "str_coa_3": "1AD is committed as the counterattack force against 11th Army Corps and Belarus-based threats to the Suwałki corridor rather than held as reserve; the Estonian and Latvian restoration is led by MND-N Allied forces with US fires, air and 2CR in support, and US armor joins Phase III late.",
    "str_coa_4": "Seek early NAC and national approval to strike Kaliningrad IADS, Kalibr shooters and coastal batteries with Tomahawk and long-range fires; carrier strike group holds the Northern Fleet at risk; ground counteroffensive follows a compressed Phase II. Fastest route to air and sea superiority; highest escalation exposure.",
    "str_coa_5": "Establish an unbreakable defense on the Daugava, Tapa and Suwałki lines with US forces, deny further gains, and use the Alliance build-up as leverage for a Russian withdrawal without a counteroffensive. Lowest casualties and escalation risk; does not restore territory by force and risks the frozen conflict the intent forbids.",
}

# Mission statement (JP 5-0 who/what/when/where/why). `what` differs per COA; the rest is the OPORD's.
MISSION_WHEN = "on order and not later than C-Day, 10 September 2026, through six planning periods"
MISSION_WHERE = "in the Baltic Region and the reception corridor through Poland and Germany"
MISSION_WHY = ("to restore the territorial integrity of Estonia and Latvia, preserve the credibility of NATO Article 5 "
               "and deter further Russian aggression against the Alliance")
MISSION_WHAT = {
    "str_coa_1": "deploys, receives and employs designated forces and attacks along the Daugava-Rezekne axis at C+30",
    "str_coa_2": "defends forward, completes full division closure and mine countermeasures clearance, and attacks at C+60",
    "str_coa_3": "defends the Suwalki corridor with the armored division while Allied divisions lead the restoration",
    "str_coa_4": "conducts a fires-led shaping campaign against Kaliningrad and the reconnaissance-strike complex and attacks at C+25",
    "str_coa_5": "establishes a forward defense on the Daugava, Tapa and Suwalki lines and negotiates a Russian withdrawal",
}

# Russian courses of action (JP 5-0 Fig. III-13 labels), from the UI's SCENARIOS list.
# (strategy_id, name, label, probability, summary, main_effort, sequencing, reserve_policy, actions)
RED_COAS = [
    ("str_rus_ml", "Consolidation and freeze", "most_likely", 0.50,
     "Maneuver defense behind a mine, obstacle and electronic warfare belt in Narva and Latgale; hybrid pressure; "
     "nuclear signalling as NATO builds.",
     "consolidation of the seized ground", "sequential", "operational reserve held east of the border",
     ["act_rus_consolidate", "act_rus_nuclear_signal", "act_rus_hold"]),
    ("str_rus_md", "Expanded incursion", "most_dangerous", 0.25,
     "1st Guards Tank Army reinforces via Pskov; a converging attack closes the Suwalki corridor; the Baltic Fleet "
     "mines and strikes the sea ports of debarkation; a demonstrative nuclear detonation follows.",
     "converging attack on the Suwalki corridor", "simultaneous", "operational reserve committed on the Pskov axis",
     ["act_rus_expand", "act_rus_close_suwalki", "act_rus_mine_baltic", "act_rus_nuclear_signal"]),
    ("str_rus_alt", "Horizontal escalation", "alternative", 0.25,
     "Kalibr and long-range strikes on Polish and German air and sea ports of debarkation; sabotage of the undersea "
     "cables and the rail lines of communication.",
     "strikes on the reception corridor", "simultaneous", "no ground reserve committed",
     ["act_rus_horizontal_strike", "act_rus_mine_baltic", "act_rus_hold"]),
]

# ---------------------------------------------------------------- policy rules and decision points
# Each COA gets one rule per action in its list, on a period schedule, plus one mixed pair at the
# decision point where the branch is genuinely probabilistic (invariant 5: rules sharing a
# (strategy, condition, priority) group have probabilities that sum to 1).
#
# Rule conditions use only variables the actor observes (invariant 1).
RULE_CONDITIONS = {
    "act_close_2cr": {"var": "suwalki", "op": "!=", "value": "secure"},
    "act_draw_aps2": {"var": "force_flow", "op": "!=", "value": "ahead"},
    "act_sealift_division": {"var": "force_flow", "op": "!=", "value": "ahead"},
    "act_airlift_173": {"var": "force_flow", "op": "==", "value": "behind"},
    "act_establish_iamd": True,
    "act_secure_loc": {"var": "suwalki", "op": "!=", "value": "secure"},
    "act_sead_dead": {"var": "strike_authority", "op": "!=", "value": "engaged_forces_only"},
    "act_deep_fires_pskov": {"var": "strike_authority", "op": "==", "value": "deep_released"},
    "act_strike_kaliningrad": {"var": "strike_authority", "op": "in", "value": ["kaliningrad_released", "deep_released"]},
    "act_mcm_qroute": {"var": "spod_status", "op": "!=", "value": "open"},
    "act_maritime_pressure": {"var": "spod_status", "op": "!=", "value": "open"},
    "act_counteroffensive": {"var": "d_day", "op": "!=", "value": "not_set"},
    "act_defend_line": True,
    "act_persistent_isr": True,
    "act_stratcom": {"var": "alliance_consensus", "op": "!=", "value": "solid"},
    "act_request_nac_approval": {"var": "strike_authority", "op": "==", "value": "engaged_forces_only"},
    "act_deescalation_channel": {"var": "nuclear_signal", "op": "!=", "value": "none"},
    "act_nuclear_posture_response": {"var": "nuclear_signal", "op": "==", "value": "demonstration"},
    "act_cyber_defend_loc": True,
    "act_hold_reserve": {"var": "d_day", "op": "==", "value": "not_set"},
}
RED_RULE_CONDITIONS = {
    "act_rus_consolidate": {"var": "d_day", "op": "==", "value": "not_set"},
    "act_rus_expand": {"var": "force_flow", "op": "==", "value": "behind"},
    "act_rus_close_suwalki": {"var": "suwalki", "op": "!=", "value": "secure"},
    "act_rus_mine_baltic": True,
    "act_rus_horizontal_strike": {"var": "force_flow", "op": "!=", "value": "behind"},
    "act_rus_nuclear_signal": {"var": "strike_authority", "op": "!=", "value": "engaged_forces_only"},
    "act_rus_hold": True,
}

# The three decision points the UI names, present on every COA, plus one COA-specific decision
# point each. (suffix, name, pir_id, latest_period, the action index whose rule is the branch)
COMMON_DPS = [
    ("dp1_force_flow", "DP1 - Force flow", "pir_01", 2),
    ("dp2_strike_authorities", "DP2 - Strike authorities", "pir_05", 4),
    ("dp3_nuclear_signalling", "DP3 - Nuclear signalling", "pir_04", 5),
]
# (strategy_id, suffix, name, pir_id, latest_period)
COA_DPS = {
    "str_coa_1": ("dp4_commit_reserve", "DP4 - Commit the third brigade combat team", "pir_03", 5),
    "str_coa_2": ("dp4_d_day_release", "DP4 - Release the delayed D-Day", "pir_03", 6),
    "str_coa_3": ("dp4_release_abct", "DP4 - Release an armored brigade combat team to the north", "pir_02", 4),
    "str_coa_4": ("dp4_pskov_axis", "DP4 - Counter the Pskov axis", "pir_01", 4),
    "str_coa_5": ("dp4_reject_freeze", "DP4 - Reject or accept the offered freeze", "pir_07", 6),
}

# Resource budgets per COA: the theater allocation the COA is given, set 12-20 per cent above the
# worst-case trajectory cost of its own policy so the JP 5-0 feasible test compares against a real
# ceiling. Adding one more costly rule, or halving an allocation, makes a COA infeasible - see
# app/tests/scenarios/test_validity.py::test_feasible_is_not_vacuous.
BUDGETS = {
    "str_coa_1": {"res_airlift": 10, "res_sealift": 20, "res_sorties": 72, "res_munitions": 90, "res_sustain_days": 20},
    "str_coa_2": {"res_airlift": 8, "res_sealift": 26, "res_sorties": 76, "res_munitions": 92, "res_sustain_days": 26},
    "str_coa_3": {"res_airlift": 22, "res_sealift": 12, "res_sorties": 34, "res_munitions": 50, "res_sustain_days": 18},
    "str_coa_4": {"res_airlift": 8, "res_sealift": 18, "res_sorties": 108, "res_munitions": 118, "res_sustain_days": 22},
    "str_coa_5": {"res_airlift": 8, "res_sealift": 10, "res_sorties": 26, "res_munitions": 20, "res_sustain_days": 20},
}
RED_BUDGET = {"res_airlift": 4, "res_sealift": 4, "res_sorties": 32, "res_munitions": 60, "res_sustain_days": 20}


def _rule_periods(i: int, n: int) -> list[int]:
    """Spread a COA's actions over the six periods, one rule per period, wrapping for long lists."""
    return [1 + (i * HORIZON) // n]


def strategy_rows() -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """Returns (strategies, strategy_objectives, strategy_resources, policy_rules, decision_points,
    assumptions) for both actors. `mitigates_he_ids` and `theory_of_victory` are filled by build.py."""
    strategies, sobj, sres, rules, dps, asms = [], [], [], [], [], []

    for sid, _ui, name, approach, deps, main_effort, sequencing, task_org, reserve, own_c, acts in COAS:
        strategies.append(dict(
            strategy_id=sid, game_id=GAME_ID, actor_id=BLUE, name=name,
            summary=f"{approach}. {CONCEPTS[sid]}", echelon="theater_strategic",
            guidance_source="gd_opord_26_004", adversary_coa_label=None,
            mission_who="United States European Command, as the supported combatant command",
            mission_what=MISSION_WHAT[sid], mission_when=MISSION_WHEN, mission_where=MISSION_WHERE, mission_why=MISSION_WHY,
            end_state_objective_id="obj_end_state", constraints=CONSTRAINTS + [own_c], restraints=list(RESTRAINTS),
            main_effort=main_effort, sequencing=sequencing, task_org=task_org, reserve_policy=reserve,
            mitigates_he_ids=[], risk_functional="expected", risk_alpha=None, opponent_model_id="om_blue",
            theory_of_victory=[]))
        for oid, w in BLUE_WEIGHTS.items():
            sobj.append(dict(strategy_id=sid, objective_id=oid, weight=w, rating_1_to_3=None))
        for rid, budget in BUDGETS[sid].items():
            sres.append(dict(strategy_id=sid, resource_id=rid, budget=float(budget)))
        for dep in deps:
            k, aid, subj, pred, op, val, role, origin, stmt = ASSUMPTIONS[dep - 1]
            asms.append(dict(assumption_id=f"{aid}_{sid[4:]}", strategy_id=sid, index_k=k, statement=stmt,
                             subject_id=subj, predicate=pred, tolerance=dict(op=op, value=val), role=role,
                             jp50_logical=True, jp50_realistic=(k != UNREALISTIC_INDEX_K), jp50_essential=True,
                             origin=origin, in_decision_matrix=True))
        n = len(acts)
        rule_by_action = {}
        for i, act in enumerate(acts):
            rule_id = f"rule_{sid[4:]}_{i}"
            rule_by_action[act] = rule_id
            rules.append(dict(rule_id=rule_id, strategy_id=sid, priority=i, condition=RULE_CONDITIONS[act],
                              action_id=act, probability=1.0, periods=_rule_periods(i, n),
                              rationale_claim_ids=[], decision_point_id=None))
        # One genuinely probabilistic branch per COA: hold the reserve or commit it, 40/60, at the
        # COA-specific decision point. Same (strategy, condition, priority) group, sums to 1.
        branch_cond = {"var": "d_day", "op": "==", "value": "not_set"}
        hold_id, commit_id = f"rule_{sid[4:]}_hold", f"rule_{sid[4:]}_commit"
        for rule_id, act, prob in ((hold_id, "act_hold_reserve", 0.4), (commit_id, "act_persistent_isr", 0.6)):
            rules.append(dict(rule_id=rule_id, strategy_id=sid, priority=n, condition=branch_cond,
                              action_id=act, probability=prob, periods=[HORIZON],
                              rationale_claim_ids=[], decision_point_id=None))
        dp_specs = [(suffix, dp_name, pir, per, acts[min(j * 2 + 1, n - 1)])
                    for j, (suffix, dp_name, pir, per) in enumerate(COMMON_DPS)]
        suffix, dp_name, pir, per = COA_DPS[sid]
        for suffix_, dp_name_, pir_, per_, act_ in dp_specs:
            dp_id = f"dp_{sid[4:]}_{suffix_}"
            dps.append(dict(dp_id=dp_id, strategy_id=sid, name=dp_name_, condition=RULE_CONDITIONS[act_],
                            branch_rule_ids=[rule_by_action[act_]], pir_id=pir_, latest_period=per_))
            for r in rules:
                if r["rule_id"] == rule_by_action[act_]:
                    r["decision_point_id"] = dp_id
        dp_id = f"dp_{sid[4:]}_{suffix}"
        dps.append(dict(dp_id=dp_id, strategy_id=sid, name=dp_name, condition=branch_cond,
                        branch_rule_ids=[hold_id, commit_id], pir_id=pir, latest_period=per))
        for r in rules:
            if r["rule_id"] in (hold_id, commit_id):
                r["decision_point_id"] = dp_id

    for sid, name, label, _p, summary, main_effort, sequencing, reserve, acts in RED_COAS:
        strategies.append(dict(
            strategy_id=sid, game_id=GAME_ID, actor_id=RED, name=name, summary=summary, echelon="operational",
            guidance_source="gd_rus_directive", adversary_coa_label=label,
            mission_who="Russian forces in the Baltic Region", mission_what=f"conducts {main_effort}",
            mission_when="through six planning periods from 10 September 2026",
            mission_where="in Estonia, Latvia, Kaliningrad Oblast and the Baltic approaches",
            mission_why="to retain the seized territory without provoking general war",
            end_state_objective_id="obj_rus_end_state",
            constraints=["Retain the seized ground in Ida-Viru and Latgale"],
            restraints=["No deliberate nuclear employment against Allied forces", "No strikes on the continental United States"],
            main_effort=main_effort, sequencing=sequencing, task_org=["unit_rus_6_caa", "unit_rus_76_gaad"],
            reserve_policy=reserve, mitigates_he_ids=[], risk_functional="expected", risk_alpha=None,
            opponent_model_id="om_rus", theory_of_victory=[]))
        for oid, w in RED_WEIGHTS.items():
            sobj.append(dict(strategy_id=sid, objective_id=oid, weight=w, rating_1_to_3=None))
        for rid, budget in RED_BUDGET.items():
            sres.append(dict(strategy_id=sid, resource_id=rid, budget=float(budget)))
        k, subj, pred, op, val, role, origin, stmt = RED_ASSUMPTION
        asms.append(dict(assumption_id=f"asm_rus_k{k}_{sid[4:]}", strategy_id=sid, index_k=k, statement=stmt,
                         subject_id=subj, predicate=pred, tolerance=dict(op=op, value=val), role=role,
                         jp50_logical=True, jp50_realistic=True, jp50_essential=True, origin=origin,
                         in_decision_matrix=True))
        for i, act in enumerate(acts):
            rules.append(dict(rule_id=f"rule_{sid[4:]}_{i}", strategy_id=sid, priority=i,
                              condition=RED_RULE_CONDITIONS[act], action_id=act, probability=1.0,
                              periods=_rule_periods(i, len(acts)), rationale_claim_ids=[], decision_point_id=None))
    return strategies, sobj, sres, rules, dps, asms


def opponent_models() -> list[dict]:
    """Sigma_-i. Blue faces the three Russian COAs; Russia faces the five Blue COAs uniformly."""
    return [
        dict(opponent_model_id="om_blue", actor_id=RED,
             distribution=[dict(strategy_id=sid, probability=p) for sid, _n, _l, p, *_ in RED_COAS]),
        dict(opponent_model_id="om_rus", actor_id=BLUE,
             distribution=[dict(strategy_id=sid, probability=0.2) for sid, *_ in COAS]),
    ]
