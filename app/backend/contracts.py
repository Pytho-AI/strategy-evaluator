"""Typed API responses.

Every number in these models is either a column the loader recomputed or the return value
of a function in ``dataset/eval``. Nothing is hand-entered and no formula is copied.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_serializer

ADVERSARY_RANGE = (
    "dataset value_ci: the min/max expected value across the adversary COAs in the "
    "opponent model. Not a statistical confidence interval and not a casualty estimate."
)


class DatasetIdentityView(BaseModel):
    """What the batch cache is keyed on."""

    archive_sha256: str | None = Field(description="SHA-256 of the frozen dataset archive")
    git_head: str | None = Field(description="git HEAD of the dataset checkout, if any")
    key: str = Field(description="cache key component: <archive sha>:<git head>")


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    ok: bool
    dataset: DatasetIdentityView
    load_ms: float = Field(
        description="milliseconds of the load that filled the batch-0 cache entry"
    )


class BatchMeta(BaseModel):
    batch: int
    as_of: str
    table_counts: dict[str, int]


class WorldsMeta(BaseModel):
    blue_worlds: int = Field(
        description="theta-assignments over the Blue actor's K assumptions"
    )
    distinct_world_labels: int = Field(
        description="distinct payoffs.world label strings across every actor"
    )
    note: str


class MetaResponse(BaseModel):
    product_name: str
    dataset_name: str
    marking: str
    dataset: DatasetIdentityView
    batches: list[BatchMeta]
    worlds: WorldsMeta


class InjectManifestView(BaseModel):
    batch: int
    as_of: str
    docs: list[str]
    change_events: list[dict[str, Any]]
    expected_effects: dict[str, Any]


class InjectsResponse(BaseModel):
    injects: list[InjectManifestView]


# The overlay keys. They are present only when a workspace's accepted claims were merged
# into the evaluation; with an empty workspace the response is exactly the replay response.
OVERLAY_KEYS = (
    "overlay_applied", "workspace", "graph_version", "product_claim_ids", "batch_as_of",
)


def _without_unset(data: dict, keys: tuple[str, ...], present: str) -> dict:
    if not data.get(present):
        for key in keys:
            data.pop(key, None)
    return data


class Envelope(BaseModel):
    """What every batch-scoped response carries.

    ``as_of`` is the date the evaluation ran at. With an overlay applied it can be later than
    the batch's own date, which is then served as ``batch_as_of``.
    """

    batch: int
    as_of: str
    marking: str
    load_ms: float = Field(description="milliseconds of the load that filled the cache")
    response_ms: float = Field(description="milliseconds spent serving this request")
    overlay_applied: bool | None = Field(
        default=None,
        description="present only when a workspace's accepted claims were evaluated",
    )
    workspace: str | None = None
    graph_version: int | None = Field(
        default=None, description="the workspace's accepted-claim graph version"
    )
    product_claim_ids: list[str] | None = Field(
        default=None, description="accepted product claims merged into this evaluation"
    )
    batch_as_of: str | None = Field(
        default=None, description="the batch's own as-of date, when the overlay moved it"
    )

    @model_serializer(mode="wrap")
    def _hide_overlay_when_unapplied(self, handler):
        return _without_unset(handler(self), OVERLAY_KEYS, "overlay_applied")


# ---------------------------------------------------------------- strategies
class ValidityTestView(BaseModel):
    test: str
    passed: bool
    evidence: str


class StrategyView(BaseModel):
    """The comparison row: what the snapshot lists for every strategy."""

    strategy_id: str
    game_id: str
    actor_id: str
    name: str
    status: str
    value: float
    adversary_range: list[float] = Field(description=ADVERSARY_RANGE)
    robustness: float
    validity: list[ValidityTestView]


class RankingView(BaseModel):
    game_id: str
    actor_id: str
    strategy_ids: list[str] = Field(description="valid strategies, best value first")


class AssumptionView(BaseModel):
    assumption_id: str
    strategy_id: str
    index_k: int
    statement: str
    status: str
    p_holds: float
    sensitivity: float | None
    evpi: float | None
    subject_id: str
    subject_name: str | None
    predicate: str
    tolerance_op: str
    tolerance_value: Any
    role: str
    origin: str = Field(description="JP 5-0: higher_hq or own")
    jp50_logical: bool
    jp50_realistic: bool
    jp50_essential: bool
    in_decision_matrix: bool


class ProblemSetAssessmentView(BaseModel):
    problem_set_id: str
    jsps_horizon: str
    max_risk_level: str
    he_ids: list[str]
    aggregated_statement_text: str


class CollectionRequirementView(BaseModel):
    req_id: str
    status: str
    priority: float | None
    jipcl_rank: int | None


class StrategyObjectiveView(BaseModel):
    objective_id: str
    name: str
    kind: str
    weight: float = Field(description="w_k: the strategy's weight on this objective")
    rating_1_to_3: int | None = Field(
        description="JP 5-0 App. F rank of E[u_k] among the actor's valid strategies"
    )
    expected_contribution: float = Field(
        description="E[u_k]: eval.value.value with a one-hot weight vector"
    )
    aspiration: float | None


class ResourceUseView(BaseModel):
    resource_id: str
    name: str
    unit: str
    budget: float
    worst_case_use: float = Field(
        description="eval.validity.worst_case_cost: the costliest trajectory the policy allows"
    )
    within_budget: bool


class ChainEdgeView(BaseModel):
    edge_id: str
    kind: str
    mechanism: str
    from_type: str
    from_id: str
    from_name: str
    to_type: str
    to_id: str
    to_name: str
    basis: str = Field(
        default="dependency_edge",
        description=(
            "'dependency_edge' for an edge in the frozen dependencies table; "
            "'current_evidence' for a link derived the way the evaluator selects "
            "evidence at this batch's as_of date"
        ),
    )


class HorizonRiskView(BaseModel):
    jsps_horizon: str
    risk_level: str
    trend: str
    p_level: str
    c_level: str
    p_raw: float


class HarmfulEventRefView(BaseModel):
    he_id: str
    statement: str
    problem_set_id: str
    problem_set_name: str | None
    risk_type: str
    horizons: list[HorizonRiskView]


class DecisionPointView(BaseModel):
    dp_id: str
    name: str
    latest_period: int | None
    branch_rule_ids: list[str]
    pir_id: str | None
    pir_statement: str | None


class AdversaryCoaView(BaseModel):
    strategy_id: str
    name: str
    summary: str
    adversary_coa_label: str | None = Field(
        description="JP 5-0: most_likely, most_dangerous or alternative"
    )
    probability: float


class OpponentModelView(BaseModel):
    opponent_model_id: str
    actor_id: str
    actor_name: str | None
    coas: list[AdversaryCoaView]


class StrategyDetailView(BaseModel):
    """One option, side by side with the others."""

    strategy_id: str
    game_id: str
    actor_id: str
    name: str
    summary: str
    echelon: str
    status: str
    gate_failed: str | None = Field(
        description="the validity test that made this option invalid, if any"
    )
    gates_failed: list[str]
    validity: list[ValidityTestView]
    value: float
    adversary_range: list[float] = Field(description=ADVERSARY_RANGE)
    robustness: float
    aspiration: float
    risk_functional: str
    risk_alpha: float | None
    objectives: list[StrategyObjectiveView]
    assumptions: list[AssumptionView]
    resources: list[ResourceUseView]
    theory_of_victory: list[ChainEdgeView]
    constraints: list[str] = Field(description="JP 5-0 'must do'")
    restraints: list[str] = Field(description="JP 5-0 'cannot do'")
    mitigated_harmful_events: list[HarmfulEventRefView]
    unmitigated_harmful_events: list[HarmfulEventRefView]
    decision_points: list[DecisionPointView]
    opponent_model: OpponentModelView
    mission_who: str
    mission_what: str
    mission_when: str
    mission_where: str
    mission_why: str
    main_effort: str
    sequencing: str
    reserve_policy: str
    task_org: list[str]
    task_org_names: list[str]


class StrategiesResponse(Envelope):
    caution: str
    ranking: list[str]
    strategies: list[StrategyDetailView]


class StrategyDetailResponse(Envelope):
    caution: str
    ranking: list[str]
    strategy: StrategyDetailView


# ---------------------------------------------------------------- decision overview
class CriterionView(BaseModel):
    objective_id: str
    name: str
    weight: float
    rating_1_to_3: int | None
    contribution: float
    runner_up_contribution: float | None
    runner_up_rating: int | None


class TradeoffView(BaseModel):
    runner_up_id: str
    runner_up_name: str
    value_gap: float = Field(description="recommended value minus runner-up value")
    objectives_favouring_runner_up: list[CriterionView]


class RecommendedView(BaseModel):
    strategy_id: str
    name: str
    status: str
    value: float
    adversary_range: list[float] = Field(description=ADVERSARY_RANGE)
    robustness: float
    risk_functional: str
    risk_alpha: float | None


class WhyView(BaseModel):
    winning_criteria: list[CriterionView]
    validity_evidence: list[ValidityTestView]
    tradeoff: TradeoffView | None


class RiskHighlightView(BaseModel):
    he_id: str
    statement: str
    problem_set_id: str
    problem_set_name: str | None
    jsps_horizon: str
    risk_level: str
    trend: str
    p_level: str
    c_level: str


class PriorityBasisView(BaseModel):
    basis: str = Field(description="'evpi' or 'fallback'")
    assumption_id: str | None
    evpi: float | None
    claim_id: str | None
    confidence: float | None
    degree: int | None = Field(
        description="fallback basis: the claim's degree in the dependency graph"
    )


class AssetCandidateView(BaseModel):
    asset_id: str
    name: str
    owner_org: str
    discipline: str
    p_success: float
    latency_periods: int
    range_ok: bool
    timeliness_ok: bool
    target_characteristics_match: bool
    capacity_per_period: int
    cost_per_task: float


class AuthorityView(BaseModel):
    tier_id: str
    name: str
    approver_role: str
    recommendation_type: str
    risk_level_threshold: str


class SourceView(BaseModel):
    source_id: str
    title: str
    path: str = Field(description="path under dataset/ the claim was extracted from")
    doc_type: str | None = None
    author_org: str | None = None
    reliability: str | None = Field(default=None, description="source reliability A–F")
    credibility: str | None = Field(default=None, description="information credibility 1–6")
    published_at: str | None = None
    batch: int | None = None


class StrategyRefView(BaseModel):
    strategy_id: str
    name: str
    status: str


class RequirementStatusChangeView(BaseModel):
    status: str
    actor: str
    at: str
    reason: str | None = None


class ProductRequirementView(BaseModel):
    """The product-owned half of a ``preq_`` requirement. Absent on dataset replay rows."""

    strategy_question: str | None
    strategy_id: str | None
    gap_reason: str
    proposed_owner: str
    required_evidence: str
    authority_tier_id: str | None
    satisfied_by_claim_id: str | None
    created_actual_at: str
    created_by: str
    status_history: list[RequirementStatusChangeView]


class RequirementView(BaseModel):
    req_id: str
    pir_id: str
    pir_statement: str | None
    pir_priority_rank: int | None
    commander_role: str | None
    eei: str
    indicators: list[str]
    sir: str
    gap_type: str
    status: str
    ltiov: str
    created_at: str
    routing: str
    routing_authority: AuthorityView | None
    rfi_disposition: str
    subject_id: str
    subject_name: str | None
    predicate: str
    priority: float | None
    priority_basis: PriorityBasisView | None
    jipcl_rank: int | None
    closure_basis: str | None = Field(
        description="'manifest_replay' when the loader closed it from a batch manifest"
    )
    answered_by_source: SourceView | None
    assumption: AssumptionView | None
    affected_strategies: list[StrategyRefView]
    candidate_assets: list[AssetCandidateView]
    disciplines: list[str]
    owner: str | None = Field(
        default=None,
        description="'product' on requirements this workspace raised; absent on dataset rows",
    )
    product: ProductRequirementView | None = None

    @model_serializer(mode="wrap")
    def _hide_product_when_dataset(self, handler):
        return _without_unset(handler(self), ("owner", "product"), "owner")


class DecisionOverviewView(BaseModel):
    scenario_id: str
    scenario_name: str
    friendly_force_id: str
    friendly_force_name: str
    adversary_id: str
    adversary_name: str
    as_of: str
    batch: int
    marking: str
    caution: str = Field(description="JP 5-0 App. F caution (eval.style_check.CAUTION)")
    ranking: list[str]
    recommended: RecommendedView | None
    why: WhyView | None
    highest_sensitivity_assumptions: list[AssumptionView]
    top_collection_requirement: RequirementView | None
    highest_risks: list[RiskHighlightView]
    problem_sets_at_highest_level: list[ProblemSetAssessmentView]


class SnapshotResponse(Envelope):
    decision_overview: DecisionOverviewView
    strategies: list[StrategyView]
    rankings: list[RankingView]
    assumptions: list[AssumptionView]
    problem_set_assessments: list[ProblemSetAssessmentView]
    collection_requirements: list[CollectionRequirementView]


class CollectionResponse(Envelope):
    requirements: list[RequirementView]


# ---------------------------------------------------------------- claims
class ClaimFlagsView(BaseModel):
    proposed: bool
    contradiction: bool
    contradicts_claim_ids: list[str]
    stale: bool = Field(description="valid_to is before the batch's as_of date")
    superseded: bool
    superseded_by_claim_id: str | None


class ClaimView(BaseModel):
    claim_id: str
    subject_id: str
    subject_name: str | None
    predicate: str
    object_id: str | None
    object_name: str | None
    value: Any
    value_type: str
    unit: str | None
    valid_from: str
    valid_to: str | None
    asserted_at: str = Field(description="transaction time, distinct from valid time")
    estimative: bool
    likelihood_icd203: str | None
    likelihood_surface_term: str | None
    confidence_icd203: str = Field(description="ICD 203 confidence: low, moderate or high")
    confidence: float = Field(
        description="derived from likelihood and confidence_icd203; not a probability of truth"
    )
    confidence_basis: str
    status: str
    supersedes_claim_id: str | None
    truth_claim_id: str | None
    span_start: int
    span_end: int
    span_text: str | None = Field(description="the exact source excerpt, read from the file")
    source_id: str
    source: SourceView | None
    flags: ClaimFlagsView


class ClaimsResponse(Envelope):
    total: int
    limit: int
    offset: int
    claims: list[ClaimView]


class TraceNodeView(BaseModel):
    type: str
    id: str
    name: str
    status: str | None = Field(
        default=None,
        description="claim nodes: 'superseded' when a later claim supersedes it, else the claim status",
    )


class TracePathView(BaseModel):
    nodes: list[TraceNodeView]
    edges: list[ChainEdgeView]


class ClaimTraceView(BaseModel):
    claim_id: str
    claim_node: TraceNodeView = Field(
        description="the traced claim itself; status is 'superseded' when a later claim replaced it"
    )
    edges: list[ChainEdgeView]
    paths: list[TracePathView] = Field(
        description="source span → claim → assumption or risk driver → strategy or risk"
    )


class ClaimDetailResponse(Envelope):
    claim: ClaimView
    trace: ClaimTraceView


# ---------------------------------------------------------------- risk
class ClaimRefView(BaseModel):
    claim_id: str
    label: str
    value: Any
    status: str
    likelihood_icd203: str | None
    confidence: float
    source_id: str
    source_title: str | None
    reliability: str | None


class RiskDriverView(BaseModel):
    driver_id: str
    driver_kind: str = Field(description="one of the JRAM ten driver considerations")
    locus: str
    label: str
    op: str
    value: Any
    delta: float
    claim_subject_id: str
    claim_subject_name: str | None
    claim_predicate: str
    dominant: bool
    claims: list[ClaimRefView] = Field(description="the approved claims that satisfy the term")


class HorizonAssessmentView(BaseModel):
    jsps_horizon: str
    p_raw: float
    p_level: str
    c_level: str
    risk_level: str
    trend: str
    statement_text: str
    forced_choice_applied: bool
    posture_rationale: str | None
    dominant_driver_id: str | None
    active_drivers: list[RiskDriverView]


class ConsequenceBasisView(BaseModel):
    basis: str = Field(description="'msr' (Fig. 23) or 'mr' (Fig. 28)")
    strategic_value: str | None
    damage_degree: str | None
    fig28_row: str | None
    fig28_cell: str | None


class RiskSourceView(BaseModel):
    rs_id: str
    source_kind: str
    entity_id: str
    entity_name: str | None
    description: str


class EscalationEdgeView(BaseModel):
    edge_id: str
    from_he_id: str
    from_statement: str | None
    to_he_id: str
    to_statement: str | None
    lift: float
    mechanism: str


class CascadeView(BaseModel):
    upstream_paths: list[list[str]] = Field(
        description="chains of harmful events that feed this one, root first"
    )
    upstream_edges: list[EscalationEdgeView]
    downstream_edges: list[EscalationEdgeView]


class HarmfulEventView(BaseModel):
    he_id: str
    problem_set_id: str
    problem_set_name: str | None
    statement: str
    risk_type: str
    risk_subset: str | None
    thing_of_value_id: str
    thing_of_value_name: str | None
    consequence_basis: ConsequenceBasisView
    condition: str
    base_p: float
    posture_subject_ids: list[str]
    posture_subject_names: list[str]
    beneficial_counterpart_he_id: str | None
    beneficial_statement: str | None
    key_actions: str | None
    horizons: list[HorizonAssessmentView]
    sources_of_risk: list[RiskSourceView]
    cascade: CascadeView


class ProblemSetHorizonView(BaseModel):
    jsps_horizon: str
    max_risk_level: str
    he_ids: list[str]
    aggregated_statement_text: str


class ProblemSetView(BaseModel):
    problem_set_id: str
    name: str
    entity_id: str
    tier: int
    thing_of_value_ids: list[str]
    thing_of_value_names: list[str]
    risk_owner_role: str
    tolerance_statement: str
    strategic_context: str
    scope_and_boundaries: str
    assumptions_and_constraints: str
    expected_outputs: str
    risk_context_source: SourceView | None
    horizons: list[ProblemSetHorizonView]


class RisksResponse(Envelope):
    problem_sets: list[ProblemSetView]
    harmful_events: list[HarmfulEventView]
    escalation_edges: list[EscalationEdgeView]


# ---------------------------------------------------------------- inject diff
class AssumptionChangeView(BaseModel):
    """Field names match the manifest's expected_effects.assumptions_changed."""

    model_config = ConfigDict(populate_by_name=True)

    assumption_id: str
    from_status: str = Field(alias="from")
    to: str
    statement: str
    p_holds_before: float
    p_holds_after: float


class ValidityChangeView(BaseModel):
    strategy_id: str
    name: str
    test: str
    before: bool
    after: bool
    evidence_after: str


class StrategyRestatedView(BaseModel):
    strategy_id: str
    name: str
    value_before: float
    value_after: float
    status_before: str
    status_after: str


class RiskChangeView(BaseModel):
    he_id: str
    horizon: str
    level_before: str
    level_after: str
    trend_after: str
    p_before: float
    p_after: float
    statement: str
    trend_before: str
    cascade_paths: list[list[str]] = Field(
        description="upstream chains whose events also changed in this batch"
    )


class ProblemSetMovedView(BaseModel):
    problem_set_id: str
    jsps_horizon: str
    level_before: str
    level_after: str
    name: str


class JipclChangeView(BaseModel):
    req_id: str
    rank_before: int | None
    rank_after: int | None
    status_before: str
    status_after: str
    new: bool = Field(description="the requirement did not exist in the earlier batch")


class EvidenceChangeView(BaseModel):
    claims_added: list[ClaimRefView]
    claims_superseded: list[ClaimRefView] = Field(
        description="claims an added claim supersedes"
    )
    claims_contradicted: list[ClaimRefView] = Field(
        description="added claims that conflict with an approved claim"
    )


class DiffResponse(BaseModel):
    batch: int
    marking: str
    as_of_before: str
    as_of_after: str
    response_ms: float
    evidence: EvidenceChangeView
    assumptions_changed: list[AssumptionChangeView]
    validity_changed: list[ValidityChangeView]
    strategies_restated: list[StrategyRestatedView]
    ranking_before: list[str]
    ranking_after: list[str]
    risk_assessments_changed: list[RiskChangeView]
    problem_sets_moved: list[ProblemSetMovedView]
    requirements_closed: list[str]
    jipcl_changed: list[JipclChangeView]


# ---------------------------------------------------------------- product: reports
class ProposedClaimFlagView(BaseModel):
    """Why a proposed claim still needs a reviewer."""

    flag: str
    note: str | None = None


class ProposedClaimView(BaseModel):
    """One extracted claim, exactly as the report states it. Nothing is filled in."""

    claim_id: str
    report_id: str
    status: str = Field(description="proposed, approved or rejected in this workspace")
    subject_id: str | None
    subject_name: str | None
    predicate: str
    object_id: str | None
    object_name: str | None
    value: Any
    value_type: str
    unit: str | None
    valid_from: str | None
    valid_to: str | None
    asserted_at: str | None
    estimative: bool
    likelihood_icd203: str | None
    likelihood_surface_term: str | None
    confidence_icd203: str | None
    confidence: float | None = Field(
        default=None, description="eval.value.derived_confidence; null until confidence is known"
    )
    span_start: int
    span_end: int
    span_text: str = Field(description="the exact [span_start, span_end) slice of the report")
    flags: list[str]
    notes: list[str]
    contradicts: list[str] = []
    contradicts_reason: str | None = None
    accepted_graph_version: int | None = None


class InstructionLikeSpanView(BaseModel):
    """A sentence that reads as an instruction. Recorded as data; it produces no claim."""

    span_start: int
    span_end: int
    text: str


class ReportView(BaseModel):
    report_id: str
    filename: str
    format: str
    sha256: str
    uploaded_at: str
    actor: str
    report_date: str | None
    source_id: str
    extractor: str
    text_length: int


class ReportIngestResponse(BaseModel):
    workspace: str
    report: ReportView
    duplicate: bool = Field(
        description="true when this exact sha256 was already ingested: no new claims"
    )
    extractor: str = Field(description="which extractor ran; the offline path is local_rules")
    proposed_claims: list[ProposedClaimView]
    instruction_like_spans: list[InstructionLikeSpanView]
    response_ms: float


class ReportsResponse(BaseModel):
    workspace: str
    reports: list[ReportView]


class ReportDetailResponse(BaseModel):
    workspace: str
    report: ReportView
    text: str
    proposed_claims: list[ProposedClaimView]


# ---------------------------------------------------------------- product: review
class ChangeSetView(BaseModel):
    """What one accepted claim changed, computed from the two evaluations."""

    evidence: EvidenceChangeView
    assumptions_changed: list[AssumptionChangeView]
    validity_changed: list[ValidityChangeView]
    strategies_restated: list[StrategyRestatedView]
    ranking_before: list[str]
    ranking_after: list[str]
    risk_assessments_changed: list[RiskChangeView]
    problem_sets_moved: list[ProblemSetMovedView]
    requirements_closed: list[str]
    jipcl_changed: list[JipclChangeView]


class DecisionView(BaseModel):
    decision_id: str
    target_type: str
    target_id: str
    decision: str
    actor: str
    decided_at: str
    reason: str | None
    revision: dict[str, Any]


class PlanningFlagView(BaseModel):
    object_id: str
    kind: str
    text: str
    review_status: str
    reason: str
    claim_ids: list[str]
    dependent_options: list[str]


class ClaimDecisionResponse(BaseModel):
    workspace: str
    batch: int
    as_of: str = Field(description="the date the new evaluation ran at")
    graph_version: int
    claim: ProposedClaimView
    decision: DecisionView
    changes: ChangeSetView
    contradicts: list[str]
    contradiction_reason: str | None
    chosen_claim_id: str | None = Field(
        description="the claim the as-of selection rule made current for this (subject, predicate)"
    )
    requirements_changed: list[RequirementView]
    planning_flags: list[PlanningFlagView]
    response_ms: float


# ---------------------------------------------------------------- product: planning
class SourceLinkView(BaseModel):
    claim_id: str
    source_id: str | None = None
    source_title: str | None = None
    span_start: int | None = None
    span_end: int | None = None
    span_text: str | None = None


class ValidityWindowView(BaseModel):
    valid_from: str | None = None
    valid_to: str | None = None


class ObjectConfidenceView(BaseModel):
    confidence_icd203: str | None = None
    confidence: float | None = None


class PlanningReviewView(BaseModel):
    review_status: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    reason: str | None = None
    history: list[dict[str, Any]] = []


class PlanningObjectView(BaseModel):
    object_id: str
    kind: str = Field(description="assumption, constraint or restraint")
    strategy_id: str
    text: str
    subject_id: str | None
    predicate: str | None
    status: str | None = Field(description="assumption state; null for constraints/restraints")
    source_links: list[SourceLinkView]
    validity: ValidityWindowView | None
    confidence: ObjectConfidenceView | None
    review_status: str
    provenance: str = Field(
        description="where the source links came from, or that the schema carries none"
    )
    review: PlanningReviewView | None


class PlanningResponse(Envelope):
    objects: list[PlanningObjectView]
    flags: list[PlanningFlagView]


class PlanningReviewResponse(BaseModel):
    workspace: str
    object: PlanningObjectView
    response_ms: float


# ---------------------------------------------------------------- product: collection
class CollectionDraftResponse(BaseModel):
    workspace: str
    batch: int
    requirement: RequirementView
    duplicate_of: str | None = Field(
        default=None,
        description="set when an open requirement already covered this (subject, predicate, gap)",
    )
    decision: DecisionView | None = None
    response_ms: float


class RequirementUpdateResponse(BaseModel):
    workspace: str
    batch: int
    requirement: RequirementView
    response_ms: float


# ---------------------------------------------------------------- product: workspace
class AuditEntryView(BaseModel):
    seq: int
    at: str
    actor: str
    action: str
    target_type: str
    target_id: str
    detail: dict[str, Any]


class WorkspaceResponse(BaseModel):
    workspace: str
    graph_version: int
    state_version: int
    reports: int
    proposed_claims: int
    accepted_claims: int
    rejected_claims: int
    requirements: int
    decisions: int
    reviewed_planning_objects: int
    audit: list[AuditEntryView]


# ---------------------------------------------------------------- product: requests
class ReportIngestRequest(BaseModel):
    """JSON ingestion. Send ``text`` for text/markdown/CSV, ``content_base64`` for a PDF.

    A raw upload is also accepted: POST the file bytes with its own Content-Type and
    ``?filename=``.
    """

    filename: str = Field(description="the original file name; its extension picks the parser")
    actor: str = Field(description="who uploaded it; recorded on the report and in the audit log")
    text: str | None = None
    content_base64: str | None = None
    content_type: str | None = None


class ClaimDecisionRequest(BaseModel):
    decision: str = Field(description="accept or reject")
    actor: str
    reason: str | None = None
    revision: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "reviewer corrections applied before acceptance, recorded with the decision. "
            "Only claim fields: subject_id, predicate, object_id, value, valid_from, "
            "valid_to, asserted_at, estimative, likelihood_icd203, confidence_icd203."
        ),
    )


class CollectionDraftRequest(BaseModel):
    """A draft needs an explicit strategy question or PIR, plus a linked assumption or gap."""

    actor: str
    gap_type: str = Field(description="missing, stale, low_confidence or contradiction")
    required_evidence: str = Field(description="what would answer it; served as the EEI")
    gap_reason: str
    proposed_owner: str
    ltiov: str = Field(description="latest time the information is of value (ISO date)")
    strategy_question: str | None = None
    pir_id: str | None = None
    assumption_id: str | None = None
    subject_id: str | None = None
    predicate: str | None = None
    sir: str = ""
    indicators: list[str] = []


class RouteRequest(BaseModel):
    queue: str = Field(description="JIOC, JCMB or '<unit> J-2'. An internal assignment only.")
    actor: str
    reason: str | None = None


class RequirementStatusRequest(BaseModel):
    status: str = Field(description="research, validation or submission")
    actor: str
    reason: str | None = None


class PlanningReviewRequest(BaseModel):
    review_status: str = Field(
        description="unreviewed, reviewed, needs_review or invalidated"
    )
    actor: str
    reason: str | None = None
    source_links: list[SourceLinkView] | None = None
    validity: ValidityWindowView | None = None


class WorkspaceResetRequest(BaseModel):
    actor: str = "operator"
