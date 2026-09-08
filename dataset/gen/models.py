"""Pydantic models = the schema contract. One model per table; JSON Schemas in schema/ are
exported from these (`python -m gen schema`). Column semantics, PK/FK, computed columns and the
doctrinal source of each enum are documented in schema/SCHEMA.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gen import vocab as V

Value = Union[bool, int, float, str, None]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


# ---------------------------------------------------------------- predicate JSON grammar
class VarCmp(Strict):
    """Leaf: compare an observable/state variable (or a claim value) with a constant."""
    var: str
    op: V.CmpOp
    value: Any = None


class AllOf(Strict):
    all: list["Condition"]


class AnyOf(Strict):
    any: list["Condition"]


Condition = Union[bool, VarCmp, AllOf, AnyOf]
AllOf.model_rebuild()
AnyOf.model_rebuild()


class Tolerance(Strict):
    """Assumption tolerance applied to the current approved claim value, e.g. {"op":"<=","value":300}."""
    op: V.CmpOp
    value: Any = None


# ---------------------------------------------------------------- base tables
class Source(Strict):
    source_id: str = Field(pattern=r"^src_[a-z0-9_]+$")
    doc_type: V.DocType
    title: str
    published_at: date
    author_org: str = Field(description="fictional unit, or a real organizational role such as 'supported CCMD J-2'")
    reliability: V.Reliability
    credibility: V.Credibility
    real_world: bool = False
    public_reference: Optional[str] = None
    path: str = Field(description="relative path under dataset/ (corpus/ or injects/batch_n/)")
    batch: int = Field(ge=0, le=3)
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    perturbations: list[V.Perturbation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _real_world_needs_reference(self):
        if self.real_world and not self.public_reference:
            raise ValueError("real_world sources must carry public_reference")
        return self


class Entity(Strict):
    entity_id: str = Field(pattern=r"^(ent|loc|inf|unit|sys|role)_[a-z0-9_]+$", description="typed readable prefix: ent_ actor/polity/problem set, loc_ location, inf_ infrastructure, unit_ unit, sys_ system, role_ organization role")
    entity_type: V.EntityType
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    description: Optional[str] = None


class ClaimCore(Strict):
    subject_id: str
    predicate: V.Predicate
    object_id: Optional[str] = None
    value: Value = None
    value_type: V.ValueType
    unit: Optional[str] = None
    valid_from: date
    valid_to: Optional[date] = None
    estimative: bool = False
    likelihood_icd203: Optional[V.LikelihoodICD203] = None
    confidence_icd203: V.ConfidenceICD203
    confidence: float = Field(ge=0.0, le=1.0, description="DERIVED per SCHEMA.md §confidence")

    @model_validator(mode="after")
    def _estimative_consistency(self):
        if self.estimative and self.likelihood_icd203 is None:
            raise ValueError("estimative claims must carry likelihood_icd203")
        if not self.estimative and self.likelihood_icd203 is not None:
            raise ValueError("factual claims carry likelihood_icd203 = null")
        vt = self.value_type
        if vt == "entity" and not self.object_id:
            raise ValueError("value_type entity requires object_id")
        if vt != "entity" and self.value is None:
            raise ValueError("attributive claims require a value")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to before valid_from")
        return self


class Claim(ClaimCore):
    claim_id: str = Field(pattern=r"^clm_[a-z0-9_]+$")
    source_id: str
    span_start: int = Field(ge=0)
    span_end: int = Field(ge=0)
    asserted_at: date = Field(description="transaction time; = source.published_at unless the doc quotes an older report")
    likelihood_surface_term: Optional[str] = Field(default=None, description="the likelihood phrase as written in the span (may be a non-ICD synonym under hedge_drift)")
    status: V.ClaimStatus
    supersedes_claim_id: Optional[str] = None
    truth_claim_id: Optional[str] = Field(default=None, description="truth/ only: the fact this claim instantiates")

    @model_validator(mode="after")
    def _span(self):
        if self.span_end <= self.span_start:
            raise ValueError("span_end must exceed span_start")
        return self


class Fact(ClaimCore):
    fact_id: str = Field(pattern=r"^fct_[a-z0-9_]+$")
    supersedes_fact_id: Optional[str] = Field(default=None, description="the earlier fact on the same (subject, predicate) this one replaces: together they are a change event")
    first_asserted_batch: int = Field(ge=0, le=3, description="0 = asserted by a T0 document; n = first asserted by inject batch n")


class Guidance(Strict):
    guidance_id: str = Field(pattern=r"^gd_[a-z0-9_]+$")
    product_type: V.GuidanceProductType
    title: str
    issuing_role: str = Field(description="real role that issues this product type: President (NSS), SecWar (NDS), CJCS (NMS, JSCP), SecWar-approved/CJCS-endorsed (GCP), CCDR (CCP)")
    parent_guidance_id: Optional[str] = None
    objective_ids: list[str] = Field(default_factory=list)
    source_id: Optional[str] = Field(default=None, description="the rendered guidance document (set once corpus is rendered)")


class HorizonMapEntry(Strict):
    period: int = Field(ge=1)
    jsps_horizon: Literal["near", "mid", "long"]


class StateVariable(Strict):
    name: str
    domain: list[Value]


class Observable(Strict):
    actor_id: str
    variable: str


class Game(Strict):
    game_id: str
    name: str
    actor_ids: list[str]
    horizon: int = Field(ge=1)
    horizon_map: list[HorizonMapEntry]
    state_variables: list[StateVariable]
    observables: list[Observable]

    @model_validator(mode="after")
    def _map_covers_periods(self):
        periods = sorted(e.period for e in self.horizon_map)
        if periods != list(range(1, self.horizon + 1)):
            raise ValueError("horizon_map must cover periods 1..horizon exactly once")
        return self


class Effect(Strict):
    variable: str
    delta: Value


class Action(Strict):
    action_id: str = Field(pattern=r"^act_[a-z0-9_]+$")
    game_id: str
    actor_id: str
    name: str
    tactic_class: V.TacticClass
    line_of_effort: str
    mechanism: str = Field(description="primary mechanism for mission accomplishment (JP 5-0 Ch. III §(q)4.d), e.g. deny, delay, deter_by_denial, defeat, influence, sustain")
    cost: dict[str, float] = Field(default_factory=dict, description="resource_id -> cost c(a)")
    preconditions: Condition = True
    effects: list[Effect] = Field(default_factory=list)


class Objective(Strict):
    objective_id: str = Field(pattern=r"^obj_[a-z0-9_]+$")
    game_id: str
    actor_id: str
    name: str
    kind: V.ObjectiveKind
    guidance_id: Optional[str] = None
    parent_objective_id: Optional[str] = Field(default=None, description="effect -> objective -> end_state nesting (JP 5-0 Fig. IV-9)")
    metric: str
    direction: V.Direction = V.Direction.max
    aspiration: Optional[float] = None
    statement: Optional[str] = Field(default=None, description="short active-voice phrase (JP 5-0 Ch. III §(11)(b))")


class Resource(Strict):
    resource_id: str = Field(pattern=r"^res_[a-z0-9_]+$")
    game_id: str
    name: str
    unit: str


class ValidityResult(Strict):
    passed: bool = Field(alias="pass")
    evidence: str
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Validity(Strict):
    suitable: ValidityResult
    feasible: ValidityResult
    acceptable: ValidityResult
    distinguishable: ValidityResult
    complete: ValidityResult


class Strategy(Strict):
    strategy_id: str = Field(pattern=r"^str_[a-z0-9_]+$")
    game_id: str
    actor_id: str
    name: str
    summary: str
    echelon: V.Echelon
    guidance_source: Optional[str] = Field(default=None, description="FK guidance; the JSPS product this COA descends from")
    adversary_coa_label: Optional[V.AdversaryCoaLabel] = Field(default=None, description="set on opponent (Red) strategies only")
    mission_who: str
    mission_what: str
    mission_when: str
    mission_where: str
    mission_why: str
    end_state_objective_id: str
    constraints: list[str] = Field(default_factory=list, description="'must do' (JP 5-0 Ch. III §(7)(a))")
    restraints: list[str] = Field(default_factory=list, description="'cannot do' (JP 5-0 Ch. III §(7)(b))")
    main_effort: str = Field(description="line of effort that is the main effort (distinguishability dim main_effort)")
    sequencing: V.Sequencing
    task_org: list[str] = Field(default_factory=list, description="unit entity ids in the task organization")
    reserve_policy: str = Field(description="how reserves are used (distinguishability dim reserves)")
    mitigates_he_ids: list[str] = Field(default_factory=list, description="harmful events this COA mitigates (acceptable test)")
    risk_functional: V.RiskFunctional
    risk_alpha: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    opponent_model_id: str
    theory_of_victory: list[str] = Field(default_factory=list, description="ordered dependency edge ids: action -enables-> claim -supports-> objective ... end_state")
    # computed
    validity: Optional[Validity] = None
    status: Optional[V.StrategyStatus] = None
    aspiration: Optional[float] = Field(default=None, description="COMPUTED w·τ over the strategy's objectives")
    value: Optional[float] = None
    value_ci: Optional[list[float]] = Field(default=None, min_length=2, max_length=2)
    robustness: Optional[float] = None
    world_version: Optional[int] = None


class StrategyObjective(Strict):
    strategy_id: str
    objective_id: str
    weight: float = Field(ge=0.0, le=1.0)
    rating_1_to_3: Optional[int] = Field(default=None, ge=1, le=3, description="COMPUTED rank of E[u_k] among valid strategies of the same actor (3 = best)")


class StrategyResource(Strict):
    strategy_id: str
    resource_id: str
    budget: float = Field(ge=0.0)


class PolicyRule(Strict):
    rule_id: str = Field(pattern=r"^rule_[a-z0-9_]+$")
    strategy_id: str
    priority: int = Field(ge=0, description="lower fires first; equal priority + identical condition = one mixed distribution")
    condition: Condition
    action_id: str
    probability: float = Field(gt=0.0, le=1.0)
    periods: Optional[list[int]] = Field(default=None, description="periods in which the rule is active; null = all periods (used by the feasible test)")
    rationale_claim_ids: list[str] = Field(default_factory=list)
    decision_point_id: Optional[str] = None


class DecisionPoint(Strict):
    dp_id: str = Field(pattern=r"^dp_[a-z0-9_]+$")
    strategy_id: str
    name: str
    condition: Condition
    branch_rule_ids: list[str]
    pir_id: Optional[str] = Field(default=None, description="PIR tied to this decision point (JP 5-0 Ch. IV §(b)3)")
    latest_period: Optional[int] = Field(default=None, ge=1, description="latest period at which the decision can be made")


class OpponentMix(Strict):
    strategy_id: str
    probability: float = Field(ge=0.0, le=1.0)


class OpponentModel(Strict):
    opponent_model_id: str = Field(pattern=r"^om_[a-z0-9_]+$")
    actor_id: str = Field(description="the opponent whose strategies are mixed")
    distribution: list[OpponentMix]


class Payoff(Strict):
    strategy_id: str
    opponent_strategy_id: str
    world: str = Field(pattern=r"^[01]+$")
    utility: list[float]


class Distinguishability(Strict):
    strategy_a: str
    strategy_b: str
    dims_differing: list[V.DistinguishDim]
    passed: bool = Field(alias="pass", description="COMPUTED: len(dims_differing) >= 2")
    model_config = ConfigDict(extra="forbid", populate_by_name=True, use_enum_values=True)


class Assumption(Strict):
    assumption_id: str = Field(pattern=r"^asm_[a-z0-9_]+$")
    strategy_id: str
    index_k: int = Field(ge=0)
    statement: str
    subject_id: str
    predicate: V.Predicate
    tolerance: Tolerance
    role: V.AssumptionRole
    jp50_logical: bool
    jp50_realistic: bool
    jp50_essential: bool
    origin: V.AssumptionOrigin
    in_decision_matrix: bool = True
    # computed
    p_holds: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[V.AssumptionStatus] = None
    sensitivity: Optional[float] = None
    evpi: Optional[float] = None


class Dependency(Strict):
    edge_id: str = Field(pattern=r"^dep_[a-z0-9_]+$")
    from_type: V.NodeType
    from_id: str
    to_type: V.NodeType
    to_id: str
    kind: V.DependencyKind
    weight: float = Field(ge=-1.0, le=1.0)
    mechanism: str
    evidence_claim_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _typed_edges(self):
        allowed = {
            "supports": {("claim", "claim"), ("claim", "objective"), ("objective", "objective")},
            "contradicts": {("claim", "claim")},
            "grounds": {("claim", "assumption")},
            "requires": {("assumption", "strategy")},
            "enables": {("action", "claim")},
            "drives": {("claim", "harmful_event")},
            "escalates": {("harmful_event", "harmful_event")},
        }
        if (self.from_type, self.to_type) not in allowed[self.kind]:
            raise ValueError(f"edge kind {self.kind} not allowed from {self.from_type} to {self.to_type}")
        return self


# ---------------------------------------------------------------- JRAM risk tables
class ProblemSet(Strict):
    problem_set_id: str = Field(pattern=r"^ps_[a-z0-9_]+$")
    entity_id: str
    name: str
    tier: int = Field(ge=0)
    thing_of_value_ids: list[str] = Field(description="FK objectives (things of value, JRAM Encl. B §1.a)")
    risk_owner_role: str
    risk_context_source_id: Optional[str] = Field(default=None, description="FK sources with doc_type risk_context")
    tolerance_statement: str
    strategic_context: str = Field(description="Fig. 3 para a")
    scope_and_boundaries: str = Field(description="Fig. 3 para c")
    assumptions_and_constraints: str = Field(description="Fig. 3 para e")
    expected_outputs: str = Field(description="Fig. 3 para f, second sentence")


class HarmfulEvent(Strict):
    he_id: str = Field(pattern=r"^he_[a-z0-9_]+$")
    problem_set_id: str
    statement: str = Field(description="the harmful event phrase used in the Fig. 11 [harmful event] slot")
    thing_of_value_id: str = Field(description="FK objectives")
    risk_type: V.RiskType
    risk_subset: Optional[V.RiskSubset] = None
    strategic_value: Optional[V.StrategicValue] = None
    damage_degree: Optional[V.DamageDegree] = None
    fig28_row: Optional[str] = None
    fig28_cell: Optional[V.CLevel] = Field(default=None, description="MR only: the Fig. 28 cell (column) of fig28_row the assessor expects; MR consequence level")
    base_p: float = Field(gt=0.0, lt=1.0, description="baseline probability before drivers and cascade")
    condition: V.HarmCondition
    posture_subject_ids: list[str] = Field(default_factory=list, description="Blue entities whose posture_state claims decide the forced choice (JRAM Encl. C §4.d)")
    beneficial_counterpart_he_id: Optional[str] = None
    beneficial_statement: Optional[str] = Field(default=None, description="for opportunity statements (Fig. 12): the beneficial event phrase; set on the counterpart")
    key_actions: Optional[str] = Field(default=None, description="Fig. 12 [key actions/conditions] slot")

    @model_validator(mode="after")
    def _type_fields(self):
        if self.risk_type == "MSR":
            if not (self.strategic_value and self.damage_degree):
                raise ValueError("MSR rows need strategic_value and damage_degree (invariant 18)")
        else:
            if not (self.risk_subset and self.fig28_row and self.fig28_cell):
                raise ValueError("MR rows need risk_subset, fig28_row and fig28_cell (invariant 18)")
            if self.fig28_row not in V.FIG28_ROWS[self.risk_subset]:
                raise ValueError(f"fig28_row {self.fig28_row!r} is not a Fig. 28 row for subset {self.risk_subset}")
        return self


class RiskSource(Strict):
    rs_id: str = Field(pattern=r"^rs_[a-z0-9_]+$")
    he_id: str
    source_kind: V.SourceKind
    entity_id: str
    description: str


class RiskDriver(Strict):
    driver_id: str = Field(pattern=r"^rd_[a-z0-9_]+$")
    he_id: str
    claim_subject_id: str
    claim_predicate: V.Predicate
    driver_kind: V.DriverKind
    locus: V.DriverLocus
    op: V.CmpOp
    value: Any = None
    delta: float = Field(ge=-1.0, le=1.0, description="added to P_raw when the current approved claim satisfies (op, value)")
    horizons: list[Literal["near", "mid", "long"]] = Field(default_factory=lambda: ["near", "mid", "long"])
    label: str = Field(description="short phrase for the Fig. 11 [key drivers] slot")


class RiskAssessment(Strict):
    he_id: str
    jsps_horizon: Literal["near", "mid", "long"]
    world_version: int
    p_raw: float = Field(ge=0.0, le=1.0)
    p_level: V.PLevel
    forced_choice_applied: bool = False
    posture_rationale: Optional[str] = None
    dominant_driver_id: Optional[str] = None
    active_driver_ids: list[str] = Field(default_factory=list)
    c_level: V.CLevel
    risk_level: V.RiskLevel
    trend: V.Trend
    statement_text: str

    @model_validator(mode="after")
    def _forced_choice_rationale(self):
        if self.forced_choice_applied and not self.posture_rationale:
            raise ValueError("forced-choice rows need posture_rationale (invariant 19)")
        return self


class ProblemSetAssessment(Strict):
    problem_set_id: str
    jsps_horizon: Literal["near", "mid", "long"]
    world_version: int
    max_risk_level: V.RiskLevel
    he_ids: list[str]
    aggregated_statement_text: str = Field(description="JRAM Fig. 5 aggregated (complex) risk statement")


class EscalationEdge(Strict):
    edge_id: str = Field(pattern=r"^ee_[a-z0-9_]+$")
    from_he_id: str
    to_he_id: str
    lift: float = Field(ge=0.0, le=1.0)
    mechanism: str
    evidence_claim_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- collection (JP 2-01)
class Pir(Strict):
    pir_id: str = Field(pattern=r"^pir_[a-z0-9_]+$")
    statement: str
    commander_role: str
    priority_rank: int = Field(ge=1)
    decision_point_ids: list[str] = Field(default_factory=list)


class CollectionRequirement(Strict):
    req_id: str = Field(pattern=r"^req_[a-z0-9_]+$")
    pir_id: str
    eei: str
    indicators: list[str]
    sir: str
    gap_type: V.GapType
    subject_id: str
    predicate: V.Predicate
    assumption_id: Optional[str] = Field(default=None, description="assumption whose grounding claim this gap resolves (priority = EVPI_k)")
    rfi_disposition: V.RfiDisposition
    routing: str = Field(pattern=r"^(JIOC|JCMB|.+ J-2)$")
    ltiov: date
    created_at: date
    status: V.ReqStatus
    answered_by_source_id: Optional[str] = None
    # computed
    priority: Optional[float] = Field(default=None, ge=0.0)
    jipcl_rank: Optional[int] = Field(default=None, ge=1)


# ---------------------------------------------------------------- inject manifest
class ChangeEvent(Strict):
    fact_id_old: Optional[str]
    fact_id_new: str
    subject_id: str
    predicate: V.Predicate
    old_value: Value = None
    new_value: Value = None


class AssumptionChange(Strict):
    assumption_id: str
    from_status: str = Field(alias="from")
    to_status: str = Field(alias="to")
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class StrategyRestated(Strict):
    strategy_id: str
    value_before: float
    value_after: float
    status_before: str
    status_after: str


class ProblemSetMoved(Strict):
    problem_set_id: str
    jsps_horizon: str
    level_before: str
    level_after: str


class RiskAssessmentChanged(Strict):
    he_id: str
    horizon: str
    level_before: str
    level_after: str
    trend_after: str
    p_before: float
    p_after: float


class ValidityChanged(Strict):
    strategy_id: str
    test: V.ValidityTest
    before: bool
    after: bool


class JipclChanged(Strict):
    req_id: str
    rank_before: Optional[int]
    rank_after: Optional[int]
    status_before: str
    status_after: str


class ExpectedEffects(Strict):
    assumptions_changed: list[AssumptionChange]
    strategies_restated: list[StrategyRestated]
    ranking_before: list[str]
    ranking_after: list[str]
    requirements_closed: list[str]
    problem_sets_moved: list[ProblemSetMoved]
    risk_assessments_changed: list[RiskAssessmentChanged]
    validity_changed: list[ValidityChanged]
    jipcl_changed: list[JipclChanged]


class Manifest(Strict):
    batch: int = Field(ge=1, le=3)
    as_of: date
    docs: list[str]
    change_events: list[ChangeEvent]
    expected_effects: ExpectedEffects


# ---------------------------------------------------------------- registry
@dataclass
class TableSpec:
    name: str
    model: type[BaseModel]
    pk: list[str]
    purpose: str
    fks: dict[str, str] = field(default_factory=dict)
    computed: list[str] = field(default_factory=list)
    truth_only: bool = False
    polymorphic_fks: dict[str, str] = field(default_factory=dict)


TABLES: list[TableSpec] = [
    TableSpec("sources", Source, ["source_id"], "L0 provenance: every rendered document/product with reliability, credibility, batch and perturbations."),
    TableSpec("entities", Entity, ["entity_id"], "Named things claims are about.", fks={"parent_id": "entities.entity_id"}),
    TableSpec("claims", Claim, ["claim_id"], "The world model (L3): sourced, bitemporal, ICD 203-typed assertions extracted from documents.",
              fks={"subject_id": "entities.entity_id", "object_id": "entities.entity_id", "source_id": "sources.source_id", "supersedes_claim_id": "claims.claim_id", "truth_claim_id": "facts.fact_id"},
              computed=["confidence"]),
    TableSpec("facts", Fact, ["fact_id"], "truth/ only: the canonical world documents are rendered from; change events are supersedes_fact_id pairs.",
              fks={"subject_id": "entities.entity_id", "object_id": "entities.entity_id", "supersedes_fact_id": "facts.fact_id"}, computed=["confidence"], truth_only=True),
    TableSpec("guidance", Guidance, ["guidance_id"], "JSPS products (real product types, fictional content) and their nesting.",
              fks={"parent_guidance_id": "guidance.guidance_id", "source_id": "sources.source_id"}),
    TableSpec("games", Game, ["game_id"], "Game form G = <N, S, A, T, O, H>: the operational environment, not the strategy."),
    TableSpec("actions", Action, ["action_id"], "Tactics A_i: named, costed, preconditioned.", fks={"game_id": "games.game_id", "actor_id": "entities.entity_id"}),
    TableSpec("objectives", Objective, ["objective_id"], "Ends U: end states, objectives, effects (JP 5-0 Fig. IV-9).",
              fks={"game_id": "games.game_id", "actor_id": "entities.entity_id", "guidance_id": "guidance.guidance_id", "parent_objective_id": "objectives.objective_id"}),
    TableSpec("resources", Resource, ["resource_id"], "Means M resource types.", fks={"game_id": "games.game_id"}),
    TableSpec("strategies", Strategy, ["strategy_id"], "A strategy sigma = <U, Pi, M, Theta, Sigma_-i, rho>; a JP 5-0 COA nested in the JSPS.",
              fks={"game_id": "games.game_id", "actor_id": "entities.entity_id", "guidance_source": "guidance.guidance_id", "end_state_objective_id": "objectives.objective_id", "opponent_model_id": "opponent_models.opponent_model_id"},
              computed=["validity", "status", "aspiration", "value", "value_ci", "robustness", "world_version"]),
    TableSpec("strategy_objectives", StrategyObjective, ["strategy_id", "objective_id"], "Weight vector w = COA evaluation criteria weights (JP 5-0 App. F).",
              fks={"strategy_id": "strategies.strategy_id", "objective_id": "objectives.objective_id"}, computed=["rating_1_to_3"]),
    TableSpec("strategy_resources", StrategyResource, ["strategy_id", "resource_id"], "Budget m.", fks={"strategy_id": "strategies.strategy_id", "resource_id": "resources.resource_id"}),
    TableSpec("policy_rules", PolicyRule, ["rule_id"], "Policy Pi: ordered (condition, action, probability) rules; the condition is the information set.",
              fks={"strategy_id": "strategies.strategy_id", "action_id": "actions.action_id", "decision_point_id": "decision_points.dp_id"}),
    TableSpec("decision_points", DecisionPoint, ["dp_id"], "Decision points with their branch rules (JP 5-0 Ch. IV).", fks={"strategy_id": "strategies.strategy_id", "pir_id": "pirs.pir_id"}),
    TableSpec("opponent_models", OpponentModel, ["opponent_model_id"], "Sigma_-i: distribution over the opponent's strategies.", fks={"actor_id": "entities.entity_id"}),
    TableSpec("payoffs", Payoff, ["strategy_id", "opponent_strategy_id", "world"], "truth/: the finite Bayesian game payoff tensor u(sigma_i, sigma_-i, theta).",
              fks={"strategy_id": "strategies.strategy_id", "opponent_strategy_id": "strategies.strategy_id"}, truth_only=True),
    TableSpec("distinguishability", Distinguishability, ["strategy_a", "strategy_b"], "COMPUTED pairwise JP 5-0 distinguishability dimensions.",
              fks={"strategy_a": "strategies.strategy_id", "strategy_b": "strategies.strategy_id"}, computed=["dims_differing", "pass"]),
    TableSpec("assumptions", Assumption, ["assumption_id"], "Theta: planning assumptions as predicates over world-model claims.",
              fks={"strategy_id": "strategies.strategy_id", "subject_id": "entities.entity_id"}, computed=["p_holds", "status", "sensitivity", "evpi"]),
    TableSpec("dependencies", Dependency, ["edge_id"], "Typed dependency graph over claims, assumptions, strategies, actions, objectives, harmful events.",
              polymorphic_fks={"from_id": "from_type", "to_id": "to_type"}),
    TableSpec("problem_sets", ProblemSet, ["problem_set_id"], "JRAM tier-0 problem sets with their risk context statement fields.",
              fks={"entity_id": "entities.entity_id", "risk_context_source_id": "sources.source_id"}),
    TableSpec("harmful_events", HarmfulEvent, ["he_id"], "JRAM harmful events (Pillar 1) with consequence inputs.",
              fks={"problem_set_id": "problem_sets.problem_set_id", "thing_of_value_id": "objectives.objective_id", "beneficial_counterpart_he_id": "harmful_events.he_id"}),
    TableSpec("risk_sources", RiskSource, ["rs_id"], "Sources of risk: threats and hazards.", fks={"he_id": "harmful_events.he_id", "entity_id": "entities.entity_id"}),
    TableSpec("risk_drivers", RiskDriver, ["driver_id"], "Drivers of risk: claim terms that move P_raw.", fks={"he_id": "harmful_events.he_id", "claim_subject_id": "entities.entity_id"}),
    TableSpec("risk_assessments", RiskAssessment, ["he_id", "jsps_horizon", "world_version"], "COMPUTED Pillar-2 assessment per harmful event per horizon, with Fig. 11 statement.",
              fks={"he_id": "harmful_events.he_id", "dominant_driver_id": "risk_drivers.driver_id"},
              computed=["p_raw", "p_level", "forced_choice_applied", "posture_rationale", "dominant_driver_id", "active_driver_ids", "c_level", "risk_level", "trend", "statement_text"]),
    TableSpec("problem_set_assessments", ProblemSetAssessment, ["problem_set_id", "jsps_horizon", "world_version"], "COMPUTED aggregated (Fig. 5) risk per problem set per horizon.",
              fks={"problem_set_id": "problem_sets.problem_set_id"}, computed=["max_risk_level", "he_ids", "aggregated_statement_text"]),
    TableSpec("escalation_edges", EscalationEdge, ["edge_id"], "Cascade DAG between harmful events with conditional lift.", fks={"from_he_id": "harmful_events.he_id", "to_he_id": "harmful_events.he_id"}),
    TableSpec("pirs", Pir, ["pir_id"], "Priority intelligence requirements (JP 2-01 Ch. III §5.a)."),
    TableSpec("collection_requirements", CollectionRequirement, ["req_id"], "Gaps as JP 2-01 collection requirements with computed EVPI priority and JIPCL rank.",
              fks={"pir_id": "pirs.pir_id", "subject_id": "entities.entity_id", "assumption_id": "assumptions.assumption_id", "answered_by_source_id": "sources.source_id"},
              computed=["priority", "jipcl_rank"]),
]

MANIFEST_MODEL = Manifest
TABLE_BY_NAME = {t.name: t for t in TABLES}
