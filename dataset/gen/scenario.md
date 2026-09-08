# Scenario: the Meridian Sea (fictional theater)

Everything below is fictional: the theater, the polities, the units, the systems, the events.
Doctrine, organizations, processes and product formats are real and cited in
`doctrine/EXTRACTS.md`. Real organizations appear only as roles ("the supported combatant
commander", "the supported combatant command J-2", "the Chairman of the Joint Chiefs of Staff").
`gen/scenario_data.py` holds the same design as data; `tests/test_p1.py` cross-checks anchors.

T0 = 08 September 2026 (day 0). Backstory facts are valid from day −180 (12 March 2026). The three
inject batches land at days +20 (28 September), +45 (23 October) and +70 (17 November) 2026.

## 1. Theater sketch

The Meridian Sea is bounded by four polities. **Ilmara** (partner, Blue-aligned) holds the western
shore and Port Auberon. **Varenia** (Red) holds the eastern coast with Cape Dorne, Novak Naval
Base and the Serath Missile Complex. **Corvane** is a neutral island polity to the south whose
Halden Airfield Blue wants to use. **Sondria** is a neutral polity on the eastern shore of the
strait that leans toward Varenia and hosts the border camps beyond Ravel Crossing.

Geography as a graph (12 locations; edges are routes carried as infrastructure entities with
throughput facts):

| location | role | notes |
|---|---|---|
| Kestrel Strait | maritime chokepoint | 38 km wide; sea lane throughput 120 transits/day |
| Port Auberon | Ilmara's deep-water port, Blue logistics hub | 310 km from Cape Dorne |
| Halden Airfield | airfield on Corvane Island | 210 km south of the strait; degraded at T0 |
| Corvane Island | neutral island polity | Task Group Kestrel and Halden Brigade staged here |
| Lisenne | Ilmaran capital | 90 km inland; Veyra power station, grid control network |
| Cape Dorne | Varenian headland | 7th Coastal Missile Brigade, Dorne coastal radar |
| Novak Naval Base | Varenian fleet base | 260 km east of the strait |
| Serath Missile Complex | Varenian long-range strike site | 480 km from Lisenne |
| Kessary Plain | Varenian mobilization area | 12th, 14th, 21st brigades |
| Ravel Crossing | Ilmara–Sondria land border | displacement route |
| Meridian Sea | open sea area | dispersal area for a distributed posture |
| Sondrian border camps | displaced-person camps | 4,000 persons at T0 |

Routes: Kestrel Strait sea lane (120/day), Southern Passage around Corvane (40/day),
Auberon–Halden air bridge (18 sorties/day), Ilmaran coastal road (900 vehicles/day).

## 2. Actors, units, systems

Blue = **Joint Task Force Meridian** (aliases JTF Meridian, Blue), the joint task force of the
supported combatant command: Task Group Kestrel (five Vigil-class frigates), Halden Brigade (two
battalions and a support battalion), Auberon Air Expeditionary Wing (strike and airlift squadrons;
24 Skylark strike aircraft), Meridian Logistics Group (45 days of Meridian standoff munitions at
T0), Meridian Cyber Protection Team, Lantern Battery (two Halyard air defense fire units), Meridian
Surveillance Detachment (six Lark surveillance drones).

Ilmara: 3rd Coastal Division (two regiments and a coastal artillery group), Navy Patrol Squadron
(eight Gull-class patrol boats), Border Guard.

Red = **Varenia**: Northern Fleet at Novak (six Talon-class frigates, four Sable-class
submarines), 7th Coastal Missile Brigade at Cape Dorne (three batteries; twelve Dorne-3 coastal
anti-ship missile launchers, range 280 km at T0), Serath Missile Regiment (twelve Serath
long-range strike missiles, 900 km), 12th and 14th Mechanized Brigades and the 21st Reserve
Brigade on Kessary Plain, Varenian Signals Directorate Nine (offensive cyberspace), Coastal Air
Brigade (Kite-7 drones, Sparrowhawk strike aircraft).

Sondria: Border Guard. Corvane: Coastal Authority. Organization roles: the supported combatant
commander (risk owner), the supported combatant command J-2 and J-5, the joint intelligence
operations center, the joint collection management board, the Chairman, the Secretary of War, the
President, the country team in Lisenne.

Entity count ≈ 120 (2 actors, 3 polities, 12 locations, 10 infrastructure, 20 units + 47
sub-units, 12 systems, 9 roles, 4 problem-set entities). Every non-role entity has ≥ 2 facts.

## 3. Timeline and change events

| day | date | event |
|---|---|---|
| −180 | 12 Mar 2026 | backstory baseline |
| −60 | 10 Jul 2026 | Dorne-3 launcher count 8 → 12; Sondria displaced persons 1,500 → 4,000 (stale-echo material) |
| −45 | 25 Jul 2026 | Task Group Kestrel moves from Port Auberon to Corvane Island |
| −30 | 09 Aug 2026 | Veyra outage hours 30 → 6 |
| −20 | 19 Aug 2026 | the mobilization-time estimate for Varenia expires (assumption k1 becomes stale) |
| 0 | 08 Sep 2026 | T0: corpus published |
| +20 | 28 Sep 2026 | **batch 1** — Dorne-3 range 280 → 340 km (valid from +15); Varenia mobilizes two brigades in 21 days (valid +18); Task Group Kestrel posture postured-to-react → vulnerable; 21st Reserve Brigade operational; Northern Fleet readiness 0.70 → 0.82 |
| +45 | 23 Oct 2026 | **batch 2** — Corvane grants basing access (valid +40); Halden Airfield operational; munitions 45 → 41 days; Ilmaran patrol squadron readiness 0.70 → 0.78; Halden Brigade posture out-of-position → postured-to-react |
| +70 | 17 Nov 2026 | **batch 3** — a reliability-D news source contradicts the approved strait throughput (60 vs 120); the J-2 assesses a roughly even chance that Varenian cyber capacity against logistics is extensive; displaced persons 4,000 → 26,000; Sondria assessed likely Red-aligned (low confidence) |
| +900 / +1100 | 2029 / 2029 | projections: Dorne-3 launchers 16 by early 2029 (likely, moderate); Serath missiles 20 by late 2029 (likely, low) — they drive mid-/long-term risk |

## 4. Guidance chain (JSPS nesting)

`gd_nss` (NSS, the President) → `gd_nds` (NDS, the Secretary of War) → `gd_nms` (NMS, the
Chairman; objectives `obj_nms_deter_partners`, `obj_nms_commons`) → `gd_jscp` (JSCP, the Chairman)
→ `gd_ccp_meridian` (CCP, the supported combatant commander; objectives `obj_deter`,
`obj_navigation`, `obj_preserve_force`, `obj_limit_escalation`, each nested under an NMS
objective by `parent_objective_id`/end state) → `gd_conplan_meridian` (contingency plan Meridian
Shield). The three Blue COAs carry `guidance_source = gd_ccp_meridian` and `echelon =
theater_strategic`. Their theory-of-victory chains reach all four CCP objectives (suitable test).

## 5. Ends: end state, objectives, effects (JP 5-0 Fig. IV-9)

End state `obj_end_state`: Varenian coercion of Ilmara ended with the Kestrel Strait open and
Blue forces intact. Objectives (weights = evaluation criteria, JP 5-0 App. F; aspiration τ = 0.5 on
each, payoffs in [0, 1]): deter Varenian aggression (0.35), freedom of navigation (0.30), preserve
the force (0.20), limit escalation and protect civilians (0.15). Effects: Port Auberon outside
Dorne-3 coverage; transits ≥ 80/day; sustainment uninterrupted; Ilmaran patrols integrated; Halden
available; displacement below camp capacity.

## 6. Game form

`N = {Blue, Varenia}`; H = 6 periods (1–2 near-term, 3–4 mid-term, 5–6 long-term). State
variables: red_mobilized_brigades {0..3}, strait_status {open, contested, closed}, corvane_basing
{pending, granted, denied}, red_strike {none, port, energy}, cyber_disruption {none, partial,
severe}, displacement {low, high}, blue_posture {forward, distributed, holding}. Blue observes all;
Varenia observes blue_posture, strait_status, corvane_basing, red_mobilized_brigades. Resources (M):
surveillance flight hours, sorties, precision standoff munitions, lift tons, sustainment days.
Blue actions (13) and Red actions (8) are listed in `scenario_data.ACTIONS` with tactic class,
line of effort, mechanism and cost.

## 7. Courses of action

Blue (three COAs, `echelon = theater_strategic`):

| COA | name | main effort | sequencing | mechanism | depends on |
|---|---|---|---|---|---|
| `str_blue_1` | Anchor (forward presence) | maritime presence at Port Auberon and Halden | simultaneous | deter by presence | k0 range, k2 basing, k3 throughput, k5 munitions |
| `str_blue_2` | Lattice (distributed denial) | dispersed maritime and air denial from the Meridian Sea and the Ilmaran coast | simultaneous | deny | k0 (weakly), k3, k4 cyber, k5 |
| `str_blue_3` | Bulwark (delay and reinforce) | hold south of Corvane, delay with Ilmaran forces, reinforce through Halden | sequential | delay then defeat | k1 (Red cannot mobilize two brigades in 30 days — `realistic = false`), k2, k5 |

Each COA has a mission statement (who/what/when/where/why), 8–10 policy rules conditioned on the
observables, 2–3 decision points tied to PIRs, constraints (must do: maintain the combined patrol
with Ilmara; keep Lantern Battery at Port Auberon) and restraints (cannot do: no strikes on
Varenian territory before a strait closure; no forces into Sondria). Red COAs (support of
Σ_-Blue): `str_red_ml` coercive pressure (most likely, 0.55), `str_red_md` strait seizure (most
dangerous, 0.25), `str_red_alt` energy coercion (alternative, 0.20).

## 8. Assumptions (Θ, K = 6) and the 3×6 dependency matrix

| k | statement | grounding (subject, predicate) tolerance | T0 status | realistic | COA 1 | COA 2 | COA 3 |
|---|---|---|---|---|---|---|---|
| 0 | Dorne-3 range does not reach Port Auberon (≤ 300 km) | (Dorne-3, range_km) ≤ 300; T0 claim 280, factual, moderate | holds (p ≈ 0.90) | yes | ● | ○ | |
| 1 | Varenia cannot mobilize two brigades within 30 days (≥ 45 days) | (Varenia, mobilization_days) ≥ 45; T0 estimate 35 days expired day −20 | stale (p ≈ 0.35) | **no** (assumes away a Red capability) | | | ● |
| 2 | Corvane grants basing at Halden | (Corvane, basing_access) == true; no approved claim at T0 | unknown (p = 0.5) | yes | ● | ○ | ● |
| 3 | Strait throughput stays ≥ 80/day | (Kestrel sea lane, throughput_per_day) ≥ 80; T0 claim 120, factual, high | holds (p = 0.97) | yes | ● | ● | |
| 4 | Varenian cyber capacity against Blue logistics is limited | (Varenia, cyber_capacity) == limited; T0 estimate likely, moderate | holds (p ≈ 0.65) | yes | | ● | |
| 5 | Blue munitions stock ≥ 30 days | (Meridian Logistics Group, munitions_stock_days) ≥ 30; T0 claim 45, factual, high | holds (p = 0.97) | yes | ● | ● | ● |

● strong dependence (large δ_k), ○ weak. Every COA depends on ≥ 3 assumptions; every assumption
grounds ≥ 1 COA. k1 is authored `jp50_realistic = false` and is flagged in COA 3's decision matrix.
k2 carries the highest EVPI at T0 (p = 0.5 and the argmax switches on it), so its collection
requirement tops the JIPCL.

## 9. Problem sets and risk context statements (JRAM Fig. 3)

Four problem sets, each a tier-0 node with its own risk context statement (six lettered
paragraphs rendered from `problem_sets` fields), risk owner and initial tolerance.

**PS1 Maritime chokepoint** (`ps_chokepoint`). a. Strategic context: MSR and MR associated with
freedom of navigation through the Kestrel Strait and the CCP objective to deter Varenia, as
directed by the NMS and the CCP; things of value are the strait sea lane and Task Group Kestrel,
in a globally integrated context involving Ilmara, Corvane and commercial shipping. b. Time
horizons: near, mid, long. c. Scope: the strait, the Southern Passage, Port Auberon approaches;
interdependencies with the energy and humanitarian problem sets. d. Risk owner: the supported
combatant commander. e. Assumptions k0, k3; constraints: the combined patrol with Ilmara continues;
critical dependencies: Dorne-3 range, Varenian mobilization. f. Tolerance: willing to accept
Moderate, trending down risk to the task group in the near term to prevent Significant risk to
freedom of navigation in the mid-term.

**PS2 Energy infrastructure** (`ps_energy`). Ilmaran energy security (Aldis terminal, Veyra
station, grid control) as a partner interest and as the power supply of Port Auberon. Owner: the
supported combatant commander with the country team. Assumptions: k5; dependencies: Serath count,
Veyra status. Tolerance: accept Moderate risk to partner energy supply in the near term; no
tolerance for Significant risk to Blue sustainment.

**PS3 Cyber** (`ps_cyber`). The Blue logistics network and the Ilmaran grid control network.
Owner: the supported combatant commander. Assumptions: k4; dependency: Directorate Nine intent and
capacity. Tolerance: accept Moderate risk to partner networks; Significant risk to Blue
sustainment requires mitigation.

**PS4 Humanitarian** (`ps_humanitarian`). Civilians at Ravel Crossing and the Sondrian camps, and
Blue readiness against diversion to relief. Owner: the supported combatant commander with the
country team. Assumptions: k1; dependencies: displacement, Sondrian alignment. Tolerance: accept
Moderate risk of diversion in the near term to protect civilians.

## 10. Harmful events, sources, drivers, consequence basis

| id | PS | harmful event | type / basis | base P | drivers (kind, locus, condition → Δ) | counterpart |
|---|---|---|---|---|---|---|
| he_01 | PS1 | Varenia closes the Kestrel Strait to Blue and partner shipping | MSR; Ally/Global × Catastrophic → Major | 0.20 | Dorne-3 range ≥ 300 (accessibility, ext, +0.20); mobilized brigades ≥ 2 (response, ext, +0.15); coercive intent (frequency, ext, +0.05); Dorne-3 count ≥ 16 mid/long (accessibility, ext, +0.10) | he_09 (opportunity: combined patrols sustain transits) |
| he_02 | PS1 | Task Group Kestrel suffers losses to Varenian coastal missiles while transiting the strait | MR Operational; Fig. 28 "Achieve Objectives (CCMD Daily Ops)" → Major | 0.15 | range ≥ 300 (accessibility, +0.25); task group posture vulnerable (vulnerability, int, +0.15); Vigil readiness < 0.7 (resilience, int, +0.10); Dorne radar operational (recognition, ext, +0.05) | |
| he_03 | PS2 | Varenia strikes or sabotages the Aldis terminal or the Veyra station | MSR; Partner/Regional × Catastrophic → Major | 0.12 | Serath count ≥ 10 (accessibility, +0.10); coercive intent (+0.08); Veyra degraded (vulnerability, ext, +0.10); Serath count ≥ 20 long (+0.10) | |
| he_04 | PS2 | An extended blackout halts fuel and power to Port Auberon and degrades Blue sustainment | MR Projected Mission; "Resources Meet Required Timelines" → Major | 0.10 | Veyra outage ≥ 48 h (impact, ext, +0.20); grid control unmitigated (vulnerability, ext, +0.10); Aldis degraded (criticality, ext, +0.10) | |
| he_05 | PS3 | Varenia disrupts the Blue logistics network supporting Port Auberon | MR Force Management; "Meet CCDR Requirements (Contingency Sourcing)" → Major | 0.12 | cyber capacity extensive (accessibility, ext, +0.30, dominant); logistics network unmitigated (vulnerability, int, +0.10); Directorate Nine coercive (frequency, +0.05) | |
| he_06 | PS3 | Varenia compromises the Ilmaran grid control network | MSR; Partner/Regional × Considerable → Modest | 0.15 | cyber capacity extensive (+0.20); grid unmitigated (+0.10) | |
| he_07 | PS4 | Mass displacement across Ravel Crossing overwhelms the Sondrian camps | MSR; Other/Local × Catastrophic → Modest | 0.15 | displaced ≥ 20,000 (impact, ext, +0.25); mobilized ≥ 2 (response, +0.10); Sondrian guard degraded (resilience, ext, +0.10) | |
| he_08 | PS4 | Blue forces are diverted to relief operations, degrading readiness for the primary mission | MR Operational; "Achieve Objectives (CCMD Daily Ops)" → Modest | 0.10 | displaced ≥ 20,000 (response, +0.25); Halden Brigade readiness < 0.75 (resilience, int, +0.10) | |
| he_09 | PS1 | Combined patrols with the Ilmaran squadron fail to sustain daily transits (beneficial: they sustain transits ≥ 80) | MR Operational; "Partnerships" → Modest | 0.15 | Ilmaran squadron readiness < 0.7 (resilience, ext, +0.10); squadron operational (resources, ext, −0.05) | key actions: combined patrol rotations and shared maritime surveillance |

Sources of risk: threat = Varenia (7th Coastal Missile Brigade, Northern Fleet, Serath Regiment,
Directorate Nine); hazards = Sondrian camp capacity, Ilmaran grid fragility, Halden Airfield
condition. Posture subjects for the forced-choice rule: Task Group Kestrel and Lantern Battery
(PS1), the Blue logistics network and the cyber protection team (PS3).

## 11. Escalation DAG (6 edges, across problem sets)

he_02 → he_01 (0.5: losses in the strait precede closure); he_01 → he_07 (0.4: closure drives
displacement); he_07 → he_08 (0.6: displacement diverts Blue forces); he_06 → he_03 (0.3: grid
compromise enables sabotage); he_03 → he_04 (0.6: strikes cause blackout); he_05 → he_04 (0.5:
logistics-network disruption degrades sustainment). Acyclic; cascade by noisy-OR.

## 12. PIRs and the T0 collection requirements

PIR 1 strait closure within 30 days; PIR 2 Corvane basing; PIR 3 Dorne-3 reach; PIR 4 Varenian
cyber capacity against sustainment. T0 requirements: req_01 basing access (missing; k2; top
JIPCL), req_02 Dorne-3 range (low confidence; k0), req_03 mobilization time (stale; k1), req_04
cyber capacity (low confidence; k4), req_05 Serath launcher count (low confidence; fallback
priority), req_06 Sondrian alignment (low confidence; fallback). Batch 3 adds req_07
(contradiction on strait throughput).

## 13. Inject design and expected effects

**Batch 1 (day +20)** violates k0: the Dorne-3 range claim becomes 340 km. COA 1's value drops
below its aspiration (0.5) and its acceptable test flips to fail → status invalid; the ranking
becomes COA 2 > COA 3. The same driver claim moves he_01 from Moderate (Unlikely × Major) to
Significant trending up (Likely × Major, with mobilization and the mid-term Dorne-3 projection).
he_02 rises to Significant as well. Assumption k1 moves from stale to violated (observed 21 days).

**Batch 2 (day +45)** answers the top-JIPCL requirement req_01: Corvane grants basing (message
traffic from the country team, reliability B). req_01 → satisfaction; k2 unknown → holds (p = 0.97);
COA 3's value rises; COA 2 remains first among valid COAs.

**Batch 3 (day +70)** introduces a contradiction: a reliability-D news item reports strait
throughput of 60/day against the approved reliability-B claim of 120 (the new claim stays proposed;
req_07 opens with gap type contradiction). The J-2 delivers a roughly even chance estimate that
Varenian cyber capacity is extensive: the dominant driver of he_05 now carries
`roughly_even_chance`, the forced-choice rule fires, the Blue logistics network posture is
unmitigated → Likely, `posture_rationale` populated; he_05 → Significant. Through the cascade edge
he_05 → he_04 the energy problem set moves from Moderate to Significant (a downstream problem set
moved by a cascade edge alone). Displacement 26,000 moves he_07 and he_08.

## 14. Document plan (T0: 50–70 documents) and perturbations

Reference entries (12, one per key entity), situation reports (7), news (8), message traffic (8),
tabular (4), intelligence assessments (4), risk assessments (9, one per harmful event with its
Fig. 11 statement), risk context statements (4), collection plans (4, one per PIR), COA statements
(3) and a COA comparison decision product (1), guidance documents (6). Every fact is assigned to
≥ 1 document; the six assumption-grounding facts to ≥ 2 documents of different types. At least 60%
of T0 documents carry two or more perturbations (paraphrase, unit_drift, stale_echo, implicit,
distractor, alias, typo, hedge_drift); exactly one T0 assessment carries `mixed_scale` as the
style-check negative example; `contradiction` is used only in batch 3.
