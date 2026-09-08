"""JRAM (CJCSM 3105.01C) made computable. Pure functions.

Scales reproduced exactly from the manual: Fig. 6 probability levels, Fig. 7 consequence levels,
Fig. 19 ICD 203 -> JRAM crosswalk, Fig. 23 MSR consequence matrix, Fig. 26 MR consequence
descriptions, Fig. 28 MR consequence assessment matrix rows/cells, Fig. 11/12/5 templates, Encl. C
§4.d forced-choice rule. The risk contour (Fig. 8) is a drawn figure; CONTOUR below is the team's
reading of it, with the four cells that lie close to a dashed boundary listed in
CONTOUR_BOUNDARY_CELLS. Noisy-OR cascade and least-squares trend are the team's computable
extensions (doctrine does not prescribe them) — see DATA_CARD.md Fidelity statement.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

P_LEVELS = ["very_unlikely", "unlikely", "likely", "very_likely"]
C_LEVELS = ["minor", "modest", "major", "extreme"]
RISK_LEVELS = ["low", "moderate", "significant", "high"]

P_LABEL = {"very_unlikely": "Very Unlikely", "unlikely": "Unlikely", "likely": "Likely", "very_likely": "Very Likely"}
C_LABEL = {"minor": "Minor", "modest": "Modest", "major": "Major", "extreme": "Extreme"}
RISK_LABEL = {"low": "Low", "moderate": "Moderate", "significant": "Significant", "high": "High"}
HORIZON_LABEL = {
    "immediate": "immediate (days to months)",
    "near": "near-term (0-3 years)",
    "mid": "mid-term (2-7 years)",
    "long": "long-term (5-15 years)",
}
HORIZON_MIDPOINT_YEARS = {"near": 1.5, "mid": 4.5, "long": 10.0}

# Fig. 6 probability bands (upper bound inclusive): Very Unlikely ~01-20%, Unlikely ~21-50%,
# Likely ~51-80%, Very Likely ~81-99%.
P_BANDS = [("very_unlikely", 0.20), ("unlikely", 0.50), ("likely", 0.80), ("very_likely", 1.0)]

# Fig. 19 crosswalk. roughly_even_chance -> None = boundary flag (Encl. C §4.d forced choice).
ICD_TO_JRAM: dict[str, Optional[str]] = {
    "almost_certain": "very_likely",
    "very_likely": "very_likely",
    "likely": "likely",
    "roughly_even_chance": None,
    "unlikely": "unlikely",
    "very_unlikely": "very_unlikely",
    "almost_no_chance": "very_unlikely",
}

# Encl. C §4.d(2): posture factors that force Likely vs Unlikely.
POSTURE_LIKELY = {"vulnerable": "highly vulnerable", "out_of_position": "out of position", "unmitigated": "lacks rehearsed mitigations"}
POSTURE_UNLIKELY = {"hardened": "hardened", "postured_to_react": "postured to react", "mitigated": "possesses strong existing mitigations"}

# Fig. 8 risk contour, team's reading (rows = consequence, cols = probability VU, U, L, VL).
CONTOUR: dict[str, dict[str, str]] = {
    "minor":   {"very_unlikely": "low",      "unlikely": "low",      "likely": "moderate",    "very_likely": "moderate"},
    "modest":  {"very_unlikely": "low",      "unlikely": "moderate", "likely": "moderate",    "very_likely": "moderate"},
    "major":   {"very_unlikely": "moderate", "unlikely": "moderate", "likely": "significant", "very_likely": "significant"},
    "extreme": {"very_unlikely": "moderate", "unlikely": "moderate", "likely": "significant", "very_likely": "high"},
}
# Cells whose centre lies within ~5% of a dashed boundary in Fig. 8 (alternative reading in value).
CONTOUR_BOUNDARY_CELLS: dict[tuple[str, str], str] = {
    ("modest", "unlikely"): "low",
    ("major", "very_unlikely"): "low",
    ("modest", "very_likely"): "significant",
    ("major", "very_likely"): "high",
}

# Fig. 23 MSR consequence: strategic value (rows) x degree of damage (cols).
FIG23: dict[str, dict[str, str]] = {
    "homeland_vital":   {"confined": "modest", "considerable": "major", "catastrophic": "extreme", "existential": "extreme"},
    "ally_global":      {"confined": "modest", "considerable": "major", "catastrophic": "major",   "existential": "extreme"},
    "partner_regional": {"confined": "minor",  "considerable": "modest", "catastrophic": "major",  "existential": "major"},
    "other_local":      {"confined": "minor",  "considerable": "minor",  "catastrophic": "modest", "existential": "modest"},
}
STRATEGIC_VALUE_LABEL = {"homeland_vital": "Homeland / Vital", "ally_global": "Ally / Global", "partner_regional": "Partner / Regional", "other_local": "Other / Local"}
DAMAGE_LABEL = {"confined": "Confined", "considerable": "Considerable", "catastrophic": "Catastrophic", "existential": "Existential"}

# Fig. 26 MR consequence-of-event-to-NMS descriptions.
FIG26: dict[str, dict[str, str]] = {
    "extreme": {"RM": "Mission Failure, Objectives Unachievable", "RF": "No Sourcing Solutions Exist for Critical Requirements"},
    "major":   {"RM": "Objectives Minimally Achieved (consider time, priority)", "RF": "Shortfalls Exist for Critical Requirements"},
    "modest":  {"RM": "Objectives Mostly Achieved (consider time, priority)", "RF": "Worldwide Sourcing Solution Exist for Most Requirements"},
    "minor":   {"RM": "Mission Success, Objectives Achievable", "RF": "Joint Force Fully Sustained and Requirements Sourced"},
}

# Fig. 28 rows ("Risks to What") with their four cells, transcribed from the matrix.
FIG28: dict[str, dict[str, str]] = {
    "Achieve Objectives (CCMD Daily Ops)": {"minor": "Can fully achieve all OBJs (minimal costs)", "modest": "Can achieve all critical OBJs (acceptable costs)", "major": "Can achieve only most critical OBJs (substantial costs)", "extreme": "Potential failure; can't achieve critical OBJs (unacceptable costs)"},
    "Meet CCDR Requirements (CCMD Daily Ops)": {"minor": "GFM sources >= 90% (some shortfalls)", "modest": "GFM sources >= 80% (no critical shortfalls)", "major": "GFM sources >= 70% (critical shortfalls)", "extreme": "GFM sources < 70% (shortfalls cause mission failure)"},
    "Achieve Plan Objectives": {"minor": "As planned (minimal costs)", "modest": "Limited delays (acceptable costs)", "major": "Extended delays (substantial costs)", "extreme": "Extreme delays (unacceptable costs)"},
    "Meet CCDR Requirements (Contingency Sourcing)": {"minor": "Capacity to source plan requirements to achieve objective(s)", "modest": "Shortfalls cause minor plan deviations (no critical shortfalls)", "major": "Shortfalls cause major plan deviations", "extreme": "Shortfalls cause plan failure"},
    "Authorities": {"minor": "Full authority provided to achieve all objectives", "modest": "Sufficient authority provided to achieve most objectives, no critical shortfalls", "major": "Insufficient authority provided to achieve some critical objectives", "extreme": "Insufficient authority for key objectives, potential mission failure"},
    "Resources Meet Required Timelines": {"minor": "As planned (minimal costs)", "modest": "Limited delays (acceptable costs)", "major": "Extended delays (substantial costs)", "extreme": "Extreme delays (unacceptable costs)"},
    "Partnerships": {"minor": "Partnerships effective", "modest": "Critical partnerships effective", "major": "Critical partnerships partially effective", "extreme": "Critical partnerships ineffective, potential mission failure"},
    "Messaging": {"minor": "Messaging effective", "modest": "Key messaging effective", "major": "Key messaging partially effective", "extreme": "Key messaging ineffective, potential mission failure"},
    "Capability: DOTMLPF-P vs Threat": {"minor": "Dominance", "modest": "Superiority", "major": "Parity", "extreme": "Inferiority"},
    "Readiness (DRRS)": {"minor": "Full spectrum C1 full capability", "modest": "Ready for MCO C1/C2 some capacity shortfalls", "major": "Ready for minor armed conflict critical capabilities C1/C2 limited capacity", "extreme": "Critical capabilities < C2 capacity shortfalls cause mission failure"},
    "Stress on AC Force (D2D)": {"minor": "D2D 1:3 or greater", "modest": "1:3 > D2D >= 1:2.5", "major": "1:2.5 > D2D >= 1:2", "extreme": "D2D threshold is 1:2"},
    "Stress on RC Force (M2D)": {"minor": "M2D 1:5 or greater", "modest": "1:5 > M2D >= 1:4.5", "major": "1:4.5 > M2D >= 1:4", "extreme": "M2D threshold is 1:4"},
    "Stress on AC Mobility Force (T2D)": {"minor": "T2D > 1:2.5", "modest": "1:2.5 > T2D > 1:2", "major": "1:2 > T2D >= 1:1.5", "extreme": "T2D < 1:1.5"},
    "Stress on RC Mobility Air Force (T2D)": {"minor": "T2D > 1:5", "modest": "1:5 > T2D > 1:4", "major": "1:4 > T2D >= 1:3", "extreme": "T2D < 1:3"},
    "Modernization / Critical Maintenance": {"minor": "As planned (minimal costs)", "modest": "Limited delays (acceptable costs)", "major": "Extended delays (substantial costs)", "extreme": "Extreme delays (unacceptable costs)"},
    "Programmatic": {"minor": "Meets or exceeds schedule, IOC or FOC; incurred savings", "modest": "Minor delays milestone >= B; minor budget difficulty", "major": "Major delays milestone >= A; over budget (Nunn-McCurdy)", "extreme": "Program failure; zeroed out (de-funded)"},
    "Force Development & Design / Defense Industrial Base": {"minor": "Meets all mission requirements", "modest": "Meets priority mission requirements (no critical shortfalls)", "major": "Critical shortfalls cause major plan deviations", "extreme": "Failure to meet essential requirements causes mission failure"},
    "Operational Imperatives & CRCs": {"minor": "Achieves all operational imperatives (no capability gaps)", "modest": "Achieves priority operational imperatives (minor critical capability gaps)", "major": "Achieves minimal operational imperatives (minor critical capability gaps)", "extreme": "Operational imperatives not achieved (major critical capability gaps)"},
}

SUBSET_TO_RMRF = {"operational": "RM", "projected_mission": "RM", "force_management": "RF", "institutional": "RF"}
SUBSET_LABEL = {"operational": "Operational Risk", "projected_mission": "Projected Mission Risk", "force_management": "Force Management Risk", "institutional": "Institutional Risk"}


# ---------------------------------------------------------------- probability
def clip_p(p: float) -> float:
    """JRAM deliberately has no zero-probability level (Encl. B §3.c(1)(a)2): clip to [0.01, 0.99]."""
    return max(0.01, min(0.99, p))


def p_bin(p_raw: float) -> str:
    """Fig. 6 bands. Boundaries are 'best estimates' (Encl. B §3.c(1)(a)1); upper bound inclusive."""
    p = clip_p(p_raw)
    for level, upper in P_BANDS:
        if p <= upper + 1e-12:
            return level
    return "very_likely"


def forced_choice(posture_values: Iterable[tuple[str, str]]) -> tuple[str, str]:
    """Encl. C §4.d(2): decide Likely/Unlikely from friendly posture factors.
    posture_values: (entity_id, posture_state value). Likely if any factor is in the vulnerable set,
    Unlikely only if every factor is in the hardened set; with no documented posture the force
    'lacks rehearsed mitigations' -> Likely. Returns (level, rationale)."""
    vals = list(posture_values)
    likely_factors = [f"{e}: {POSTURE_LIKELY[v]}" for e, v in vals if v in POSTURE_LIKELY]
    unlikely_factors = [f"{e}: {POSTURE_UNLIKELY[v]}" for e, v in vals if v in POSTURE_UNLIKELY]
    if not vals:
        return "likely", "Roughly even chance intelligence estimate; no documented friendly posture factors, so the force is treated as lacking rehearsed mitigations (plotted Likely)."
    if likely_factors:
        return "likely", "Roughly even chance intelligence estimate; plotted Likely because friendly posture factors are " + "; ".join(likely_factors) + "."
    return "unlikely", "Roughly even chance intelligence estimate; plotted Unlikely because friendly posture factors are " + "; ".join(unlikely_factors) + "."


def crosswalk(likelihood_icd203: str, posture_values: Iterable[tuple[str, str]] = ()) -> tuple[str, bool, Optional[str]]:
    """Fig. 19 ICD 203 -> JRAM probability level. Returns (p_level, forced_choice_applied, rationale)."""
    lvl = ICD_TO_JRAM[likelihood_icd203]
    if lvl is not None:
        return lvl, False, None
    lvl, rationale = forced_choice(posture_values)
    return lvl, True, rationale


# ---------------------------------------------------------------- consequence and risk level
def msr_consequence(strategic_value: str, damage_degree: str) -> str:
    return FIG23[strategic_value][damage_degree]


def mr_consequence(fig28_row: str, fig28_cell: str) -> str:
    if fig28_row not in FIG28:
        raise KeyError(f"not a Fig. 28 row: {fig28_row}")
    if fig28_cell not in C_LEVELS:
        raise KeyError(fig28_cell)
    return fig28_cell


def risk_level(p_level: str, c_level: str) -> str:
    return CONTOUR[c_level][p_level]


def risk_level_boundary_note(p_level: str, c_level: str) -> Optional[str]:
    alt = CONTOUR_BOUNDARY_CELLS.get((c_level, p_level))
    return None if alt is None else f"contour boundary cell; alternative reading {alt}"


# ---------------------------------------------------------------- cascade and trend
def topological_order(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[str]:
    nodes = list(nodes)
    edges = list(edges)
    indeg = {n: 0 for n in nodes}
    succ: dict[str, list[str]] = {n: [] for n in nodes}
    for a, b in edges:
        succ[a].append(b)
        indeg[b] += 1
    order = [n for n in nodes if indeg[n] == 0]
    out: list[str] = []
    while order:
        n = order.pop(0)
        out.append(n)
        for m in succ[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                order.append(m)
    if len(out) != len(nodes):
        raise ValueError("escalation edges contain a cycle")
    return out


def noisy_or_cascade(base: dict[str, float], edges: Iterable[tuple[str, str, float]]) -> dict[str, float]:
    """P(j) = 1 - (1 - base_j) * prod_{i->j} (1 - w_ij * P(i)), evaluated in topological order
    (exact fixed point on a DAG). Output clipped to [0.01, 0.99]."""
    edges = list(edges)
    order = topological_order(base.keys(), [(a, b) for a, b, _ in edges])
    preds: dict[str, list[tuple[str, float]]] = {n: [] for n in base}
    for a, b, w in edges:
        preds[b].append((a, w))
    out: dict[str, float] = {}
    for n in order:
        prod = 1.0
        for a, w in preds[n]:
            prod *= 1.0 - w * out[a]
        out[n] = clip_p(1.0 - (1.0 - clip_p(base[n])) * prod)
    return out


def trend(p_by_horizon: dict[str, float], eps_per_year: float = 0.002) -> str:
    """Sign of dP/dt from a least-squares line through (horizon midpoint years, P_raw)."""
    xs = [HORIZON_MIDPOINT_YEARS[h] for h in ("near", "mid", "long") if h in p_by_horizon]
    ys = [p_by_horizon[h] for h in ("near", "mid", "long") if h in p_by_horizon]
    if len(xs) < 2:
        return "flat"
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    if slope > eps_per_year:
        return "up"
    if slope < -eps_per_year:
        return "down"
    return "flat"


# ---------------------------------------------------------------- statement renderers
def risk_type_phrase(risk_type: str, risk_subset: Optional[str]) -> str:
    if risk_type == "MSR":
        return "Military Strategic Risk"
    rmrf = SUBSET_TO_RMRF[risk_subset]
    return "Military Risk (Risk-to-Mission)" if rmrf == "RM" else "Military Risk (Risk-to-Force)"


def render_risk_statement(p_level: str, harmful_event: str, horizon: str, drivers: list[str], condition: str,
                          c_level: str, risk_level_: str, trend_: str, risk_type: str, risk_subset: Optional[str],
                          thing_of_value: str) -> str:
    """JRAM Fig. 11 template, verbatim slot order."""
    drv = ", ".join(drivers[:-1]) + (", and " if len(drivers) > 2 else " and ") + drivers[-1] if len(drivers) > 1 else (drivers[0] if drivers else "no identified drivers")
    trend_txt = f", trending {trend_}," if trend_ in ("up", "down") else ""
    return (f'There is a "{P_LABEL[p_level]}" probability that {harmful_event} in the {HORIZON_LABEL[horizon]}, '
            f"driven primarily by {drv} under current {condition} conditions, "
            f'will result in "{C_LABEL[c_level]}" consequence. '
            f"This results in {RISK_LABEL[risk_level_]}{trend_txt} {risk_type_phrase(risk_type, risk_subset)} to {thing_of_value}.")


RISK_STATEMENT_RE = re.compile(
    r'^There is a "(?P<p>Very Unlikely|Unlikely|Likely|Very Likely)" probability that (?P<event>.+?) in the '
    r"(?P<horizon>immediate \(days to months\)|near-term \(0-3 years\)|mid-term \(2-7 years\)|long-term \(5-15 years\)), "
    r"driven primarily by (?P<drivers>.+?) under current (?P<condition>action|inaction|posture|plan) conditions, "
    r'will result in "(?P<c>Minor|Modest|Major|Extreme)" consequence\. '
    r"This results in (?P<risk>Low|Moderate|Significant|High)(?P<trend>, trending (?:up|down),)? "
    r"(?P<type>Military Strategic Risk|Military Risk \((?:Risk-to-Mission|Risk-to-Force)\)) to (?P<tov>.+)\.$"
)


def parse_risk_statement(text: str) -> Optional[dict]:
    m = RISK_STATEMENT_RE.match(text.strip())
    return m.groupdict() if m else None


def render_opportunity_statement(p_level: str, beneficial_event: str, horizon: str, key_actions: str,
                                 c_level: str, thing_of_value: str, risk_level_: str, risk_type: str, risk_subset: Optional[str]) -> str:
    """JRAM Fig. 12 template."""
    return (f'There is a "{P_LABEL[p_level]}" probability that {beneficial_event} in the {HORIZON_LABEL[horizon]}, '
            f'if {key_actions} are undertaken, will generate "{C_LABEL[c_level]}" (beneficial) improvement in {thing_of_value}. '
            f"If not pursued, this creates {RISK_LABEL[risk_level_]} risk to {risk_type_phrase(risk_type, risk_subset)}.")


OPPORTUNITY_STATEMENT_RE = re.compile(
    r'^There is a "(?P<p>Very Unlikely|Unlikely|Likely|Very Likely)" probability that (?P<event>.+?) in the '
    r"(?P<horizon>immediate \(days to months\)|near-term \(0-3 years\)|mid-term \(2-7 years\)|long-term \(5-15 years\)), "
    r'if (?P<actions>.+?) are undertaken, will generate "(?P<c>Minor|Modest|Major|Extreme)" \(beneficial\) improvement in (?P<tov>.+?)\. '
    r"If not pursued, this creates (?P<risk>Low|Moderate|Significant|High) risk to (?P<type>Military Strategic Risk|Military Risk \((?:Risk-to-Mission|Risk-to-Force)\))\.$"
)


def render_aggregated_statement(horizon: str, events: list[str], ability: str, degraded_or_denied: str,
                                risk_level_: str, thing_of_value: str) -> str:
    """JRAM Fig. 5 aggregated (complex) risk statement. The template's own 'may be' is doctrine text."""
    ev = "; ".join(events)
    return (f"If the following related harmful events or conditions occur in combination within the {HORIZON_LABEL[horizon]}, "
            f"{ev}, then the Joint Force's ability to {ability} may be {degraded_or_denied} resulting in {RISK_LABEL[risk_level_]} risk "
            f"to {thing_of_value} in the {HORIZON_LABEL[horizon]}.")


AGGREGATED_STATEMENT_RE = re.compile(
    r"^If the following related harmful events or conditions occur in combination within the (?P<horizon>[^,]+), (?P<events>.+?), "
    r"then the Joint Force's ability to (?P<ability>.+?) may be (?P<effect>degraded|denied) resulting in (?P<risk>Low|Moderate|Significant|High) risk to (?P<tov>.+?) in the (?P<horizon2>.+)\.$"
)
