"""Scenario master data (fictional theater 'Meridian Sea'). Single source of truth for entities,
facts, change events, guidance chain, objectives, resources, actions, PIRs, problem sets, harmful
events, drivers, escalation edges, strategies and payoff structure. gen/scenario.md narrates the
same design; tests/test_p1.py cross-checks anchors between the two.

All names are fictional. Real organizations appear only as roles (organization_role entities).
No real nation, alliance, person or weapon designator is used.
"""
from __future__ import annotations

from datetime import date

T0 = date(2026, 9, 8)
BACKSTORY_DAY = -180
BATCH_DAYS = {1: 20, 2: 45, 3: 70}

# ---------------------------------------------------------------- entities
# (entity_id, entity_type, canonical_name, aliases, parent_id, description)
ACTORS = [
    ("ent_blue", "actor", "Joint Task Force Meridian", ["JTF Meridian", "Blue", "the joint task force"], None,
     "Blue: the joint task force of the supported combatant command operating in the Meridian Sea"),
    ("ent_varenia", "actor", "Varenia", ["Varenian Federation", "Red", "Varenian forces"], None,
     "Red: the Varenian Federation, a coastal state with coercive aims against Ilmara"),
]
POLITIES = [
    ("ent_ilmara", "polity", "Ilmara", ["Republic of Ilmara", "the Ilmaran government"], None, "partner polity on the western shore of the Kestrel Strait"),
    ("ent_corvane", "polity", "Corvane", ["Corvane Island Authority", "the Corvane authorities"], None, "neutral island polity whose Halden Airfield Blue seeks to use"),
    ("ent_sondria", "polity", "Sondria", ["Sondrian Republic", "the Sondrians"], None, "neutral polity on the eastern shore, leaning toward Varenia"),
]
LOCATIONS = [
    ("loc_kestrel_strait", "Kestrel Strait", ["the strait", "Kestrel narrows"], "maritime chokepoint between Ilmara and Sondria, 38 km wide at its narrowest"),
    ("loc_port_auberon", "Port Auberon", ["Auberon", "Auberon harbour"], "Ilmara's principal deep-water port and Blue's logistics hub"),
    ("loc_halden_airfield", "Halden Airfield", ["Halden", "Halden field"], "airfield on Corvane Island, 210 km south of the strait"),
    ("loc_corvane_island", "Corvane Island", ["the island"], "island polity territory hosting Halden Airfield and the southern passage"),
    ("loc_lisenne", "Lisenne", ["the Ilmaran capital"], "capital of Ilmara, 90 km inland from Port Auberon"),
    ("loc_cape_dorne", "Cape Dorne", ["Dorne headland", "the Dorne coast"], "Varenian headland 310 km from Port Auberon hosting the coastal missile brigade"),
    ("loc_novak_base", "Novak Naval Base", ["Novak", "Novak anchorage"], "Varenian fleet base 260 km east of the strait"),
    ("loc_serath_complex", "Serath Missile Complex", ["Serath", "the Serath site"], "Varenian long-range strike complex 480 km from Lisenne"),
    ("loc_kessary_plain", "Kessary Plain", ["Kessary", "the Kessary mobilization area"], "Varenian interior mobilization and training area"),
    ("loc_ravel_crossing", "Ravel Crossing", ["Ravel", "the Ravel border post"], "Ilmara–Sondria land border crossing and displacement route"),
    ("loc_meridian_sea", "Meridian Sea", ["the Meridian", "the open sea area"], "the sea area bounded by Ilmara, Sondria, Corvane and Varenia"),
    ("loc_sondria_camps", "Sondrian border camps", ["the border camps", "the Sondria camps"], "displaced-person camps 15 km inside Sondria from Ravel Crossing"),
]
# routes as infrastructure (throughput facts); other infrastructure
INFRA = [
    ("inf_kestrel_lane", "Kestrel Strait sea lane", ["the strait sea lane", "the main lane"], "loc_kestrel_strait", "shipping lane through the strait"),
    ("inf_southern_passage", "Southern Passage", ["the southern route", "the passage around Corvane"], "loc_corvane_island", "alternate sea route south of Corvane Island"),
    ("inf_auberon_halden_airbridge", "Auberon–Halden air bridge", ["the air bridge"], "loc_halden_airfield", "airlift route between Port Auberon and Halden Airfield"),
    ("inf_ilmara_coastal_road", "Ilmaran coastal road", ["the coastal road", "Route Lisenne"], "loc_lisenne", "road link from Port Auberon to Lisenne and Ravel Crossing"),
    ("inf_aldis_terminal", "Aldis gas terminal", ["Aldis", "the Aldis terminal"], "loc_port_auberon", "Ilmara's liquefied gas import terminal beside Port Auberon"),
    ("inf_veyra_station", "Veyra power station", ["Veyra", "the Veyra plant"], "loc_lisenne", "Ilmara's main gas-fired generating station"),
    ("inf_ilmara_grid_control", "Ilmaran grid control network", ["the grid control network", "Ilmara grid control"], "loc_lisenne", "supervisory control network of the Ilmaran electricity grid"),
    ("inf_blue_logistics_network", "Blue logistics network", ["the sustainment network", "the joint logistics network"], "loc_port_auberon", "Blue's sustainment information network at Port Auberon"),
    ("inf_kestrel_cable", "Kestrel undersea cable", ["the undersea cable", "the Kestrel cable"], "loc_kestrel_strait", "undersea data cable crossing the strait"),
    ("inf_dorne_radar", "Dorne coastal radar", ["the Dorne radar", "Cape Dorne surveillance radar"], "loc_cape_dorne", "Varenian coastal surveillance radar cueing the missile brigade"),
]
# units: (id, name, aliases, parent actor/polity, location, readiness, description)
UNITS = [
    # Blue
    ("unit_tg_kestrel", "Task Group Kestrel", ["TG Kestrel", "the task group", "the maritime group"], "ent_blue", "loc_corvane_island", 0.85, "Blue surface task group of five frigates"),
    ("unit_halden_brigade", "Halden Brigade", ["2nd Expeditionary Brigade", "the brigade at Halden"], "ent_blue", "loc_halden_airfield", 0.80, "Blue expeditionary brigade staged on Corvane Island"),
    ("unit_auberon_wing", "Auberon Air Expeditionary Wing", ["the wing", "Auberon Wing"], "ent_blue", "loc_port_auberon", 0.88, "Blue air expeditionary wing at Port Auberon"),
    ("unit_meridian_log_group", "Meridian Logistics Group", ["the logistics group", "Meridian Log Group"], "ent_blue", "loc_port_auberon", 0.90, "Blue sustainment group holding theater munitions and stocks"),
    ("unit_cyber_protection_team", "Meridian Cyber Protection Team", ["the cyber protection team", "the protection team"], "ent_blue", "loc_port_auberon", 0.75, "Blue defensive cyberspace team protecting the logistics network"),
    ("unit_lantern_battery", "Lantern Battery", ["the air defense battery", "Lantern"], "ent_blue", "loc_port_auberon", 0.82, "Blue air and missile defense battery protecting Port Auberon"),
    ("unit_meridian_isr_det", "Meridian Surveillance Detachment", ["the surveillance detachment", "the ISR detachment"], "ent_blue", "loc_halden_airfield", 0.78, "Blue intelligence, surveillance and reconnaissance detachment"),
    # Ilmara
    ("unit_ilm_coastal_div", "Ilmaran 3rd Coastal Division", ["3rd Coastal Division", "the Ilmaran division"], "ent_ilmara", "loc_lisenne", 0.65, "Ilmaran army division defending the coast and the capital"),
    ("unit_ilm_patrol_sqn", "Ilmaran Navy Patrol Squadron", ["the patrol squadron", "Ilmaran patrol boats"], "ent_ilmara", "loc_port_auberon", 0.70, "Ilmaran patrol boat squadron"),
    ("unit_ilm_border_guard", "Ilmaran Border Guard", ["the border guard"], "ent_ilmara", "loc_ravel_crossing", 0.60, "Ilmaran border force at Ravel Crossing"),
    # Varenia
    ("unit_var_northern_fleet", "Varenian Northern Fleet", ["the Northern Fleet", "Novak fleet"], "ent_varenia", "loc_novak_base", 0.70, "Varenian fleet of six frigates and four submarines"),
    ("unit_var_coastal_msl_bde", "7th Coastal Missile Brigade", ["the coastal missile brigade", "7th Brigade"], "ent_varenia", "loc_cape_dorne", 0.80, "Varenian brigade operating the Dorne-3 anti-ship missile"),
    ("unit_var_serath_regt", "Serath Missile Regiment", ["the Serath regiment"], "ent_varenia", "loc_serath_complex", 0.75, "Varenian regiment operating the Serath long-range strike system"),
    ("unit_var_12_mech_bde", "12th Mechanized Brigade", ["12th Brigade", "the 12th"], "ent_varenia", "loc_kessary_plain", 0.72, "Varenian active mechanized brigade"),
    ("unit_var_14_mech_bde", "14th Mechanized Brigade", ["14th Brigade", "the 14th"], "ent_varenia", "loc_kessary_plain", 0.68, "Varenian active mechanized brigade"),
    ("unit_var_21_reserve_bde", "21st Reserve Brigade", ["21st Brigade", "the reserve brigade"], "ent_varenia", "loc_kessary_plain", 0.40, "Varenian reserve brigade requiring mobilization"),
    ("unit_var_directorate_nine", "Varenian Signals Directorate Nine", ["Directorate Nine", "the signals directorate"], "ent_varenia", "loc_serath_complex", 0.80, "Varenian offensive cyberspace and signals organization"),
    ("unit_var_air_brigade", "Varenian Coastal Air Brigade", ["the air brigade", "Varenian air brigade"], "ent_varenia", "loc_novak_base", 0.66, "Varenian strike and reconnaissance aviation brigade"),
    # Sondria / Corvane
    ("unit_son_border_guard", "Sondrian Border Guard", ["the Sondrian guard"], "ent_sondria", "loc_sondria_camps", 0.50, "Sondrian border force administering the camps"),
    ("unit_corvane_coastal_authority", "Corvane Coastal Authority", ["the coastal authority"], "ent_corvane", "loc_corvane_island", 0.55, "Corvane's maritime and airfield authority"),
]
# programmatic sub-units: (parent unit id, prefix names)
SUBUNITS = {
    "unit_tg_kestrel": [("frigate Vigil", "Vigil"), ("frigate Cormorant", "Cormorant"), ("frigate Petrel", "Petrel"), ("frigate Gannet", "Gannet"), ("frigate Skua", "Skua")],
    "unit_halden_brigade": [("1st Battalion, Halden Brigade", "1st Battalion"), ("2nd Battalion, Halden Brigade", "2nd Battalion"), ("Halden Brigade Support Battalion", "Support Battalion")],
    "unit_auberon_wing": [("Auberon Wing Strike Squadron", "the strike squadron"), ("Auberon Wing Airlift Squadron", "the airlift squadron")],
    "unit_ilm_coastal_div": [("31st Ilmaran Regiment", "31st Regiment"), ("32nd Ilmaran Regiment", "32nd Regiment"), ("Ilmaran Coastal Artillery Group", "the coastal artillery")],
    "unit_var_northern_fleet": [("frigate Dravik", "Dravik"), ("frigate Morova", "Morova"), ("frigate Selen", "Selen"), ("frigate Tarnov", "Tarnov"), ("frigate Iskra", "Iskra"), ("frigate Vorna", "Vorna"),
                                ("submarine Ushen", "Ushen"), ("submarine Kalvo", "Kalvo"), ("submarine Reska", "Reska"), ("submarine Dolen", "Dolen")],
    "unit_var_coastal_msl_bde": [("1st Dorne Battery", "1st Battery"), ("2nd Dorne Battery", "2nd Battery"), ("3rd Dorne Battery", "3rd Battery")],
    "unit_var_12_mech_bde": [("121st Mechanized Battalion", "121st Battalion"), ("122nd Mechanized Battalion", "122nd Battalion"), ("123rd Mechanized Battalion", "123rd Battalion")],
    "unit_var_14_mech_bde": [("141st Mechanized Battalion", "141st Battalion"), ("142nd Mechanized Battalion", "142nd Battalion"), ("143rd Mechanized Battalion", "143rd Battalion")],
    "unit_var_21_reserve_bde": [("211th Reserve Battalion", "211th Battalion"), ("212th Reserve Battalion", "212th Battalion")],
    "unit_var_air_brigade": [("Varenian 4th Strike Squadron", "4th Strike Squadron"), ("Varenian 9th Reconnaissance Squadron", "9th Reconnaissance Squadron")],
    "unit_ilm_patrol_sqn": [("patrol boat Tern", "Tern"), ("patrol boat Plover", "Plover"), ("patrol boat Sanderling", "Sanderling"), ("patrol boat Curlew", "Curlew")],
    "unit_meridian_log_group": [("Auberon Supply Battalion", "the supply battalion"), ("Meridian Munitions Detachment", "the munitions detachment")],
    "unit_var_serath_regt": [("1st Serath Battery", "1st Serath Battery"), ("2nd Serath Battery", "2nd Serath Battery")],
    "unit_ilm_border_guard": [("Ravel Crossing Border Post", "the Ravel post"), ("Coastal Road Checkpoint", "the checkpoint")],
    "unit_lantern_battery": [("Lantern Battery Fire Unit Alpha", "fire unit Alpha"), ("Lantern Battery Fire Unit Bravo", "fire unit Bravo")],
}
# systems: (id, name, aliases, operated_by unit, range_km or None, count, description)
SYSTEMS = [
    ("sys_dorne_asm", "Dorne-3 coastal anti-ship missile", ["Dorne-3", "the Dorne missile", "the coastal missile"], "unit_var_coastal_msl_bde", 280, 12, "Varenian truck-launched anti-ship cruise missile"),
    ("sys_serath_lrs", "Serath long-range strike system", ["Serath system", "the Serath missile"], "unit_var_serath_regt", 900, 12, "Varenian long-range surface-to-surface strike missile"),
    ("sys_talon_frigate", "Talon-class frigate", ["Talon class", "Talon frigates"], "unit_var_northern_fleet", 220, 6, "Varenian guided-missile frigate"),
    ("sys_sable_submarine", "Sable-class submarine", ["Sable class", "Sable boats"], "unit_var_northern_fleet", None, 4, "Varenian diesel-electric attack submarine"),
    ("sys_kite_uav", "Kite-7 reconnaissance drone", ["Kite-7", "the Kite drone"], "unit_var_air_brigade", 600, 18, "Varenian medium-altitude reconnaissance drone"),
    ("sys_varen_strike_ac", "Varenian Sparrowhawk strike aircraft", ["Sparrowhawk", "the strike aircraft"], "unit_var_air_brigade", 750, 20, "Varenian multirole strike aircraft"),
    ("sys_vigil_frigate", "Vigil-class frigate", ["Vigil class", "Vigil frigates"], "unit_tg_kestrel", 250, 5, "Blue guided-missile frigate"),
    ("sys_halyard_sam", "Halyard air defense system", ["Halyard", "the Halyard battery"], "unit_lantern_battery", 120, 2, "Blue surface-to-air and missile defense system"),
    ("sys_skylark_strike", "Skylark strike aircraft", ["Skylark", "Skylark aircraft"], "unit_auberon_wing", 900, 24, "Blue multirole strike aircraft"),
    ("sys_meridian_standoff_munition", "Meridian standoff munition", ["the standoff munition", "standoff weapons"], "unit_meridian_log_group", 400, 180, "Blue air-launched precision standoff munition"),
    ("sys_gull_patrol_boat", "Gull-class patrol boat", ["Gull class", "Gull boats"], "unit_ilm_patrol_sqn", 60, 8, "Ilmaran coastal patrol boat"),
    ("sys_lark_isr_uav", "Lark surveillance drone", ["Lark", "the Lark drone"], "unit_meridian_isr_det", 800, 6, "Blue long-endurance surveillance drone"),
]
ROLES = [
    ("role_supported_ccdr", "the supported combatant commander", ["the supported CCDR", "the commander"], "commander of the supported combatant command; risk owner"),
    ("role_ccmd_j2", "the supported combatant command intelligence directorate", ["the supported CCMD J-2", "the theater J-2"], "J-2 of the supported combatant command"),
    ("role_ccmd_j5", "the supported combatant command plans directorate", ["the supported CCMD J-5", "the theater J-5"], "J-5 of the supported combatant command"),
    ("role_jioc", "the supported combatant command joint intelligence operations center", ["the JIOC", "the theater JIOC"], "JIOC validating and prioritizing collection requirements"),
    ("role_jcmb", "the joint collection management board", ["the JCMB"], "board that prioritizes requirements into the joint integrated prioritized collection list"),
    ("role_cjcs", "the Chairman of the Joint Chiefs of Staff", ["the Chairman", "CJCS"], "issues the National Military Strategy and the Joint Strategic Campaign Plan"),
    ("role_secwar", "the Secretary of War", ["SecWar", "the Secretary"], "issues the National Defense Strategy"),
    ("role_president", "the President", ["the national command authority"], "issues the National Security Strategy"),
    ("role_country_team", "the country team in Lisenne", ["the embassy country team"], "diplomatic mission coordinating basing and relief"),
]
PROBLEM_SET_ENTITIES = [
    ("ent_ps_chokepoint", "Maritime chokepoint problem set", ["the chokepoint problem set"], "loc_kestrel_strait"),
    ("ent_ps_energy", "Energy infrastructure problem set", ["the energy problem set"], "loc_lisenne"),
    ("ent_ps_cyber", "Cyber problem set", ["the cyber problem set"], "loc_port_auberon"),
    ("ent_ps_humanitarian", "Humanitarian problem set", ["the humanitarian problem set"], "loc_ravel_crossing"),
]

# ---------------------------------------------------------------- facts
# Base facts valid from BACKSTORY_DAY (unless from_day given) and open-ended unless changed.
# (subject, predicate, value_or_object, estimative, likelihood, confidence, from_day)
BASE_FACTS = [
    # actors / polities
    ("ent_varenia", "intent", "coercive", True, "likely", "moderate", -120),
    ("ent_varenia", "mobilized_brigades", 0, False, None, "high", -180),
    ("ent_varenia", "mobilization_days", 35, True, "likely", "moderate", -150),   # days to mobilize two brigades; assumption k1 needs >= 45; expires day -20 (see EXPIRES)
    ("ent_varenia", "cyber_capacity", "limited", True, "likely", "moderate", -90),
    ("ent_varenia", "controls", "loc_cape_dorne", False, None, "high", -180),
    ("ent_varenia", "controls", "loc_novak_base", False, None, "high", -180),
    ("ent_ilmara", "alignment", "blue_aligned", False, None, "high", -180),
    ("ent_ilmara", "basing_access", True, False, None, "high", -180),
    ("ent_corvane", "alignment", "neutral", False, None, "high", -180),
    ("ent_sondria", "alignment", "neutral", True, "likely", "moderate", -180),
    ("ent_sondria", "basing_access", False, False, None, "high", -180),
    ("ent_sondria", "displaced_persons", 4000, False, None, "moderate", -60),
    ("ent_blue", "munitions_stock_days", 45, False, None, "high", -30),
    ("ent_blue", "posture_state", "postured_to_react", False, None, "high", -30),
    ("ent_blue", "controls", "loc_meridian_sea", True, "likely", "moderate", -30),
    # locations
    ("loc_kestrel_strait", "status", "operational", False, None, "high", -180),
    ("loc_port_auberon", "status", "operational", False, None, "high", -180),
    ("loc_port_auberon", "hosts", "unit_meridian_log_group", False, None, "high", -60),
    ("loc_port_auberon", "hosts", "unit_auberon_wing", False, None, "high", -60),
    ("loc_halden_airfield", "status", "degraded", False, None, "high", -180),
    ("loc_halden_airfield", "hosts", "unit_halden_brigade", False, None, "high", -45),
    ("loc_corvane_island", "hosts", "unit_tg_kestrel", False, None, "high", -45),
    ("loc_lisenne", "hosts", "unit_ilm_coastal_div", False, None, "high", -180),
    ("loc_cape_dorne", "hosts", "unit_var_coastal_msl_bde", False, None, "high", -180),
    ("loc_novak_base", "hosts", "unit_var_northern_fleet", False, None, "high", -180),
    ("loc_serath_complex", "hosts", "unit_var_serath_regt", False, None, "high", -180),
    ("loc_kessary_plain", "hosts", "unit_var_12_mech_bde", False, None, "high", -180),
    ("loc_ravel_crossing", "status", "operational", False, None, "high", -180),
    ("loc_meridian_sea", "status", "operational", False, None, "high", -180),
    ("loc_sondria_camps", "displaced_persons", 4000, False, None, "moderate", -60),
    ("loc_sondria_camps", "hosts", "unit_son_border_guard", False, None, "high", -180),
    # infrastructure
    ("inf_kestrel_lane", "throughput_per_day", 120, False, None, "high", -180),
    ("inf_kestrel_lane", "status", "operational", False, None, "high", -180),
    ("inf_southern_passage", "throughput_per_day", 40, False, None, "moderate", -180),
    ("inf_southern_passage", "status", "operational", False, None, "high", -180),
    ("inf_auberon_halden_airbridge", "throughput_per_day", 18, False, None, "high", -60),
    ("inf_auberon_halden_airbridge", "status", "operational", False, None, "high", -60),
    ("inf_ilmara_coastal_road", "throughput_per_day", 900, False, None, "moderate", -180),
    ("inf_ilmara_coastal_road", "status", "operational", False, None, "high", -180),
    ("inf_aldis_terminal", "status", "operational", False, None, "high", -180),
    ("inf_aldis_terminal", "supplies", "inf_veyra_station", False, None, "high", -180),
    ("inf_veyra_station", "capacity_mw", 640, False, None, "high", -180),
    ("inf_veyra_station", "status", "operational", False, None, "high", -180),
    ("inf_veyra_station", "outage_hours", 6, False, None, "high", -30),
    ("inf_veyra_station", "supplies", "loc_port_auberon", False, None, "high", -180),
    ("inf_ilmara_grid_control", "posture_state", "unmitigated", False, None, "moderate", -90),
    ("inf_ilmara_grid_control", "status", "operational", False, None, "high", -180),
    ("inf_blue_logistics_network", "posture_state", "unmitigated", False, None, "high", -30),
    ("inf_blue_logistics_network", "status", "operational", False, None, "high", -60),
    ("inf_blue_logistics_network", "supplies", "unit_meridian_log_group", False, None, "high", -60),
    ("inf_kestrel_cable", "status", "operational", False, None, "high", -180),
    ("inf_kestrel_cable", "supplies", "loc_lisenne", False, None, "high", -180),
    ("inf_dorne_radar", "status", "operational", False, None, "moderate", -120),
    ("inf_dorne_radar", "supplies", "unit_var_coastal_msl_bde", False, None, "moderate", -120),
    # units: posture
    ("unit_tg_kestrel", "posture_state", "postured_to_react", False, None, "high", -45),
    ("unit_halden_brigade", "posture_state", "out_of_position", False, None, "high", -45),
    ("unit_lantern_battery", "posture_state", "hardened", False, None, "high", -60),
    ("unit_cyber_protection_team", "posture_state", "unmitigated", False, None, "moderate", -30),
    ("unit_meridian_log_group", "munitions_stock_days", 45, False, None, "high", -30),
    ("unit_var_directorate_nine", "intent", "coercive", True, "likely", "moderate", -90),
    ("unit_var_coastal_msl_bde", "intent", "coercive", True, "very_likely", "moderate", -120),
    ("unit_var_northern_fleet", "intent", "coercive", True, "likely", "low", -120),
    ("unit_var_21_reserve_bde", "status", "degraded", False, None, "moderate", -180),
    ("unit_ilm_patrol_sqn", "status", "operational", False, None, "high", -180),
    ("unit_son_border_guard", "status", "degraded", False, None, "moderate", -90),
    # problem-set entities
    ("ent_ps_chokepoint", "status", "operational", False, None, "high", -30),
    ("ent_ps_energy", "status", "operational", False, None, "high", -30),
    ("ent_ps_cyber", "status", "operational", False, None, "high", -30),
    ("ent_ps_humanitarian", "status", "operational", False, None, "high", -30),
]

# Facts whose validity window closes before T0 without a successor (stale material): (subject, predicate, valid_to_day)
EXPIRES = [("ent_varenia", "mobilization_days", -20)]

# Future-valid projections (estimative facts whose valid_from is after T0; they drive mid/long-term risk):
# (subject, predicate, value, valid_from_day, likelihood, confidence)
FUTURE_FACTS = [
    ("sys_dorne_asm", "count", 16, 900, "likely", "moderate"),
    ("sys_serath_lrs", "count", 20, 1100, "likely", "low"),
]

# Backstory change events before T0 (material for stale_echo): (subject, predicate, old, new, change_day)
BACKSTORY_CHANGES = [
    ("sys_dorne_asm", "count", 8, 12, -60),
    ("unit_tg_kestrel", "located_at", "loc_port_auberon", "loc_corvane_island", -45),
    ("inf_veyra_station", "outage_hours", 30, 6, -30),
    ("ent_sondria", "displaced_persons", 1500, 4000, -60),
]

# Inject change events: (batch, subject, predicate, new value/object, valid_from_day, estimative, likelihood, confidence)
INJECT_CHANGES = {
    1: [
        ("sys_dorne_asm", "range_km", 340, 15, False, None, "moderate"),          # violates k0 (<= 300)
        ("ent_varenia", "mobilized_brigades", 2, 18, False, None, "high"),        # drives he_01 / he_07
        ("ent_varenia", "mobilization_days", 21, 18, False, None, "high"),        # k1 (>= 45) violated harder, observed
        ("unit_tg_kestrel", "posture_state", "vulnerable", 16, False, None, "high"),
        ("unit_var_21_reserve_bde", "status", "operational", 17, False, None, "moderate"),
        ("unit_var_northern_fleet", "readiness", 0.82, 14, False, None, "moderate"),
    ],
    2: [
        ("ent_corvane", "basing_access", True, 40, False, None, "high"),           # answers top JIPCL requirement; k2 unknown -> holds
        ("loc_halden_airfield", "status", "operational", 41, False, None, "high"),
        ("unit_meridian_log_group", "munitions_stock_days", 41, 38, False, None, "high"),
        ("ent_blue", "munitions_stock_days", 41, 38, False, None, "high"),
        ("unit_ilm_patrol_sqn", "readiness", 0.78, 39, False, None, "moderate"),
        ("unit_halden_brigade", "posture_state", "postured_to_react", 42, False, None, "high"),
    ],
    3: [
        ("ent_varenia", "cyber_capacity", "extensive", 62, True, "roughly_even_chance", "moderate"),  # dominant driver -> forced choice
        ("ent_sondria", "displaced_persons", 26000, 63, False, None, "moderate"),
        ("loc_sondria_camps", "displaced_persons", 26000, 63, False, None, "moderate"),
        ("ent_sondria", "alignment", "red_aligned", 60, True, "likely", "low"),
        ("unit_son_border_guard", "readiness", 0.35, 64, False, None, "moderate"),
        ("loc_ravel_crossing", "status", "degraded", 63, False, None, "high"),
    ],
}
# Batch 3 contradiction: a reliability-D news source asserts a throughput of 60 against the approved
# reliability-B claim of 120. The truth value does not change; the claim stays `proposed`.
CONTRADICTION = {"batch": 3, "subject": "inf_kestrel_lane", "predicate": "throughput_per_day", "false_value": 60, "asserted_day": 68}

# ---------------------------------------------------------------- guidance chain (JSPS)
GUIDANCE = [
    ("gd_nss", "NSS", "National Security Strategy (fictional extract): secure partners and the global commons", "the President", None, []),
    ("gd_nds", "NDS", "National Defense Strategy (fictional extract): deter coercion of partners", "the Secretary of War", "gd_nss", []),
    ("gd_nms", "NMS", "National Military Strategy (fictional extract): objectives for the Meridian region", "the Chairman of the Joint Chiefs of Staff", "gd_nds", ["obj_nms_deter_partners", "obj_nms_commons"]),
    ("gd_jscp", "JSCP", "Joint Strategic Campaign Plan (fictional extract): Meridian tasking", "the Chairman of the Joint Chiefs of Staff", "gd_nms", []),
    ("gd_ccp_meridian", "CCP", "Combatant Command Campaign Plan Meridian (fictional)", "the supported combatant commander", "gd_jscp", ["obj_deter", "obj_navigation", "obj_preserve_force", "obj_limit_escalation"]),
    ("gd_conplan_meridian", "contingency_plan", "Contingency Plan Meridian Shield (fictional)", "the supported combatant commander", "gd_ccp_meridian", ["obj_deter", "obj_navigation", "obj_preserve_force", "obj_limit_escalation"]),
]

# ---------------------------------------------------------------- objectives (Blue) and Red
# (objective_id, actor, name, kind, guidance_id, parent, metric, aspiration, statement)
OBJECTIVES = [
    ("obj_nms_deter_partners", "ent_blue", "deterrence of aggression against partners in the Meridian region", "objective", "gd_nms", None, "absence of armed coercion of partners", None, "Deter aggression against Meridian partners"),
    ("obj_nms_commons", "ent_blue", "access to the maritime commons", "objective", "gd_nms", None, "freedom of navigation sustained", None, "Preserve access to the maritime commons"),
    ("obj_end_state", "ent_blue", "Varenian coercion of Ilmara ended with the Kestrel Strait open and Blue forces intact", "end_state", "gd_ccp_meridian", None, "end state conditions met", None, "Varenian coercion ended, strait open, force intact"),
    ("obj_deter", "ent_blue", "deterrence of Varenian aggression against Ilmara", "objective", "gd_ccp_meridian", "obj_end_state", "probability that Varenia refrains from armed action against Ilmara", 0.5, "Deter Varenian aggression against Ilmara"),
    ("obj_navigation", "ent_blue", "freedom of navigation through the Kestrel Strait", "objective", "gd_ccp_meridian", "obj_end_state", "fraction of planned transits completed", 0.5, "Maintain freedom of navigation through the Kestrel Strait"),
    ("obj_preserve_force", "ent_blue", "preservation of the force", "objective", "gd_ccp_meridian", "obj_end_state", "fraction of combat power retained", 0.5, "Preserve the force"),
    ("obj_limit_escalation", "ent_blue", "limited escalation and protection of civilians", "objective", "gd_ccp_meridian", "obj_end_state", "absence of strikes on population centres and displacement kept low", 0.5, "Limit escalation and protect civilians"),
    # effects (JP 5-0 Fig. IV-9), parent = objective they support
    ("obj_eff_port_coverage", "ent_blue", "Port Auberon remains outside effective Varenian coastal missile coverage", "effect", "gd_ccp_meridian", "obj_preserve_force", "range of the Dorne-3 missile below the distance to Port Auberon", None, None),
    ("obj_eff_transits", "ent_blue", "strait transits sustained at or above eighty per day", "effect", "gd_ccp_meridian", "obj_navigation", "daily transits", None, None),
    ("obj_eff_sustainment", "ent_blue", "Blue sustainment at Port Auberon uninterrupted", "effect", "gd_ccp_meridian", "obj_preserve_force", "days of supply and network status", None, None),
    ("obj_eff_partner_integration", "ent_blue", "Ilmaran patrol forces integrated in combined patrols", "effect", "gd_ccp_meridian", "obj_deter", "combined patrol sorties", None, None),
    ("obj_eff_basing", "ent_blue", "Halden Airfield available for Blue reinforcement", "effect", "gd_ccp_meridian", "obj_deter", "basing access granted", None, None),
    ("obj_eff_civil", "ent_blue", "displacement across Ravel Crossing kept below camp capacity", "effect", "gd_ccp_meridian", "obj_limit_escalation", "displaced persons", None, None),
    # Red
    ("obj_red_end_state", "ent_varenia", "Ilmara coerced into concessions without general war", "end_state", None, None, "concessions obtained", None, "Coerce Ilmara without general war"),
    ("obj_red_coerce", "ent_varenia", "coercion of Ilmara", "objective", None, "obj_red_end_state", "concessions obtained", 0.4, "Coerce Ilmara"),
    ("obj_red_preserve", "ent_varenia", "preservation of Varenian forces", "objective", None, "obj_red_end_state", "combat power retained", 0.4, "Preserve Varenian forces"),
]
BLUE_WEIGHTS = {"obj_deter": 0.35, "obj_navigation": 0.30, "obj_preserve_force": 0.20, "obj_limit_escalation": 0.15}
RED_WEIGHTS = {"obj_red_coerce": 0.6, "obj_red_preserve": 0.4}

# ---------------------------------------------------------------- resources and actions
RESOURCES = [
    ("res_isr_hours", "surveillance flight hours", "hours"),
    ("res_sorties", "strike and patrol sorties", "sorties"),
    ("res_munitions", "precision standoff munitions", "rounds"),
    ("res_lift", "sealift and airlift capacity", "tons"),
    ("res_sustain_days", "sustainment days of supply", "days"),
]
# (action_id, actor, name, tactic_class, line_of_effort, mechanism, cost dict, effects)
ACTIONS = [
    ("act_blue_forward_deploy_tg", "ent_blue", "forward deploy Task Group Kestrel to Port Auberon", "posture", "maritime presence", "deter_by_presence", {"res_lift": 20, "res_sustain_days": 5}, [{"variable": "blue_posture", "delta": "forward"}]),
    ("act_blue_disperse_tg", "ent_blue", "disperse Task Group Kestrel across the Meridian Sea", "posture", "maritime presence", "deny", {"res_sustain_days": 4}, [{"variable": "blue_posture", "delta": "distributed"}]),
    ("act_blue_hold_corvane", "ent_blue", "hold Task Group Kestrel south of Corvane Island", "posture", "maritime presence", "delay", {"res_sustain_days": 2}, [{"variable": "blue_posture", "delta": "holding"}]),
    ("act_blue_combined_patrol", "ent_blue", "conduct combined patrols with the Ilmaran patrol squadron", "posture", "partner integration", "deter_by_presence", {"res_sorties": 10, "res_sustain_days": 2}, [{"variable": "strait_status", "delta": "open"}]),
    ("act_blue_isr_surge", "ent_blue", "surge surveillance over Kessary Plain and Cape Dorne", "isr", "intelligence", "inform", {"res_isr_hours": 40}, []),
    ("act_blue_strike_coastal_battery", "ent_blue", "strike the 7th Coastal Missile Brigade", "strike", "fires", "defeat", {"res_sorties": 24, "res_munitions": 40}, [{"variable": "strait_status", "delta": "open"}]),
    ("act_blue_air_defense_auberon", "ent_blue", "defend Port Auberon with Lantern Battery", "posture", "protection", "deny", {"res_munitions": 10}, []),
    ("act_blue_reinforce_halden", "ent_blue", "reinforce through Halden Airfield", "logistics", "reinforcement", "defeat", {"res_lift": 60, "res_sustain_days": 10}, [{"variable": "blue_posture", "delta": "forward"}]),
    ("act_blue_preposition_stocks", "ent_blue", "preposition stocks at Port Auberon and Halden", "logistics", "sustainment", "sustain", {"res_lift": 30}, []),
    ("act_blue_cyber_harden", "ent_blue", "harden the Blue logistics network", "cyber", "protection", "deny", {"res_sustain_days": 1}, [{"variable": "cyber_disruption", "delta": "none"}]),
    ("act_blue_strategic_messaging", "ent_blue", "message deterrence resolve to Varenia and the region", "information", "information", "influence", {}, []),
    ("act_blue_basing_negotiation", "ent_blue", "negotiate basing access with Corvane", "diplomatic", "partner integration", "enable", {}, [{"variable": "corvane_basing", "delta": "granted"}]),
    ("act_blue_relief_ops", "ent_blue", "support relief operations at Ravel Crossing", "logistics", "humanitarian", "protect", {"res_lift": 25, "res_sustain_days": 5}, [{"variable": "displacement", "delta": "low"}]),
    # Red
    ("act_red_harass_shipping", "ent_varenia", "harass shipping in the Kestrel Strait", "posture", "maritime coercion", "coerce", {"res_sorties": 8}, [{"variable": "strait_status", "delta": "contested"}]),
    ("act_red_mobilize", "ent_varenia", "mobilize reserve brigades on Kessary Plain", "logistics", "mobilization", "threaten", {"res_sustain_days": 6}, [{"variable": "red_mobilized_brigades", "delta": 2}]),
    ("act_red_missile_strike_port", "ent_varenia", "strike Port Auberon with coastal missiles", "strike", "fires", "defeat", {"res_munitions": 30}, [{"variable": "red_strike", "delta": "port"}]),
    ("act_red_seize_approaches", "ent_varenia", "seize the eastern approaches of the strait", "posture", "maritime coercion", "seize", {"res_sustain_days": 8, "res_sorties": 20}, [{"variable": "strait_status", "delta": "closed"}]),
    ("act_red_cyber_logistics", "ent_varenia", "disrupt the Blue logistics network", "cyber", "cyber", "disrupt", {}, [{"variable": "cyber_disruption", "delta": "partial"}]),
    ("act_red_strike_energy", "ent_varenia", "strike Ilmaran energy infrastructure", "strike", "fires", "coerce", {"res_munitions": 20}, [{"variable": "red_strike", "delta": "energy"}]),
    ("act_red_info_ops", "ent_varenia", "conduct information operations against Ilmaran resolve", "information", "information", "influence", {}, []),
    ("act_red_hold", "ent_varenia", "hold forces in garrison", "posture", "posture", "wait", {}, []),
]
STATE_VARIABLES = [
    {"name": "red_mobilized_brigades", "domain": [0, 1, 2, 3]},
    {"name": "strait_status", "domain": ["open", "contested", "closed"]},
    {"name": "corvane_basing", "domain": ["pending", "granted", "denied"]},
    {"name": "red_strike", "domain": ["none", "port", "energy"]},
    {"name": "cyber_disruption", "domain": ["none", "partial", "severe"]},
    {"name": "displacement", "domain": ["low", "high"]},
    {"name": "blue_posture", "domain": ["forward", "distributed", "holding"]},
]
OBSERVABLES = [{"actor_id": "ent_blue", "variable": v["name"]} for v in STATE_VARIABLES] + [
    {"actor_id": "ent_varenia", "variable": "blue_posture"},
    {"actor_id": "ent_varenia", "variable": "strait_status"},
    {"actor_id": "ent_varenia", "variable": "corvane_basing"},
    {"actor_id": "ent_varenia", "variable": "red_mobilized_brigades"},
]
HORIZON_MAP = [{"period": 1, "jsps_horizon": "near"}, {"period": 2, "jsps_horizon": "near"}, {"period": 3, "jsps_horizon": "mid"},
               {"period": 4, "jsps_horizon": "mid"}, {"period": 5, "jsps_horizon": "long"}, {"period": 6, "jsps_horizon": "long"}]

# ---------------------------------------------------------------- PIRs
PIRS = [
    ("pir_01", "Will Varenia attempt to close the Kestrel Strait to Blue and partner shipping within the next thirty days?", "the supported combatant commander", 1),
    ("pir_02", "Will Corvane grant Blue basing access at Halden Airfield before reinforcement is required?", "the supported combatant commander", 2),
    ("pir_03", "Can Varenian coastal missiles range Port Auberon and the strait sea lane?", "the supported combatant commander", 3),
    ("pir_04", "Can Varenia disrupt Blue sustainment networks at Port Auberon?", "the supported combatant commander", 4),
]

DENYLIST_NOTE = "see gen/denylist.txt"
