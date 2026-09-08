# Doctrine extracts the generator relies on

Verbatim copies (≤ 40 words each) of every scale, template and definition used by the schema,
the generator and the evaluation harness, cited to document, enclosure/chapter, paragraph, figure
and page (document page label, then the PDF page in brackets). `python -m gen.check_extracts`
verifies every quotation against the PDF text layer; extracts transcribed from figure images (which
have no text layer) are marked *(figure image, transcribed)* and were read from the rendered page.

Documents: **[JRAM]** CJCSM 3105.01C, 10 July 2026 · **[JP 5-0]** JP 5-0, Joint Planning, 2020 ·
**[JSPS]** CJCSI 3100.01F, 29 January 2024 · **[JP 2-01]** JP 2-01, 5 January 2012 ·
**[JP 3-60]** JP 3-60, 20 September 2024 · ICD 203 (12 June 2023) is applied as reproduced in [JRAM].

---

## A. Risk: JRAM Enclosure B

### E01 — risk [JRAM] Encl. B §1.a, p. B-1 [11]
> Risk is the probability (likelihood) and consequence (impact) of an event or condition causing harm to a thing that is valued.

Used by: harmful_events, risk_assessments.

### E02 — four baseline levels and trend modifiers [JRAM] Encl. B §1.a, p. B-1 [11]
> The JRAM characterizes risk across four baseline levels—Low, Moderate, Significant, and High—and may further describe them with trend modifiers that reflect expected changes over the near-, mid-, and long-term time horizons used in the JSPS.

Used by: RiskLevel, Trend, TimeHorizon.

### E03 — the five pillars [JRAM] Encl. B §2, p. B-1 [11]
> Context and Scoping → Risk Identification → Risk Analysis → Risk Judgement → Risk Management → Risk Review and Refinement.

Used by: DATA_CARD (pillars 1–2 mechanical, 3–5 human), score_effects (Pillar 5).

### E04 — three time horizons [JRAM] Encl. B §3.a(2), p. B-3 [13]
> The three time horizons from the JSPS continuum—near-term (0–3 years), mid-term (2–7 years), and long-term (5–15 years)—provide the framework for this approach.

Used by: TimeHorizon, games.horizon_map, risk_assessments.jsps_horizon.

### E05 — immediate horizon (expedited process) [JRAM] Encl. B §3.a(1), p. B-3 [13]
> To address urgent contingencies within an “immediate” time horizon (days to months), an expedited risk assessment process should be considered and tailored as appropriate.

Used by: TimeHorizon.immediate.

### E06a — risk context statement, para a [JRAM] Fig. 3, p. B-4 [14]
> a. Strategic Context. This assessment examines [MSR/MR] associated with [describe objectives, interests, missions, or plans], as directed by [NSS/NDS/NMS/DPG/GEF/other].

### E06b — risk context statement, para b [JRAM] Fig. 3, p. B-4 [14]
> b. Time Horizons. Risk will be assessed across the following time horizons, consistent with JSPS usage: – Near-term (0–3 years) – Mid-term (2–7 years) – Long-term (5–15 years)

### E06c — risk context statement, para c [JRAM] Fig. 3, p. B-4 [14]
> c. Scope and Boundaries. This assessment covers [describe activities, missions, plans, capabilities, and forces in scope]. The geographic, functional, and operational scope includes [regions, domains, functions, or specific problem sets].

### E06d — risk context statement, para d [JRAM] Fig. 3, p. B-4 [14]
> d. Roles and Responsibilities. The risk owner for this assessment is [title/ organization], accountable for decisions regarding acceptance, avoidance, mitigation, or transfer of risk.

### E06e — risk context statement, para e [JRAM] Fig. 3, p. B-4 [14]
> e. Assumptions and Constraints. This assessment is based on the following key assumptions: [A1, A2, A3…] and constraints: [B1, B2, B3…]. Critical dependencies that could materially change the risk if altered include [C1, C2, C3…].

### E06f — risk context statement, para f [JRAM] Fig. 3, p. B-4 [14]
> f. Risk tolerance and Expected Outputs. Initial risk tolerance for this problem set is described as [qualitative statement—e.g., “willing to accept moderate, trending down risk to X in the near term to prevent significant risk to Y

Used by: problem_sets (strategic_context, scope_and_boundaries, risk_owner_role, assumptions_and_constraints, tolerance_statement, expected_outputs); style guide jram_risk_context.md.

### E07 — harmful event [JRAM] Encl. B §3.b(1), p. B-5 [15]
> A harmful event is a foreseeable occurrence or condition that, if it happens, will negatively impact what is valued in the risk context statement.

### E08 — threat [JRAM] Encl. B §3.b(2)(a), p. B-5 [15]
> Threat. State or non-state actors that possess the capability and intent or potential intent to harm what is valued, whether through military, informational, economic, cyber, or other means.

### E09 — hazard [JRAM] Encl. B §3.b(2)(b), p. B-5 [15]
> Hazard. Conditions—internal or external to the DoW—that can enable or amplify harm or advantage.

Used by: risk_sources.source_kind.

### E10 — drivers of risk [JRAM] Encl. B §3.b(3), p. B-5 [15]
> Drivers of Risk. Factors that influence the probability or consequence of risks arising from various sources. Drivers can increase or decrease risk by shaping the environment in ways that enable or minimize harmful events.

### E10a — frequency [JRAM] Encl. B §3.b(3)(a), p. B-5 [15]
> Frequency. The number of times a threat or hazard occurs within the situational environment over a given time horizon.

### E10b — vulnerability [JRAM] Encl. B §3.b(3)(b), p. B-5 [15]
> Vulnerability. The susceptibility of an asset, force, or mission to face harm from a threat or hazard (e.g., due to weaknesses in security, design, or resilience characteristics).

### E10c — resilience [JRAM] Encl. B §3.b(3)(c), p. B-5 [15]
> Resilience. The ability to anticipate, withstand, adapt to, and recover from disruption.

### E10d — criticality [JRAM] Encl. B §3.b(3)(d), p. B-6 [16]
> Criticality. The importance of, or degree of dependency on, what is valued.

### E10e — accessibility [JRAM] Encl. B §3.b(3)(e), p. B-6 [16]
> Accessibility. How easily a hostile force or capability can reach what is valued.

### E10f — recognition [JRAM] Encl. B §3.b(3)(f), p. B-6 [16]
> Recognition. How easily what is valued can be identified by a hostile force or capability, including its significance to the Joint Force.

### E10g — impact [JRAM] Encl. B §3.b(3)(g), p. B-6 [16]
> Impact. How severe the damage is, including the secondary and tertiary effects of damage to what is valued.

### E10h — resources [JRAM] Encl. B §3.b(3)(h), p. B-6 [16]
> Resources. People, equipment, funding, locations, or ideas available to respond to a threat or hazard; that is, what the Joint Force will use to mitigate the threat or hazard and reduce risk.

### E10i — response [JRAM] Encl. B §3.b(3)(i), p. B-6 [16]
> Response. The changing demands placed on the Joint Force, which may increase or decrease as situations escalate or de-escalate.

### E10j — reliance [JRAM] Encl. B §3.b(3)(j), p. B-6 [16]
> Reliance. Reliance on commercial capabilities can provide opportunities beyond organic capabilities and is often identified as a risk management measure. However, it may also introduce risk.

Used by: risk_drivers.driver_kind.

### E11 — internal and external drivers [JRAM] Fig. 4, p. B-6 [16] *(figure image, transcribed)*
> Internal Driver Examples (Primarily within DoW Control): Force posture and presence decisions; Readiness levels, training, and modernization choices; Redundancy and resilience of networks, basing, and logistics;

> Talent, manning, and rotation policies; Allocation of resources among campaigns, theaters, and portfolios.

> External Driver Examples (Primarily Outside DoW Control): Adversary capabilities, intent, and risk appetite; Allied and partner capacity, access, and political will; Global economic, technological, environmental, or demographic trends;

> Domestic and international political conditions and legal constraints; Actions by other USG departments and agencies or non-state actors.

Used by: risk_drivers.locus.

### E12 — aggregation [JRAM] Encl. B §3.b(4), p. B-7 [17]
> When appropriate, events and issues can be combined to describe the overall risk to a strategic objective, mission set, or force element. Aggregated risks should retain enough detail to support targeted mitigation efforts and the development of opportunities.

### E13a — aggregated (complex) risk statement, first half [JRAM] Fig. 5, p. B-7 [17]
> If the following related harmful events or conditions occur in combination within [Time Horizon], [Event/Condition 1, Event/Condition 2, Event/Condition 3],

### E13b — aggregated (complex) risk statement, second half [JRAM] Fig. 5, p. B-7 [17]
> then the Joint Force’s ability to [execute mission/maintain posture/etc.] may be [degraded/denied] resulting in [risk] to [thing of value] in the [time horizon].

### E13c — aggregation note [JRAM] Fig. 5, p. B-7 [17]
> The events or conditions aggregated should each be assessed individually before being aggregated into a complex risk.

Used by: problem_set_assessments.aggregated_statement_text; eval/jram.py::render_aggregated_statement.

### E14 — probability [JRAM] Encl. B §3.c(1)(a)1, p. B-7 [17]
> Probability (P) is the assessed likelihood that a harmful event will occur within a specified time horizon under the conditions outlined in the risk context statement.

### E15 — probability levels [JRAM] Fig. 6, p. B-8 [18] *(figure image, transcribed)*
> Probability of Event (P): Very Likely (~81-99%); Likely (~51-80%); Unlikely (~21-50%); Very Unlikely (~01-20%)

Used by: PLevel; eval/jram.py::P_BANDS, p_bin.

### E16 — no zero-probability level [JRAM] Encl. B §3.c(1)(a)2, p. B-8 [18]
> The structure deliberately omits a level for very low, zero, or negligible probability.

Used by: eval/jram.py::clip_p (P_raw clipped to [0.01, 0.99]).

### E17 — consequence levels [JRAM] Fig. 7, p. B-8 [18] *(figure image, transcribed)*
> Consequence of Event (C): Extreme harm to the thing of value; Major harm to the thing of value; Modest harm to the thing of value; Minor harm to the thing of value

Used by: CLevel.

### E18a — baseline risk levels legend [JRAM] Fig. 8, p. B-9 [19] *(figure image, transcribed)*
> HIGH RISK: Maximum level of expected impact on the thing of value. SIGNIFICANT RISK: Severe level of expected impact on the thing of value.

> MODERATE RISK: Medium level of expected impact on the thing of value. LOW RISK: Little or no expected impact on the thing of value.

### E18b — reading the contour [JRAM] Fig. 9 text, p. B-10 [20]
> a harmful event is assessed with a “Very Likely” probability and “Minor” consequence is characterized as a Low or Moderate risk. Separately, a harmful event with “Very Unlikely” probability and “Extreme” consequence is also a Low or Moderate risk.

### E18c — same contour, different cells [JRAM] Encl. B §3.d(1)(a), p. B-12 [22]
> a decision-maker might choose to accept more “Likely (P), Modest (C)” events rather than “Very Unlikely (P), Extreme (C)” events from the same threat, even if both fall within the same Moderate risk contour

### E18d — Fig. 10 worked levels [JRAM] Encl. B §3.c(4)(b), p. B-11 [21]
> In the near-term (0–3 years), there is a Very Likely probability and Extreme consequence to a harmful event occurring.

Used by: eval/jram.py::CONTOUR (team's reading of Fig. 8 constrained by E18b–d and Fig. 11's example: Likely × Major = Significant).

### E19 — trend modifiers [JRAM] Encl. B §3.c(3), p. B-10 [20]
> Risk levels can incorporate a temporal aspect by assigning “trending up” or “trending down” modifiers to the baseline risk level. These modifiers indicate the assessed direction of risk over a specified time horizon if left unmanaged

Used by: Trend; eval/jram.py::trend.

### E20 — risk statement contents [JRAM] Encl. B §3.g(1), pp. B-15–B-16 [25–26]
> A risk statement should clearly express probability, the harmful event, time horizon, key drivers, consequence, overall risk level,

### E21 — risk statement template [JRAM] Fig. 11, p. B-16 [26]
> “There is a [probability level] probability that [harmful event] in the [time horizon], driven primarily by [key drivers] under current [action/inaction/posture/plan] conditions, will result in [consequence level] consequence. This results in [risk level] [risk type] to [thing of value]”.

Used by: risk_assessments.statement_text; eval/jram.py::render_risk_statement, RISK_STATEMENT_RE (invariant 14).

### E22 — opportunity statement template [JRAM] Fig. 12, p. B-17 [27]
> “There is a [probability level] probability that [beneficial event/opportunity] in the [time horizon], if [key actions/conditions] are undertaken, will generate [consequence level – beneficial] improvement in [thing of value]. If not pursued, this creates [risk level] risk to [risk type].”

Used by: eval/jram.py::render_opportunity_statement.

### E23 — senior-leader communication [JRAM] Encl. B §3.g, p. B-15 [25]
> Senior leaders must provide detailed analysis when communicating risk levels such as Significant or High.

Used by: extensions/authority (risk_level_threshold).

### E24 — accumulated risk [JRAM] Encl. B §3.i(7), p. B-20 [30]
> accumulated risk accounts for a macro view of the risk environment, specifically regarding past risk decisions.

### E25a — common numerical basis [JRAM] Encl. B §3.i(9)(b)3, p. B-22 [32]
> Alternative COAs must be compared on a common numerical basis (e.g., expected loss, time, or cost).

### E25b — quantitative outputs inform, not replace [JRAM] Encl. B §3.i(9)(c), p. B-22 [32]
> Quantitative approaches should still account for uncertainty and model limitations, and their outputs are used to inform, not replace, commanders’ judgment in Pillars 2 and 3.

Used by: strategies.value / value_ci presented beside the App. F table (style guide jp50_comparison.md).

### E26a — Pillar 5 review [JRAM] Encl. B §3.f(2)(a), p. B-14 [24]
> Compare expected outcomes (probability, consequence, and trend recorded in Pillar 2) with observed outcomes over the applicable time horizons.

### E26b — over/under-estimation [JRAM] Encl. B §3.f(2)(b), p. B-14 [24]
> Identify instances where risk was overestimated, underestimated, or correctly characterized, and identify what process or logic improvements can be made in conducting future risk assessments.

Used by: eval/score_effects.py (Pillar-5 report).

## B. ICD 203 as reproduced in JRAM Enclosure C §4

### E27 — likelihood and confidence are distinct [JRAM] Encl. C §4.a(1), p. C-4 [36]
> Likelihood (probability) and confidence are distinct and independent elements of uncertainty that should not be placed in the same sentence.

Used by: invariant 12; eval/style_check.py::check_likelihood_confidence.

### E28 — the 7-level scale [JRAM] Encl. C §4.a(1), p. C-4 [36]
> Reference (d) requires analysts to characterize uncertainty associated with probability, utilizing an odd-numbered, 7-level scale that includes a neutral “Roughly Even Chance” (45–55 percent) median.

### E29 — the JRAM 4-level scale [JRAM] Encl. C §4.a(2), p. C-4 [36]
> The JRAM utilizes an even-numbered, 4-level scale (Very Unlikely, Unlikely, Likely, Very Likely) to promote a directional judgement on whether mission harm will occur, driving commander risk-mitigation decisions.

### E30 — Intelligence-to-Risk Translation Crosswalk [JRAM] Fig. 19, p. C-4 [36] *(figure image, transcribed)*
> Crosswalk – Common IC Probability Expressions to JRAM Probability Scale. Intelligence Community Directive (ICD) 203 | JRAM Risk Plot

| ICD 203 expression (band) | JRAM risk plot |
|---|---|
| Almost certain(ly) / Nearly certain (95-99%) | Very Likely (~81-99%) |
| Very likely / Highly probable (80-95%) | Very Likely (~81-99%) |
| Likely / Probable (probably) (55-80%) | Likely (~51-80%) |
| Roughly even chance / Roughly even odds (45-55%) | See Execution Paragraph (Boundary Flag) |
| Unlikely / Improbable (improbably) (20-45%) | Unlikely (~21-50%) |
| Very unlikely / Highly improbable (05-20%) | Very Unlikely (~01-20%) |
| Almost no chance / Remote (01-05%) | Very Unlikely (~01-20%) |

Used by: LikelihoodICD203, ICD203_BANDS, ICD203_TERMS; eval/jram.py::ICD_TO_JRAM, crosswalk.

### E31a — high confidence [JRAM] Encl. C §4.c(1), p. C-5 [37]
> High Confidence. Well-corroborated information from independent, proven sources; minimal contradictory reporting; low potential for deception; few information gaps.

### E31b — moderate confidence [JRAM] Encl. C §4.c(2), p. C-5 [37]
> Moderate Confidence. Partially corroborated information from good sources; some potential for deception; several gaps. An assumption that changes the assessment if incorrect.

### E31c — low confidence [JRAM] Encl. C §4.c(3), p. C-5 [37]
> Low Confidence. Uncorroborated information or low-confidence database records; high potential for deception; many critical gaps. More than one linchpin assumption with substantial effect on the assessment if incorrect.

Used by: ConfidenceICD203; claims.confidence_icd203; assumption status `stale` on low confidence.

### E32a — no neutral plot [JRAM] Encl. C §4.d, p. C-5 [37]
> A fundamental principle of the JRAM is the prevention of neutrality when appraising risk. Therefore, an intelligence assessment of a “Roughly Even Chance” (45–55 percent) cannot be plotted as a neutral baseline.

### E32b — forced choice: Likely [JRAM] Encl. C §4.d(2)(a), p. C-5 [37]
> Likely. If friendly forces are highly vulnerable, out of position, or lack rehearsed mitigations, the probability of the threat causing mission harm is assessed as Likely.

### E32c — forced choice: Unlikely [JRAM] Encl. C §4.d(2)(b), p. C-5 [37]
> Unlikely. If friendly forces are hardened, postured to react, or possess strong existing mitigations, the probability of the threat causing mission harm is assessed as Unlikely.

### E32d — documentation of posture factors [JRAM] Encl. C §4.e, p. C-5 [37]
> the staffs should document the specific friendly posture factors (vulnerabilities or mitigations) that drove the directional shift.

Used by: PostureState; risk_assessments.posture_rationale (invariant 19); eval/jram.py::forced_choice.

## C. Risk types and consequence matrices: JRAM Enclosure C §5–6

### E33 — Significant or higher requires a mitigation plan [JRAM] Encl. C §5.b, p. C-6 [38]
> if the CJCS characterizes a baseline risk as Significant or higher, SecWar is required to submit to Congress a plan for mitigating those risks.

Used by: extensions/authority.

### E34 — Military Strategic Risk [JRAM] Encl. C §6.b(1), p. C-8 [40]
> MSR is defined as the probability and consequence of events, with direct military linkages, causing harm to U.S. national interests as defined in national strategic guidance.

### E35 — MSR probability and consequence levels [JRAM] Fig. 21, p. C-8 [40] *(figure image, transcribed)*
> Consequence of Event (C) to US National Interests: Extreme: Existential/Permanent damage; Major: Catastrophic damage; Modest: Considerable damage; Minor: Confined damage

### E36 — strategic value and degrees of damage [JRAM] Encl. C §6.b(1)(b) and Fig. 22, p. C-9 [41]
> Thus, strategic value becomes part of determining whether a consequence is assessed as Minor, Modest, Major, or Extreme.

> Harmful Event: Varying Degrees of Damage Based on inherent damage to interest, time, and resiliency National Interest “Risk to What?” Confined Near-term Considerable Mid-term Catastrophic Long-term Existential Permanent

Used by: DamageDegree.

### E37 — MSR consequence assessment matrix [JRAM] Fig. 23, p. C-10 [42] *(figure image, transcribed)*
> Strategic Value of Interest (Scale / Scope) × Harmful Event: Varying Degrees of Damage (Confined, Considerable, Catastrophic, Existential): Homeland / Vital: Modest, Major, Extreme, Extreme. Ally / Global: Modest, Major, Major, Extreme.

> Partner / Regional: Minor, Modest, Major, Major. Other / Local: Minor, Minor, Modest, Modest.

Used by: StrategicValue; eval/jram.py::FIG23, msr_consequence.

### E38a — Military Risk [JRAM] Encl. C §6.b(2), p. C-10 [42]
> MR is defined as the probability and consequence of events causing harm to the Joint Force’s ability to execute assigned objectives.

### E38b — Risk-to-Mission [JRAM] Encl. C §6.b(2)(a), p. C-10 [42]
> RM is the probability and consequence of planned and contingency events causing harm to current or future military objectives.

### E38c — Risk-to-Force [JRAM] Encl. C §6.b(2)(b), p. C-11 [43]
> RF is the probability and consequence of planned and contingency events causing harm to the provisions and sustainment of sufficient military resources.

### E39 — Operational Risk [JRAM] Encl. C §6.b(2)(a)1, p. C-10 [42]
> Operational Risk. The probability and consequence of failure to achieve mission objectives while protecting the force from unacceptable losses. This risk subset considers the ability to execute current, planned, and contingency operations in the near-term time horizon.

### E40 — Projected Mission Risk [JRAM] Encl. C §6.b(2)(a)2, p. C-11 [43]
> Projected Mission Risk. The probability and consequence of an anticipated event that may cause failure to meet projected operational mission requirements.

### E41 — Force Management Risk [JRAM] Encl. C §6.b(2)(b)1, p. C-11 [43]
> Force Management Risk is the probability and consequence of not maintaining the appropriate force size and structure (“breaking the force”), CCMD mission load and battlespace, force distribution among CCMDs, and global force disposition.

### E42 — Institutional Risk [JRAM] Encl. C §6.b(2)(b)2(a), p. C-12 [44]
> Institutional Risk is the probability and consequence of the DoW failing to perform established functions.

Used by: RiskType, RiskSubset.

### E43 — MR probability and consequence levels [JRAM] Fig. 26, p. C-12 [44] *(figure image, transcribed)*
> Consequence of Event (C) to NMS. Extreme: RM, Mission Failure, Objectives Unachievable; RF, No Sourcing Solutions Exist for Critical Requirements. Major: RM, Objectives Minimally Achieved (consider time, priority); RF, Shortfalls Exist for Critical Requirements.

> Modest: RM, Objectives Mostly Achieved (consider time, priority); RF, Worldwide Sourcing Solution Exist for Most Requirements. Minor: RM, Mission Success, Objectives Achievable; RF, Joint Force Fully Sustained and Requirements Sourced.

Used by: eval/jram.py::FIG26.

### E44 — subsets over time horizons [JRAM] Fig. 27, p. C-13 [45] *(figure image, transcribed)*
> Risk-to-Mission: Operational Risk (0–2 years); Projected Mission Risk (2–15 years). Risk-to-Force: Institutional Risk (0–15 years); Force Management Risk (0–7 years). Future Military Risk spans Projected Mission Risk and Institutional Risk.

### E45a — Fig. 28 usage [JRAM] Encl. C §6.b(4), p. C-13 [45]
> In Figure 28, each row presents a risk subset or thing of value for consideration, with graduated consequences toward success or failure.

### E45b — judgment on the overall level [JRAM] Encl. C §6.b(4), p. C-13 [45]
> After considering each applicable driver and assigning an expected result within the matrix, the assessor must use judgment to determine the overall expected consequence level for a situation.

### E45c — Fig. 28 rows [JRAM] Fig. 28, p. C-14 [46] *(figure image, transcribed)*
> Risks to What: Achieve Objectives (CCMD Daily Ops); Meet CCDR Requirements (CCMD Daily Ops); Achieve Plan Objectives; Meet CCDR Requirements (Contingency Sourcing); Authorities; Resources Meet Required Timelines; Partnerships; Messaging; Capability: DOTMLPF-P vs Threat; Readiness (DRRS);

> Stress on AC Force (D2D); Stress on RC Force (M2D); Stress on AC Mobility Force (T2D); Stress on RC Mobility Air Force (T2D); Modernization / Critical Maintenance; Programmatic; Force Development & Design Defense Industrial Base; Operational Imperatives & CRCs.

Used by: harmful_events.fig28_row / fig28_cell; eval/jram.py::FIG28 (full cell text transcribed there).

### E46a — risk level (glossary) [JRAM] Glossary Part II, p. GL-5 [59]
> Risk Level. A function of probability and consequence classified as Low, Moderate, Significant, or High.

### E46b — risk statement (glossary) [JRAM] Glossary Part II, p. GL-5 [59]
> Risk Statement. A statement that clearly expresses probability, the harmful event, time horizon, key drivers, consequence, overall risk level and trend.

### E46c — sources of risk (glossary) [JRAM] Glossary Part II, p. GL-6 [60]
> sources of risk. Threats or hazards which, alone or combined, have potential to cause harm to the thing that is valued.

## D. Strategy as a JP 5-0 course of action

### J01 — assumption [JP 5-0] Glossary, p. GL-5 [347]
> assumption. A specific supposition of the operational environment that is assumed to be true, in the absence of positive proof, essential for the continuation of planning.

### J02 — logical, realistic, essential [JP 5-0] Ch. III §(6)(b), p. III-17 [95]
> Valid assumptions have three characteristics: logical, realistic, and essential for planning to continue. Commanders and staffs should never assume away adversary capabilities or assume unrealistic friendly capabilities will be available.

Used by: assumptions.jp50_logical / jp50_realistic / jp50_essential.

### J03 — validate or invalidate [JP 5-0] Ch. III §(6)(b)1, p. III-17 [95]
> planners must either validate the assumptions (treat as facts) or invalidate the assumptions (alter the plan accordingly) as quickly as possible.

Used by: AssumptionStatus.

### J04 — decision matrix [JP 5-0] Ch. III §(6)(b)7, p. III-18 [96]
> All assumptions should be identified in the plan or decision matrix to ensure they are reviewed and validated prior to execution.

Used by: assumptions.in_decision_matrix (invariant 15).

### J05a — higher headquarters assumptions [JP 5-0] Ch. III §(6)(a), p. III-17 [95]
> Planners must acknowledge higher headquarters assumptions and assess the impact (risk) should they prove to be incorrect.

### J05b — followed in framing, validated for execution [JP 5-0] Ch. III §(6)(b)3, p. III-17 [95]
> Although higher headquarters assumptions are followed in framing planning, they are treated as assumptions and validated for execution.

Used by: assumptions.origin; assumptions.sensitivity ("assess the impact (risk)").

### J06 — assumptions become information requirements [JP 5-0] Ch. III §(6)(b)5, p. III-18 [96]
> The staff accomplishes this by identifying the information needed to validate assumptions and submitting an information request to an appropriate agency as an information requirement.

Used by: collection_requirements.assumption_id.

### J07a — constraint [JP 5-0] Ch. III §(7)(a), p. III-18 [96]
> A constraint is a requirement placed on the command by a higher command that dictates an action (“must do”), thus restricting freedom of action.

### J07b — restraint [JP 5-0] Ch. III §(7)(b), p. III-18 [96]
> A restraint is a requirement placed on the command by a higher command that prohibits an action (“cannot do”), thus restricting freedom of action.

Used by: strategies.constraints / restraints.

### J08 — mission statement [JP 5-0] Ch. III §(9), p. III-20 [98]
> The mission statement describes the mission in terms of the elements of who, what, when, where, and why.

Used by: strategies.mission_who … mission_why.

### J09 — military objectives [JP 5-0] Ch. III §(11)(a)–(b), p. III-22 [100]
> Military objectives are clearly defined, decisive, and attainable goals toward which a military operation is directed.

> Military objectives are written as short phrases in active voice.

Used by: objectives.statement.

### J10a — evaluation criteria [JP 5-0] Ch. III §(12), p. III-22 [100]
> Evaluation criteria are standards the commander and staff will later use to measure the relative effectiveness and efficiency of one COA relative to other COAs.

### J10b — potential evaluation criteria [JP 5-0] Fig. III-7, p. III-23 [101]
> Casualties Risk Force Protection Decisive Action Defeats Enemy Center of Gravity Surprise

Used by: strategy_objectives.weight (weights = evaluation criteria weights).

### J11 — risk assessment in planning [JP 5-0] Ch. III §(13)(a), p. III-24 [102]
> Based on judgment, military risk assessment is an integration of probability and consequence of an identified impediment.

Note: JP 5-0 Fig. III-8 uses "very likely / probable / improbable / highly unlikely"; the JRAM (2026) scale in E15 governs this dataset (conflict logged in PROGRESS.md).

### J12 — a COA [JP 5-0] Ch. III §d(1)(a), p. III-32 [110]
> A COA is a potential way (solution, method) to accomplish the assigned mission. Staffs develop multiple COAs to provide commanders with options to attain the military end state.

> All COAs must be suitable, feasible, acceptable, distinguishable, and complete.

### J13a — suitable [JP 5-0] Ch. III §(q)1, p. III-41 [119]
> Suitable—Can accomplish the mission within the commander's guidance.

### J13b — feasible [JP 5-0] Ch. III §(q)2, p. III-41 [119]
> Feasible—Can accomplish the mission within the established time, space, and resource limitations.

> Does the commander have the force structure, posture, transportation, and logistics (e.g., munitions) (means) to execute it?

### J13c — acceptable [JP 5-0] Ch. III §(q)3, p. III-41 [119]
> Acceptable—Must balance cost and risk with the advantage gained.

> A COA is considered acceptable if the estimated results justify the risks.

### J13d — distinguishable [JP 5-0] Ch. III §(q)4, p. III-42 [120]
> Distinguishable—Must be sufficiently different from other COAs in the following:

> a. The focus or direction of main effort.

> c. Sequential versus simultaneous maneuvers.

> d. The primary mechanism for mission accomplishment.

> e. Task organization(s).

> f. The use of reserves.

### J13e — complete [JP 5-0] Ch. III §(q)5, p. III-42 [120]
> Complete—Does it answer the questions who, what, where, when, how, and why?

Used by: ValidityTest, DistinguishDim; eval/validity.py; strategies.validity, status.

### J14a — weighted numerical comparison [JP 5-0] App. F §1, p. F-1 [279]
> The most common technique for COA comparison is the weighted numerical comparison, which uses evaluation criteria to determine the preferred COA, based upon the wargame.

### J14b — caution [JP 5-0] App. F §2.b, p. F-1 [279]
> The staff member must not portray this simplified numeric method as the result of a rigorous mathematical analysis. Comparing COAs by criterion is more accurate than comparing total values.

### J14c — scoring [JP 5-0] App. F §2.b, p. F-1 [279]
> Multiplying the score by the weight yields the criterion's value.

> The highest number is best.

Used by: strategy_objectives.rating_1_to_3; style guide jp50_comparison.md (invariant 17).

### J15 — military end state [JP 5-0] Ch. IV §b(1), p. IV-21 [177]
> A military end state is the set of required conditions that defines achievement of all military objectives.

Used by: ObjectiveKind.end_state; strategies.end_state_objective_id.

### J16a — effects [JP 5-0] Ch. IV §d, p. IV-27 [183]
> An effect is a physical and/or behavioral state of a system that results from an action, a set of actions, or another effect. A desired effect can be thought of as a condition that can support achieving an associated objective

### J16b — writing effects [JP 5-0] Ch. IV §d(2)(a)–(b), p. IV-28 [184]
> Each desired effect should link directly to one or more objectives.

> The effect should be measurable.

Used by: ObjectiveKind.effect; theory-of-victory chain (action → claim → effect → objective → end state).

### J17 — end state, objectives, effects, tasks [JP 5-0] Fig. IV-9, p. IV-27 [183]
> End state describes the set of conditions to meet conflict termination criteria.

> Tasks describe friendly actions to create desired effects or preclude undesired effects.

Levels shown: National strategic, Theater strategic, Operational, Tactical. Used by: Echelon.

### J18a — line of effort [JP 5-0] Glossary, p. GL-11 [353]
> line of effort. In the context of planning, using the purpose (cause and effect) to focus efforts toward establishing operational and strategic conditions by linking multiple tasks and missions.

### J18b — line of operation [JP 5-0] Glossary, p. GL-11 [353]
> line of operation. A line that defines the interior or exterior orientation of the force in relation to the enemy or that connects actions on nodes and/or decisive points related in time and space to an objective(s).

Used by: actions.line_of_effort; strategies.main_effort.

### J19a — decision point [JP 5-0] Glossary, p. GL-7 [349]
> decision point. A point in space and the latest time when the commander or staff anticipates making a key decision concerning a specific course of action.

### J19b — decision matrix and collection [JP 5-0] Ch. IV §g(1), p. IV-16 [172]
> The decision matrix also identifies the expected indicators needed in support of operation assessment and intelligence requirements and collection plans.

### J19c — decision points and PIRs [JP 5-0] Ch. IV §(b)3, p. IV-39 [195]
> a DSM to link those decision points with the earliest and latest timing of the decision, the appropriate PIR (things the commander must know about the adversary, enemy, and the OE to make the decision)

Used by: decision_points (condition, branch_rule_ids, pir_id, latest_period).

### J20a — branch [JP 5-0] Glossary, p. GL-5 [347]
> The contingency options built into the base plan used for changing the mission, orientation, or direction of movement of a force to aid success

### J20b — sequel [JP 5-0] Glossary, p. GL-12 [354]
> sequel. The subsequent operation or phase based on the possible outcomes of the current operation or phase.

### J21 — operational approach [JP 5-0] Glossary, p. GL-11 [353]
> operational approach. A broad description of the mission, operational concepts, tasks, and actions required to accomplish the mission.

### J22 — enemy most likely / most dangerous COA [JP 5-0] Ch. III §(2)(a), p. III-32 [110]
> The inputs to COA development include the staff estimates (to include assessed most likely/most dangerous enemy COAs), mission statement, refined operational approach, and CCIRs.

Used by: AdversaryCoaLabel; opponent_models.

### J23 — course of action (glossary) [JP 5-0] Glossary, p. GL-7 [349]
> course of action. 1. Any sequence of activities that an individual or unit may follow. 2. A scheme developed to accomplish a mission. Also called COA.

## E. JSPS nesting: CJCSI 3100.01F

### S01 — the JSPS [JSPS] Encl. A §3.a, p. A-1 [11]
> The JSPS is the primary method by which CJCS fulfills title 10, U.S. Code responsibilities: providing strategic direction for the Armed Forces, preparing strategic and contingency plans, advising on global military integration;

### S02 — nested strategic documents [JSPS] Encl. A §5.b, p. A-7 [17]
> The top of the triangle in Figure 2 depicts the nested national strategic documents, including the National Security Strategy (NSS), NDS and NMS. The NMS is CJCS’s framework for plans, force employment, development, and design.

### S03a — planning ecosystem and OAIs [JSPS] Encl. A §5.e(1), p. A-7 [17]
> The planning ecosystem provides strategic guidance that the CCMDs and Services turn into OAIs. The direction from plans are implemented as tangible globally integrated OAIs.

### S03b — OAIs [JSPS] Encl. A §5.e(1)(a), p. A-7 [17]
> OAIs are the specifics actions within campaigning to deter and build warfighting advantage.

### S04 — assessments ecosystem [JSPS] Encl. A §5.e(2), p. A-7 [17]
> Assessments offer feedback to calibrate force management or planning supporting the objectives.

### S05a — presidential guidance [JSPS] Encl. C §1.a, p. C-1 [25]
> Three presidential guidance documents provide direction to the DoD. These are the NSS, UCP, and Contingency Planning Guidance (CPG).

### S05b — SecDef guidance [JSPS] Encl. C §1.b, p. C-1 [25]
> The SecDef provides strategic direction to the DoD and the Joint Force primarily through the NDS, Guidance for the Employment of the Force (GEF), Defense Planning Guidance (DPG), and GFMIG.

### S06a — the NMS [JSPS] Encl. C §2.b, p. C-1 [25]
> The NMS is CJCS’s central strategy document. It translates policy guidance into Joint Force action

### S06b — NMS objectives as the lens for risk [JSPS] Encl. C §2.e, p. C-2 [26]
> The NMS strategic objectives provide the lens for evaluating risk and accomplishing assessments while implementing integrated deterrence.

### S07a — the JSCP [JSPS] Encl. D §3.a, p. D-2 [30]
> The JSCP is a five-year global strategic campaign plan (reviewed every two years) signed by the CJCS.

### S07b — JSCP operationalizes the NMS [JSPS] Encl. D §3.b, p. D-2 [30]
> The JSCP operationalizes the NMS and implements strategic planning guidance from the NDS, GEF, and CPG.

### S07c — three types of campaign plans [JSPS] Encl. D §3.c(1), p. D-2 [30]
> The JSCP directs the development of three types of campaign plans: GCP, Functional Campaign Plans (FCPs), and Combatant Command Campaign Plans (CCPs).

### S08 — GCPs [JSPS] Encl. D §4.a–b, p. D-2 [30]
> GCPs focus on integrating activities oriented against DoD’s most pressing trans-regional, all-domain, multi-functional strategic challenges.

> The SecDef is the GCP approval authority.

### S09 — CCPs [JSPS] Encl. D §6, p. D-3 [31]
> CCPs are the primary plans through which the CCMDs execute day-to-day campaigning to operationalize strategic guidance.

Used by: GuidanceProductType, guidance.parent_guidance_id (NSS → NDS → NMS → JSCP → GCP/CCP → plan), guidance.issuing_role, strategies.guidance_source.

### S10 — plan review purposes [JSPS] Encl. D §10, p. D-5 [33]
> The plans review process has four purposes: ensuring plans are feasible; enabling CJCS to provide informed military advice based on current plans; integrating the SecDef’s guidance with plans; and facilitating cross-domain and globally integrated planning.

### S11a — the CRA [JSPS] Encl. H §3.a, p. H-2 [58]
> It directs CJCS to prepare an assessment of military strategic risks to U.S. interests and military risks in executing the NMS (i.e., risks to the NMS mission areas).

### S11b — mitigation plan for significant risk [JSPS] Encl. H §3.b, p. H-2 [58]
> to include a risk mitigation plan for all areas of significant risk, or higher, associated with the NMS and for deficiencies identified in force capabilities for contingency plans.

### S12 — time horizons endure for risk [JSPS] Encl. A fn. 4, p. A-4 [14]
> Time horizons—near term (0–3 years); mid-term (2–7 years); and long-term (5–15 years)—endure when framing and reporting risk assessments.

### S13 — SPFs and assumptions [JSPS] Encl. D §9.a, p. D-4 [32]
> SPFs also enable senior leaders to provide guidance on assumptions, risks, priorities, and resourcing earlier in the plan development process.

Used by: assumptions.origin = higher_hq.

## F. Collection management: JP 2-01

### I01a — CCIRs [JP 2-01] Ch. III §5.a, p. III-4 [67]
> CCIRs consist of either PIRs or friendly force information requirements (FFIRs).

### I01b — PIRs and EEIs [JP 2-01] Ch. III §5.a, p. III-4 [67]
> IRs deemed most important to mission accomplishment are identified by the commander as PIRs. Information requirements that are most critical or that would answer PIRs are known as EEIs.

### I02a — intelligence requirement [JP 2-01] Fig. III-3, p. III-6 [69]
> Any subject, general or specific, upon which there is a need for the collection of information or the production of intelligence.

### I02b — information requirement [JP 2-01] Fig. III-3, p. III-6 [69]
> In intelligence usage, those items of information regarding the adversary and other relevant aspects of the operational environment that need to be collected and processed in order to meet the intelligence requirements of a commander.

### I03 — RFI to collection requirement [JP 2-01] Ch. III §5.c, p. III-7 [70]
> If it is determined that insufficient information exists to answer an RFI, then a collection requirement is prepared and entered into the appropriate CRM application.

### I04 — CRM and COM [JP 2-01] Ch. III §12, p. III-16 [79]
> Collection management has two distinct functions: CRM—defining what intelligence systems must collect—and collection operations management (COM)—specifying how to satisfy the requirement.

### I05 — tracking states [JP 2-01] Ch. III §13.a, p. III-19 [82]
> The CCMD JIOC tracks the status of research, validation, submission, and satisfaction of all collection requests received.

Used by: ReqStatus (research, validation, submission, satisfaction; `closed` is a dataset addition).

### I06 — JCMB and the JIPCL [JP 2-01] Ch. III §13.a, p. III-19 [82]
> the JCMB receives collection target nominations from the components and the JFC’s staff, validates and prioritizes these requirements into a joint integrated prioritized collection list (JIPCL), and recommends the employment of ISR assets to meet JIPCL requirements.

Used by: collection_requirements.routing, jipcl_rank.

### I07a — PIR → EEI [JP 2-01] Ch. III §13.b(1), p. III-19 [82]
> CRM begins with an understanding of the commander’s PIRs to provide context to the overall intelligence problem. Based on the PIRs, the intelligence staff (usually the intelligence planner and the analyst) develops more specific questions known as EEIs.

### I07b — RFI as a holdings query [JP 2-01] Ch. III §13.b(1), p. III-19 [82]
> In the context of collection management, RFIs are queries to see if the information already exists and, if not, they form the basis of a collection requirement.

### I07c — information gap [JP 2-01] Ch. III §13.b(1), p. III-19 [82]
> When the RFI manager positively determines that the information is neither available nor extractable from archived information or from lateral or higher echelons, an information gap is identified.

Used by: pirs; collection_requirements.eei, rfi_disposition, gap_type.

### I08 — collection plan contents [JP 2-01] Ch. III §13.b(2), p. III-19 [82]
> The collection plan includes PIRs, their associated EEIs and related indicators, specific information requirements, collection assets to be tasked or additional collection resources to be requested, when the information report is needed, and who is to receive it.

### I09 — sample collection plan format [JP 2-01] Fig. III-8, p. III-20 [83]
> Period Covered: From__________ To_________

> Priority or Other Intelligence Requirements Indications Specific Information Sought Assets to Be Tasked/ Resources to Be Required Place and Time to Report Remarks

Used by: style guide jp201_collection_plan.md (doctrine's column headers govern; conflict with the prompt's list logged in PROGRESS.md).

### I10 — the JIPCL as a registry [JP 2-01] Ch. III §13.b(3), p. III-20 [83]
> create, continuously update, and monitor a registry of active, prioritized requirements, such as a JIPCL.

### I11a — key elements [JP 2-01] Ch. III §13.c(1), p. III-20 [83]
> The key elements commonly considered are target characteristics, range to the target, and timeliness.

### I11b — LTIOV [JP 2-01] Ch. III §13.c(1)(c), p. III-22 [85]
> Timeliness is when the information requested must be received in order to be of value (latest time information is of value [LTIOV]).

Used by: collection_requirements.ltiov; extensions/collection_assets (target_characteristics_match, range_ok, timeliness_ok).

### I12 — prioritization [JP 2-01] Ch. III §11.b(2), p. III-15 [78]
> Prioritization assigns a distinct ranking to each collection requirement. Collection decisions can be made rationally only if requirements are prioritized and the resulting trade-offs are fully understood.

### I13 — theater J-2 validation authority [JP 2-01] Ch. III §12.e, p. III-18 [81]
> The theater J-2 retains full management authority (i.e., to validate, to modify, or to nonconcur) over all intelligence collection requirements within the AOR.

> Collection requirements should be satisfied at the lowest possible level.

### I14 — disciplines and what they capture [JP 2-01] Ch. III §11.b(3), p. III-16 [79] and §13.c(1)(a), p. III-21 [84]
> HUMINT and/or SIGINT can capture adversary intent but GEOINT cannot

> Observables are associated with GEOINT and HUMINT/CI, collectibles with SIGINT, and both are associated with MASINT.

Used by: Discipline (extension collection_assets).

### I15 — PIR (glossary) [JP 2-01] Glossary Part II [268]
> priority intelligence requirement. An intelligence requirement, stated as a priority for intelligence support, that the commander and staff need to understand the adversary or other aspects of the operational environment.

## G. Target systems: JP 3-60

### T01 — target [JP 3-60] Glossary, p. GL-6 [134]
> target. An entity that performs a function for the adversary or enemy considered for possible engagement.

### T02 — target system [JP 3-60] Glossary, p. GL-8 [136]
> target system. All the targets situated in a particular geographic area and functionally related or a group of targets that are so related that their destruction will produce some particular effect desired by the attacker.

### T03 — target system component [JP 3-60] Glossary, p. GL-8 [136]
> target system component. A related group of entities within a target system that performs or contributes toward a similar function.

### T04 — target system analysis [JP 3-60] Glossary, p. GL-8 [136]
> target system analysis. An all-source examination of potential target systems to determine relevance to stated objectives, military importance, and priority of attack.

### T05 — target component [JP 3-60] Glossary, p. GL-7 [135]
> target component. A set of targets within a target system performing a similar function.

### T06 — five characteristic categories [JP 3-60] Ch. I §8, p. I-13 [29]
> Broad categories that help define the characteristics of a target are physical; functional; cognitive, control, and informational; environmental; and temporal. Not all targets have every one of these characteristics.

### T06a — physical [JP 3-60] Ch. I §8.a, p. I-13 [29]
> The characteristics or features that describe a target are generally discernible to one or more of the five senses or through sensor-derived signatures.

### T06b — functional [JP 3-60] Ch. I §8.b and §8.b(2), p. I-14 [30]
> These characteristics describe what the target does and how it does it.

> Target status (state or condition [e.g., fully operational, degraded, or inoperative]).

### T06c — cognitive, control, and informational [JP 3-60] Ch. I §8.c, p. I-15 [31]
> These characteristics describe where and how individuals, groups, or automated systems process, perceive, judge, and make decisions.

### T06d — environmental [JP 3-60] Ch. I §8.d, p. I-16 [32]
> The following characteristics describe the effect of the OE on the target and may also help determine the methods necessary to affect or observe them:

### T06e — temporal [JP 3-60] Ch. I §8.e, p. I-16 [32]
> Time, as a characteristic of a target, describes the target’s vulnerability to detection, engagement, or attack in relation to a time horizon.

Used by: TargetCharacteristicType; Predicate.status values; extensions/target_systems.

### T07 — effect (targeting) [JP 3-60] Ch. I §5.a, p. I-9 [25]
> An effect is a change in the physical or behavioral state of a target element, target entity, target system component, or target system that results from an action, a set of actions, or another effect.

### T08 — targets link to objectives [JP 3-60] Ch. I §1.b, p. I-1 [17]
> Targets are logically and causally linked to objectives, effects, and tasks at all levels of warfare—strategic, operational, and tactical.

Used by: extensions/target_systems (criticality as a computable proxy for TSA judgment).
