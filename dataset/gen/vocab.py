"""Controlled vocabularies (enums) for every table, each with its doctrinal source.

Every enum here is reproduced from the doctrine in ../doctrine/ (see doctrine/EXTRACTS.md) or is
a dataset-defined vocabulary explicitly marked DATASET. SCHEMA.md is generated partly from the
`SOURCE` mapping at the bottom of this file, so citations live in exactly one place.
"""
from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover
        return str(self.value)


# ---------------------------------------------------------------- sources / documents
class DocType(StrEnum):
    reference_entry = "reference_entry"
    sitrep = "sitrep"
    news = "news"
    message_traffic = "message_traffic"
    tabular = "tabular"
    assessment = "assessment"
    risk_context = "risk_context"
    collection_plan = "collection_plan"
    coa_statement = "coa_statement"
    guidance = "guidance"


class Reliability(StrEnum):
    A = "A"; B = "B"; C = "C"; D = "D"; E = "E"; F = "F"


class Credibility(StrEnum):
    one = "1"; two = "2"; three = "3"; four = "4"; five = "5"; six = "6"


class Perturbation(StrEnum):
    paraphrase = "paraphrase"
    unit_drift = "unit_drift"
    stale_echo = "stale_echo"
    implicit = "implicit"
    distractor = "distractor"
    alias = "alias"
    typo = "typo"
    contradiction = "contradiction"
    hedge_drift = "hedge_drift"
    mixed_scale = "mixed_scale"


# ---------------------------------------------------------------- entities / claims
class EntityType(StrEnum):
    actor = "actor"
    unit = "unit"
    system = "system"
    location = "location"
    polity = "polity"
    infrastructure = "infrastructure"
    problem_set = "problem_set"
    organization_role = "organization_role"


class ValueType(StrEnum):
    entity = "entity"
    number = "number"
    string = "string"
    bool = "bool"
    date = "date"


class LikelihoodICD203(StrEnum):
    almost_no_chance = "almost_no_chance"
    very_unlikely = "very_unlikely"
    unlikely = "unlikely"
    roughly_even_chance = "roughly_even_chance"
    likely = "likely"
    very_likely = "very_likely"
    almost_certain = "almost_certain"


# ICD 203 bands as reproduced in JRAM Fig. 19 (percent).
ICD203_BANDS: dict[str, tuple[int, int]] = {
    "almost_no_chance": (1, 5),
    "very_unlikely": (5, 20),
    "unlikely": (20, 45),
    "roughly_even_chance": (45, 55),
    "likely": (55, 80),
    "very_likely": (80, 95),
    "almost_certain": (95, 99),
}

# Rendered ICD 203 terms (JRAM Fig. 19, left column; primary term first, then the alternates
# the figure lists). Products use the primary term only.
ICD203_TERMS: dict[str, list[str]] = {
    "almost_no_chance": ["almost no chance", "remote"],
    "very_unlikely": ["very unlikely", "highly improbable"],
    "unlikely": ["unlikely", "improbable", "improbably"],
    "roughly_even_chance": ["roughly even chance", "roughly even odds"],
    "likely": ["likely", "probable", "probably"],
    "very_likely": ["very likely", "highly probable"],
    "almost_certain": ["almost certain", "almost certainly", "nearly certain"],
}


class ConfidenceICD203(StrEnum):
    low = "low"
    moderate = "moderate"
    high = "high"


# Shrink-toward-0.5 factors for the derived numeric confidence (v2 §2.6a).
CONFIDENCE_SHRINK: dict[str, float] = {"high": 0.0, "moderate": 0.15, "low": 0.35}
# Band midpoint used for factual (non-estimative) claims = midpoint of "almost certain" (0.97).
FACTUAL_BASE = 0.97


class ClaimStatus(StrEnum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"
    superseded = "superseded"


class Predicate(StrEnum):
    """Controlled predicate vocabulary (DATASET). value_type/unit per predicate in PREDICATES."""
    # attributive
    range_km = "range_km"
    count = "count"
    readiness = "readiness"
    status = "status"
    throughput_per_day = "throughput_per_day"
    alignment = "alignment"
    basing_access = "basing_access"
    mobilization_days = "mobilization_days"
    mobilized_brigades = "mobilized_brigades"
    cyber_capacity = "cyber_capacity"
    munitions_stock_days = "munitions_stock_days"
    posture_state = "posture_state"
    capacity_mw = "capacity_mw"
    displaced_persons = "displaced_persons"
    outage_hours = "outage_hours"
    intent = "intent"
    mixing_bias = "mixing_bias"
    # relational
    located_at = "located_at"
    operated_by = "operated_by"
    subordinate_to = "subordinate_to"
    supplies = "supplies"
    controls = "controls"
    hosts = "hosts"


# predicate -> (value_type, unit or None, allowed string values or None, short meaning)
PREDICATES: dict[str, tuple[str, str | None, list[str] | None, str]] = {
    "range_km": ("number", "km", None, "maximum effective range of a system"),
    "count": ("number", "each", None, "number of systems or platforms held by a unit"),
    "readiness": ("number", "fraction", None, "readiness as a fraction 0..1 of full mission capability"),
    "status": ("string", None, ["operational", "degraded", "inoperative"], "functional status (JP 3-60 Ch. I §8.b(2))"),
    "throughput_per_day": ("number", "transits/day", None, "chokepoint or port throughput per day"),
    "alignment": ("string", None, ["blue_aligned", "neutral", "red_aligned"], "polity alignment"),
    "basing_access": ("bool", None, None, "whether the polity grants Blue basing access"),
    "mobilization_days": ("number", "days", None, "days for the actor to mobilize the stated brigade count"),
    "mobilized_brigades": ("number", "brigades", None, "brigades currently mobilized"),
    "cyber_capacity": ("string", None, ["limited", "moderate", "extensive"], "offensive cyber capacity against logistics networks"),
    "munitions_stock_days": ("number", "days", None, "days of supply of precision munitions"),
    "posture_state": ("string", None, ["hardened", "postured_to_react", "mitigated", "vulnerable", "out_of_position", "unmitigated"], "friendly posture factor (JRAM Encl. C §4.d(2))"),
    "capacity_mw": ("number", "MW", None, "generating capacity"),
    "displaced_persons": ("number", "persons", None, "internally displaced persons"),
    "outage_hours": ("number", "hours", None, "cumulative outage hours in the period"),
    "intent": ("string", None, ["coercive", "defensive", "opportunistic", "benign"], "assessed intent of an actor"),
    "mixing_bias": ("number", "fraction", None, "rock-paper-scissors: deviation of a player's mix from uniform"),
    "located_at": ("entity", None, None, "subject is located at object (location)"),
    "operated_by": ("entity", None, None, "system is operated by unit/actor"),
    "subordinate_to": ("entity", None, None, "unit is subordinate to unit/actor"),
    "supplies": ("entity", None, None, "infrastructure supplies location/unit"),
    "controls": ("entity", None, None, "actor controls location"),
    "hosts": ("entity", None, None, "location hosts unit"),
}


class PostureState(StrEnum):
    hardened = "hardened"
    postured_to_react = "postured_to_react"
    mitigated = "mitigated"
    vulnerable = "vulnerable"
    out_of_position = "out_of_position"
    unmitigated = "unmitigated"


POSTURE_LIKELY = {"vulnerable", "out_of_position", "unmitigated"}
POSTURE_UNLIKELY = {"hardened", "postured_to_react", "mitigated"}


# ---------------------------------------------------------------- JSPS guidance
class GuidanceProductType(StrEnum):
    NSS = "NSS"
    NDS = "NDS"
    NMS = "NMS"
    JSCP = "JSCP"
    GCP = "GCP"
    CCP = "CCP"
    contingency_plan = "contingency_plan"
    OPORD = "OPORD"


class TimeHorizon(StrEnum):
    immediate = "immediate"  # expedited process, days to months (JRAM Encl. B §3.a(1))
    near = "near"            # 0-3 years
    mid = "mid"              # 2-7 years
    long = "long"            # 5-15 years


HORIZON_YEARS: dict[str, tuple[float, float]] = {"immediate": (0.0, 0.5), "near": (0.0, 3.0), "mid": (2.0, 7.0), "long": (5.0, 15.0)}
HORIZON_LABEL: dict[str, str] = {
    "immediate": "immediate (days to months)",
    "near": "near-term (0-3 years)",
    "mid": "mid-term (2-7 years)",
    "long": "long-term (5-15 years)",
}


# ---------------------------------------------------------------- game / strategy
class ObjectiveKind(StrEnum):
    end_state = "end_state"
    objective = "objective"
    effect = "effect"


class Direction(StrEnum):
    max = "max"
    min = "min"


class TacticClass(StrEnum):
    posture = "posture"
    isr = "isr"
    strike = "strike"
    logistics = "logistics"
    information = "information"
    diplomatic = "diplomatic"
    cyber = "cyber"
    signal = "signal"


class Echelon(StrEnum):
    national = "national"
    theater_strategic = "theater_strategic"
    operational = "operational"
    tactical = "tactical"


class RiskFunctional(StrEnum):
    expected = "expected"
    cvar = "cvar"
    minimax = "minimax"


class StrategyStatus(StrEnum):
    valid = "valid"
    invalid = "invalid"
    stale = "stale"
    infeasible = "infeasible"


class ValidityTest(StrEnum):
    suitable = "suitable"
    feasible = "feasible"
    acceptable = "acceptable"
    distinguishable = "distinguishable"
    complete = "complete"


class DistinguishDim(StrEnum):
    main_effort = "main_effort"
    scheme = "scheme"
    sequencing = "sequencing"
    mechanism = "mechanism"
    task_org = "task_org"
    reserves = "reserves"


class Sequencing(StrEnum):
    sequential = "sequential"
    simultaneous = "simultaneous"


class AdversaryCoaLabel(StrEnum):
    most_likely = "most_likely"
    most_dangerous = "most_dangerous"
    alternative = "alternative"


class AssumptionRole(StrEnum):
    state = "state"
    transition = "transition"
    opponent = "opponent"
    means = "means"


class AssumptionOrigin(StrEnum):
    higher_hq = "higher_hq"
    own = "own"


class AssumptionStatus(StrEnum):
    holds = "holds"
    violated = "violated"
    stale = "stale"
    unknown = "unknown"


class CmpOp(StrEnum):
    eq = "=="
    ne = "!="
    lt = "<"
    le = "<="
    gt = ">"
    ge = ">="
    abs_le = "abs_le"
    in_ = "in"


class DependencyKind(StrEnum):
    supports = "supports"
    contradicts = "contradicts"
    grounds = "grounds"
    requires = "requires"
    enables = "enables"
    drives = "drives"
    escalates = "escalates"


class NodeType(StrEnum):
    claim = "claim"
    assumption = "assumption"
    strategy = "strategy"
    action = "action"
    objective = "objective"
    problem_set = "problem_set"
    harmful_event = "harmful_event"


# ---------------------------------------------------------------- JRAM risk
class RiskType(StrEnum):
    MSR = "MSR"
    MR = "MR"


class RiskSubset(StrEnum):
    operational = "operational"
    projected_mission = "projected_mission"
    force_management = "force_management"
    institutional = "institutional"


class StrategicValue(StrEnum):
    homeland_vital = "homeland_vital"
    ally_global = "ally_global"
    partner_regional = "partner_regional"
    other_local = "other_local"


class DamageDegree(StrEnum):
    confined = "confined"
    considerable = "considerable"
    catastrophic = "catastrophic"
    existential = "existential"


class HarmCondition(StrEnum):
    action = "action"
    inaction = "inaction"
    posture = "posture"
    plan = "plan"


class SourceKind(StrEnum):
    threat = "threat"
    hazard = "hazard"


class DriverKind(StrEnum):
    frequency = "frequency"
    vulnerability = "vulnerability"
    resilience = "resilience"
    criticality = "criticality"
    accessibility = "accessibility"
    recognition = "recognition"
    impact = "impact"
    resources = "resources"
    response = "response"
    reliance = "reliance"


class DriverLocus(StrEnum):
    internal = "internal"
    external = "external"


class PLevel(StrEnum):
    very_unlikely = "very_unlikely"
    unlikely = "unlikely"
    likely = "likely"
    very_likely = "very_likely"


class CLevel(StrEnum):
    minor = "minor"
    modest = "modest"
    major = "major"
    extreme = "extreme"


class RiskLevel(StrEnum):
    low = "low"
    moderate = "moderate"
    significant = "significant"
    high = "high"


class Trend(StrEnum):
    up = "up"
    down = "down"
    flat = "flat"


# Fig. 28 rows (the "Risks to What" column) grouped by the risk subset they inform.
FIG28_ROWS: dict[str, list[str]] = {
    "operational": [
        "Achieve Objectives (CCMD Daily Ops)",
        "Meet CCDR Requirements (CCMD Daily Ops)",
        "Authorities",
        "Partnerships",
        "Messaging",
        "Capability: DOTMLPF-P vs Threat",
    ],
    "projected_mission": [
        "Achieve Plan Objectives",
        "Resources Meet Required Timelines",
        "Operational Imperatives & CRCs",
    ],
    "force_management": [
        "Meet CCDR Requirements (Contingency Sourcing)",
        "Readiness (DRRS)",
        "Stress on AC Force (D2D)",
        "Stress on RC Force (M2D)",
        "Stress on AC Mobility Force (T2D)",
        "Stress on RC Mobility Air Force (T2D)",
    ],
    "institutional": [
        "Modernization / Critical Maintenance",
        "Programmatic",
        "Force Development & Design / Defense Industrial Base",
    ],
}


# ---------------------------------------------------------------- collection (JP 2-01)
class GapType(StrEnum):
    missing = "missing"
    stale = "stale"
    low_confidence = "low_confidence"
    contradiction = "contradiction"


class RfiDisposition(StrEnum):
    answered_from_holdings = "answered_from_holdings"
    gap_confirmed = "gap_confirmed"


class ReqStatus(StrEnum):
    research = "research"
    validation = "validation"
    submission = "submission"
    satisfaction = "satisfaction"
    closed = "closed"


class Discipline(StrEnum):
    GEOINT = "GEOINT"
    SIGINT = "SIGINT"
    HUMINT = "HUMINT"
    OSINT = "OSINT"
    MASINT = "MASINT"


# ---------------------------------------------------------------- JP 3-60 (extension)
class TargetCharacteristicType(StrEnum):
    physical = "physical"
    functional = "functional"
    cognitive_control_informational = "cognitive_control_informational"
    environmental = "environmental"
    temporal = "temporal"


# ---------------------------------------------------------------- doctrinal source of every enum
# (enum name) -> (source citation, note). Used to generate the enum table in SCHEMA.md.
SOURCE: dict[str, tuple[str, str]] = {
    "DocType": ("v2 §3.1; product formats: JRAM Fig. 3 (risk_context), JP 2-01 Fig. III-8 (collection_plan), JP 5-0 Ch. III/App. F (coa_statement), CJCSI 3100.01F Encl. A/C/D (guidance)", "DATASET list of document kinds"),
    "Reliability": ("Source reliability A–F (Admiralty/NATO code); JP 2-01 Ch. III §13 does not reproduce the scale", "DATASET usage; letter scale is the standard intelligence source-reliability rating"),
    "Credibility": ("Information credibility 1–6 (Admiralty/NATO code)", "as above"),
    "Perturbation": ("v1 §6, v2 §6", "DATASET realism perturbations"),
    "EntityType": ("v2 §3.2", "DATASET"),
    "ValueType": ("v1 §3.3", "DATASET"),
    "LikelihoodICD203": ("ICD 203 (12 Jun 2023) 7-level scale as reproduced in JRAM Fig. 19, p. C-4", "bands in ICD203_BANDS"),
    "ConfidenceICD203": ("JRAM Encl. C §4.c(1)-(3), p. C-5", "High / Moderate / Low"),
    "ClaimStatus": ("v1 §3.3", "DATASET"),
    "Predicate": ("DATASET; `status` values follow JP 3-60 Ch. I §8.b(2); `posture_state` values follow JRAM Encl. C §4.d(2)(a)-(b)", "controlled vocabulary"),
    "PostureState": ("JRAM Encl. C §4.d(2)(a)-(b), p. C-5", "forced-choice posture factors"),
    "GuidanceProductType": ("CJCSI 3100.01F Encl. A §3.c(2)-(3) and Encl. C §1-2, Encl. D §3-6; JP 5-0 Glossary (contingency plan, OPORD)", "NSS/NDS/NMS/JSCP/GCP/CCP + subordinate plans"),
    "TimeHorizon": ("JRAM Encl. B §3.a(1)-(2), p. B-3; CJCSI 3100.01F Encl. A fn. 4", "near 0–3 / mid 2–7 / long 5–15 years; immediate = expedited process"),
    "ObjectiveKind": ("JP 5-0 Ch. IV Fig. IV-9, p. IV-27", "end state / objectives / effects"),
    "Direction": ("v1 §3.7", "DATASET"),
    "TacticClass": ("v1 §3.6", "DATASET"),
    "Echelon": ("JP 5-0 Fig. IV-9 levels (national strategic, theater strategic, operational, tactical)", ""),
    "RiskFunctional": ("v1 §2.2 ρ ∈ {E, CVaR, minimax}; commander's risk tolerance per JRAM Encl. B §1.b", "DATASET formalization"),
    "StrategyStatus": ("v2 §3.7", "invalid = fails a JP 5-0 validity test (Ch. III §(q))"),
    "ValidityTest": ("JP 5-0 Ch. III §(q) 1–5, pp. III-41–III-42", "suitable, feasible, acceptable, distinguishable, complete"),
    "DistinguishDim": ("JP 5-0 Ch. III §(q)4 a–f, p. III-42", "main effort, scheme, sequential/simultaneous, mechanism, task organization, reserves"),
    "Sequencing": ("JP 5-0 Ch. III §(q)4.c", "sequential versus simultaneous maneuvers"),
    "AdversaryCoaLabel": ("JP 5-0 Ch. III COA development inputs (Fig. III-13): enemy most likely / most dangerous COA", "alternative = DATASET third support point"),
    "AssumptionRole": ("v1 §3.13", "DATASET"),
    "AssumptionOrigin": ("JP 5-0 Ch. III §(6)(a) and (b)3, p. III-17", "higher headquarters assumptions are followed in framing but validated for execution"),
    "AssumptionStatus": ("JP 5-0 Ch. III §(6)(b)1 validate/invalidate cycle; v2 §2.4", "holds / violated / stale / unknown"),
    "CmpOp": ("v1 §3.13", "DATASET"),
    "DependencyKind": ("v2 §2.4", "DATASET typed graph"),
    "NodeType": ("v2 §2.4", "DATASET"),
    "RiskType": ("JRAM Encl. C §6.b(1)-(2), pp. C-8–C-10; Glossary Part II", "MSR / MR"),
    "RiskSubset": ("JRAM Encl. C §6.b(2)(a)1-2 and (b)1-2, pp. C-10–C-12; Fig. 27", "operational, projected mission, force management, institutional"),
    "StrategicValue": ("JRAM Fig. 23, p. C-10", "Homeland/Vital, Ally/Global, Partner/Regional, Other/Local"),
    "DamageDegree": ("JRAM Fig. 22 and Fig. 23, pp. C-9–C-10", "Confined, Considerable, Catastrophic, Existential"),
    "HarmCondition": ("JRAM Fig. 11, p. B-16 ([action/inaction/posture/plan] slot)", ""),
    "SourceKind": ("JRAM Encl. B §3.b(2)(a)-(b), p. B-5", "threat / hazard"),
    "DriverKind": ("JRAM Encl. B §3.b(3)(a)-(j), pp. B-5–B-6", "ten driver considerations"),
    "DriverLocus": ("JRAM Fig. 4, p. B-6", "internal / external"),
    "PLevel": ("JRAM Fig. 6, p. B-8", "Very Unlikely ~01-20%, Unlikely ~21-50%, Likely ~51-80%, Very Likely ~81-99%"),
    "CLevel": ("JRAM Fig. 7, p. B-8", "Minor / Modest / Major / Extreme"),
    "RiskLevel": ("JRAM Fig. 8, p. B-9; Glossary 'Risk Level'", "Low / Moderate / Significant / High"),
    "Trend": ("JRAM Encl. B §3.c(3), p. B-10", "trending up / trending down; flat = no modifier"),
    "GapType": ("v1 §3.18", "DATASET"),
    "RfiDisposition": ("JP 2-01 Ch. III §13.b(1), p. III-19", "RFI checks holdings; gap identified when information is not available"),
    "ReqStatus": ("JP 2-01 Ch. III §13.a, p. III-19 (research, validation, submission, satisfaction)", "`closed` is a DATASET terminal state, not a JP 2-01 tracking state"),
    "Discipline": ("JP 2-01 Ch. III §11.b(3) and Fig. III-9 (GEOINT, SIGINT, HUMINT, MASINT); OSINT per JP 2-01 glossary", ""),
    "TargetCharacteristicType": ("JP 3-60 Ch. I §8 a–e, pp. I-13–I-17", "physical; functional; cognitive, control, and informational; environmental; temporal"),
}
