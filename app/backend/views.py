"""Builders: one loaded batch (derive.Index) in, typed contracts out.

The routes stay thin; the joins live here. No expected outcome and no eval formula is
written into this module — the manifests are read only by the tests.
"""
from __future__ import annotations

from typing import Any

from .adapter import BLUE_ACTOR_ID, BLUE_GAME_ID, VALIDITY_TESTS
from .branding import MARKING
from .contracts import (
    AdversaryCoaView,
    AssetCandidateView,
    AssumptionChangeView,
    AssumptionView,
    AuthorityView,
    CascadeView,
    ChainEdgeView,
    ClaimFlagsView,
    ClaimRefView,
    ClaimTraceView,
    ClaimView,
    ConsequenceBasisView,
    CriterionView,
    DecisionOverviewView,
    DecisionPointView,
    EscalationEdgeView,
    EvidenceChangeView,
    HarmfulEventRefView,
    HarmfulEventView,
    HorizonAssessmentView,
    HorizonRiskView,
    JipclChangeView,
    InstructionLikeSpanView,
    ObjectConfidenceView,
    OpponentModelView,
    PlanningFlagView,
    PlanningObjectView,
    PlanningReviewView,
    PriorityBasisView,
    ProductRequirementView,
    ProposedClaimView,
    ProblemSetAssessmentView,
    ProblemSetHorizonView,
    ProblemSetMovedView,
    ProblemSetView,
    RecommendedView,
    ReportView,
    RequirementStatusChangeView,
    RequirementView,
    ResourceUseView,
    RiskChangeView,
    RiskDriverView,
    RiskHighlightView,
    RiskSourceView,
    SourceView,
    StrategyDetailView,
    StrategyObjectiveView,
    StrategyRefView,
    SourceLinkView,
    StrategyRestatedView,
    StrategyView,
    TraceNodeView,
    TracePathView,
    ValidityWindowView,
    ValidityChangeView,
    ValidityTestView,
)
from .derive import HORIZONS, Index, caution

# The requirement statuses that close a collection requirement (JP 2-01 Ch. III §13.a).
CLOSED_STATUSES = ("satisfaction", "closed")
CONFIDENCE_BASIS = (
    "derived from the claim's ICD 203 likelihood band and confidence level "
    "(SCHEMA.md §1); it is not a probability that the claim is true"
)


def blue_strategy_ids(
    index: Index, game_id: str = BLUE_GAME_ID, actor_id: str = BLUE_ACTOR_ID
) -> list[str]:
    """The friendly options of one scenario's game.

    The defaults are Meridian's Blue player; the RPS game in that dataset is a test fixture,
    never an option. A scenario package names its own pair through GAME_ID / ACTOR_ID.
    """
    return sorted(
        s["strategy_id"]
        for s in index.rows("strategies")
        if (s["game_id"], s["actor_id"]) == (game_id, actor_id)
    )


# ---------------------------------------------------------------- strategies
def strategy_view(row: dict) -> StrategyView:
    return StrategyView(
        strategy_id=row["strategy_id"],
        game_id=row["game_id"],
        actor_id=row["actor_id"],
        name=row["name"],
        status=row["status"],
        value=row["value"],
        adversary_range=row["value_ci"],
        robustness=row["robustness"],
        validity=validity_views(row),
    )


def validity_views(row: dict) -> list[ValidityTestView]:
    return [
        ValidityTestView(
            test=name,
            passed=row["validity"][name]["pass"],
            evidence=row["validity"][name]["evidence"],
        )
        for name in VALIDITY_TESTS
    ]


def gates_failed(row: dict) -> list[str]:
    return [name for name in VALIDITY_TESTS if not row["validity"][name]["pass"]]


def assumption_view(index: Index, row: dict) -> AssumptionView:
    return AssumptionView(
        assumption_id=row["assumption_id"],
        strategy_id=row["strategy_id"],
        index_k=row["index_k"],
        statement=row["statement"],
        status=row["status"],
        p_holds=row["p_holds"],
        sensitivity=row["sensitivity"],
        evpi=row["evpi"],
        subject_id=row["subject_id"],
        subject_name=index.entity_name(row["subject_id"]),
        predicate=row["predicate"],
        tolerance_op=row["tolerance"]["op"],
        tolerance_value=row["tolerance"].get("value"),
        role=row["role"],
        origin=row["origin"],
        jp50_logical=row["jp50_logical"],
        jp50_realistic=row["jp50_realistic"],
        jp50_essential=row["jp50_essential"],
        in_decision_matrix=row["in_decision_matrix"],
    )


def _horizon_risk(index: Index, he_id: str) -> list[HorizonRiskView]:
    out = []
    for horizon in HORIZONS:
        row = index.risk_rows.get((he_id, horizon))
        if row is None:
            continue
        out.append(
            HorizonRiskView(
                jsps_horizon=horizon,
                risk_level=row["risk_level"],
                trend=row["trend"],
                p_level=row["p_level"],
                c_level=row["c_level"],
                p_raw=row["p_raw"],
            )
        )
    return out


def _harmful_event_ref(index: Index, he: dict) -> HarmfulEventRefView:
    problem_set = index.problem_sets.get(he["problem_set_id"])
    return HarmfulEventRefView(
        he_id=he["he_id"],
        statement=he["statement"],
        problem_set_id=he["problem_set_id"],
        problem_set_name=problem_set["name"] if problem_set else None,
        risk_type=he["risk_type"],
        horizons=_horizon_risk(index, he["he_id"]),
    )


def _chain_edge(index: Index, edge: dict) -> ChainEdgeView:
    return ChainEdgeView(
        edge_id=edge["edge_id"],
        kind=edge["kind"],
        mechanism=edge["mechanism"],
        from_type=edge["from_type"],
        from_id=edge["from_id"],
        from_name=index.display_name(edge["from_type"], edge["from_id"]),
        to_type=edge["to_type"],
        to_id=edge["to_id"],
        to_name=index.display_name(edge["to_type"], edge["to_id"]),
        basis=edge.get("basis", "dependency_edge"),
    )


def strategy_detail(index: Index, strategy_id: str) -> StrategyDetailView:
    row = index.strategies[strategy_id]
    contributions = index.contributions(strategy_id)
    objectives = index.objectives
    weights = [
        so
        for so in index.rows("strategy_objectives")
        if so["strategy_id"] == strategy_id
    ]
    budgets = {
        sr["resource_id"]: sr["budget"]
        for sr in index.rows("strategy_resources")
        if sr["strategy_id"] == strategy_id
    }
    used = index.worst_case_cost(strategy_id)
    resources = index.by("resources", "resource_id")
    edges = index.by("dependencies", "edge_id")
    pirs = index.by("pirs", "pir_id")
    mitigates = set(row.get("mitigates_he_ids") or [])
    opponent_model = next(
        om
        for om in index.rows("opponent_models")
        if om["opponent_model_id"] == row["opponent_model_id"]
    )
    failed = gates_failed(row)
    return StrategyDetailView(
        strategy_id=strategy_id,
        game_id=row["game_id"],
        actor_id=row["actor_id"],
        name=row["name"],
        summary=row["summary"],
        echelon=row["echelon"],
        status=row["status"],
        gate_failed=failed[0] if failed else None,
        gates_failed=failed,
        validity=validity_views(row),
        value=row["value"],
        adversary_range=row["value_ci"],
        robustness=row["robustness"],
        aspiration=row["aspiration"],
        risk_functional=row["risk_functional"],
        risk_alpha=row["risk_alpha"],
        objectives=[
            StrategyObjectiveView(
                objective_id=so["objective_id"],
                name=objectives[so["objective_id"]]["name"],
                kind=objectives[so["objective_id"]]["kind"],
                weight=so["weight"],
                rating_1_to_3=so.get("rating_1_to_3"),
                expected_contribution=contributions.get(so["objective_id"], 0.0),
                aspiration=objectives[so["objective_id"]].get("aspiration"),
            )
            for so in sorted(weights, key=lambda so: so["objective_id"])
        ],
        assumptions=[
            assumption_view(index, a)
            for a in sorted(
                (a for a in index.rows("assumptions") if a["strategy_id"] == strategy_id),
                key=lambda a: a["index_k"],
            )
        ],
        resources=[
            ResourceUseView(
                resource_id=resource_id,
                name=resources[resource_id]["name"],
                unit=resources[resource_id]["unit"],
                budget=budgets.get(resource_id, 0.0),
                worst_case_use=used.get(resource_id, 0.0),
                within_budget=used.get(resource_id, 0.0) <= budgets.get(resource_id, 0.0),
            )
            for resource_id in sorted(set(budgets) | set(used))
        ],
        theory_of_victory=[
            _chain_edge(index, edges[edge_id])
            for edge_id in row.get("theory_of_victory") or []
            if edge_id in edges
        ],
        constraints=row.get("constraints") or [],
        restraints=row.get("restraints") or [],
        mitigated_harmful_events=[
            _harmful_event_ref(index, he)
            for he in index.rows("harmful_events")
            if he["he_id"] in mitigates
        ],
        unmitigated_harmful_events=[
            _harmful_event_ref(index, he)
            for he in index.rows("harmful_events")
            if he["he_id"] not in mitigates
        ],
        decision_points=[
            DecisionPointView(
                dp_id=dp["dp_id"],
                name=dp["name"],
                latest_period=dp.get("latest_period"),
                branch_rule_ids=dp["branch_rule_ids"],
                pir_id=dp.get("pir_id"),
                pir_statement=(
                    pirs[dp["pir_id"]]["statement"] if dp.get("pir_id") in pirs else None
                ),
            )
            for dp in index.rows("decision_points")
            if dp["strategy_id"] == strategy_id
        ],
        opponent_model=OpponentModelView(
            opponent_model_id=opponent_model["opponent_model_id"],
            actor_id=opponent_model["actor_id"],
            actor_name=index.entity_name(opponent_model["actor_id"]),
            coas=[
                AdversaryCoaView(
                    strategy_id=mix["strategy_id"],
                    name=index.strategies[mix["strategy_id"]]["name"],
                    summary=index.strategies[mix["strategy_id"]]["summary"],
                    adversary_coa_label=index.strategies[mix["strategy_id"]].get(
                        "adversary_coa_label"
                    ),
                    probability=mix["probability"],
                )
                for mix in opponent_model["distribution"]
            ],
        ),
        mission_who=row["mission_who"],
        mission_what=row["mission_what"],
        mission_when=row["mission_when"],
        mission_where=row["mission_where"],
        mission_why=row["mission_why"],
        main_effort=row["main_effort"],
        sequencing=row["sequencing"],
        reserve_policy=row["reserve_policy"],
        task_org=row.get("task_org") or [],
        task_org_names=[
            index.entity_name(unit) or unit for unit in row.get("task_org") or []
        ],
    )


# ---------------------------------------------------------------- collection
def _priority_basis(index: Index, req: dict) -> PriorityBasisView | None:
    if req.get("priority") is None:
        return None
    assumption = index.assumptions.get(req.get("assumption_id") or "")
    if assumption is not None and assumption.get("evpi") is not None:
        return PriorityBasisView(
            basis="evpi",
            assumption_id=assumption["assumption_id"],
            evpi=assumption["evpi"],
            claim_id=None,
            confidence=None,
            degree=None,
        )
    claim = index.current_claim(req["subject_id"], req["predicate"])
    degree = 0
    if claim is not None:
        for edge in index.rows("dependencies"):
            degree += edge["from_type"] == "claim" and edge["from_id"] == claim["claim_id"]
            degree += edge["to_type"] == "claim" and edge["to_id"] == claim["claim_id"]
    return PriorityBasisView(
        basis="fallback",
        assumption_id=req.get("assumption_id"),
        evpi=None,
        claim_id=claim["claim_id"] if claim else None,
        confidence=claim["confidence"] if claim else 0.0,
        degree=degree,
    )


def _actor_of(index: Index, strategy_id: str) -> tuple[str, str]:
    row = index.strategies[strategy_id]
    return row["game_id"], row["actor_id"]


def _routing_authority(index: Index) -> AuthorityView | None:
    """The authority tier that approves submitting a collection requirement."""
    rule = next(
        (
            r
            for r in index.rows("recommendation_authority")
            if r["recommendation_type"] == "requirement_submit"
        ),
        None,
    )
    if rule is None:
        return None
    tier = index.by("authority_tiers", "tier_id").get(rule["tier_id"])
    if tier is None:
        return None
    return AuthorityView(
        tier_id=tier["tier_id"],
        name=tier["name"],
        approver_role=tier["approver_role"],
        recommendation_type=rule["recommendation_type"],
        risk_level_threshold=rule["risk_level_threshold"],
    )


def _source_view(index: Index, source_id: str | None) -> SourceView | None:
    source = index.sources.get(source_id or "")
    if source is None:
        return None
    return SourceView(
        source_id=source["source_id"],
        title=source["title"],
        path=source["path"],
        doc_type=source["doc_type"],
        author_org=source["author_org"],
        reliability=source["reliability"],
        credibility=source["credibility"],
        published_at=source["published_at"],
        batch=source["batch"],
    )


def requirement_view(index: Index, req: dict, authority: AuthorityView | None) -> RequirementView:
    pir = index.by("pirs", "pir_id").get(req["pir_id"])
    assumption = index.assumptions.get(req.get("assumption_id") or "")
    assets = index.by("assets", "asset_id")
    coverage = [
        row
        for row in index.rows("asset_coverage")
        if row["entity_id"] == req["subject_id"] and row["predicate"] == req["predicate"]
    ]
    affected = []
    if assumption is not None:
        # Assumptions sharing index_k share the grounding claim and p_k (SCHEMA.md §1), so
        # answering this requirement moves every option that requires one of them.
        actor = _actor_of(index, assumption["strategy_id"])
        siblings = {
            a["assumption_id"]
            for a in index.rows("assumptions")
            if a["index_k"] == assumption["index_k"]
            and _actor_of(index, a["strategy_id"]) == actor
        }
        affected = [
            edge["to_id"]
            for edge in index.rows("dependencies")
            if edge["kind"] == "requires"
            and edge["from_id"] in siblings
            and edge["to_type"] == "strategy"
        ]
    product = req.get("owner") == "product"
    closed_by_replay = (
        not product
        and req["status"] in CLOSED_STATUSES
        and req.get("answered_by_source_id") is not None
    )
    return RequirementView(
        req_id=req["req_id"],
        pir_id=req["pir_id"],
        pir_statement=pir["statement"] if pir else None,
        pir_priority_rank=pir["priority_rank"] if pir else None,
        commander_role=pir["commander_role"] if pir else None,
        eei=req["eei"],
        indicators=req["indicators"],
        sir=req["sir"],
        gap_type=req["gap_type"],
        status=req["status"],
        ltiov=req["ltiov"],
        created_at=req["created_at"],
        routing=req["routing"],
        routing_authority=authority,
        rfi_disposition=req["rfi_disposition"],
        subject_id=req["subject_id"],
        subject_name=index.entity_name(req["subject_id"]),
        predicate=req["predicate"],
        priority=req.get("priority"),
        priority_basis=_priority_basis(index, req),
        jipcl_rank=req.get("jipcl_rank"),
        closure_basis=(
            req.get("closure_basis") if product
            else ("manifest_replay" if closed_by_replay else None)
        ),
        answered_by_source=_source_view(index, req.get("answered_by_source_id")),
        assumption=assumption_view(index, assumption) if assumption else None,
        affected_strategies=[
            StrategyRefView(
                strategy_id=sid,
                name=index.strategies[sid]["name"],
                status=index.strategies[sid]["status"],
            )
            for sid in sorted(set(affected))
            if sid in index.strategies
        ],
        candidate_assets=[
            AssetCandidateView(
                asset_id=row["asset_id"],
                name=assets[row["asset_id"]]["name"],
                owner_org=assets[row["asset_id"]]["owner_org"],
                discipline=row["discipline"],
                p_success=row["p_success"],
                latency_periods=row["latency_periods"],
                range_ok=row["range_ok"],
                timeliness_ok=row["timeliness_ok"],
                target_characteristics_match=row["target_characteristics_match"],
                capacity_per_period=assets[row["asset_id"]]["capacity_per_period"],
                cost_per_task=assets[row["asset_id"]]["cost_per_task"],
            )
            for row in sorted(coverage, key=lambda r: r["asset_id"])
            if row["asset_id"] in assets
        ],
        disciplines=sorted({row["discipline"] for row in coverage}),
        owner="product" if product else None,
        product=_product_requirement(req) if product else None,
    )


def _product_requirement(req: dict) -> ProductRequirementView:
    return ProductRequirementView(
        strategy_question=req.get("strategy_question"),
        strategy_id=req.get("strategy_id"),
        gap_reason=req["gap_reason"],
        proposed_owner=req["proposed_owner"],
        required_evidence=req["required_evidence"],
        authority_tier_id=req.get("authority_tier_id"),
        satisfied_by_claim_id=req.get("satisfied_by_claim_id"),
        created_actual_at=req["created_actual_at"],
        created_by=req["created_by"],
        status_history=[
            RequirementStatusChangeView(**entry) for entry in req.get("status_history", [])
        ],
    )


def requirement_by_id(index: Index, req_id: str) -> RequirementView:
    """One requirement as the evaluator ranked it — priority and jipcl_rank included."""
    row = index.by("collection_requirements", "req_id")[req_id]
    return requirement_view(index, row, _routing_authority(index))


def requirement_views(index: Index) -> list[RequirementView]:
    """Requirements ranked by jipcl_rank; closed ones (rank null) last, by req_id."""
    authority = _routing_authority(index)
    views = [requirement_view(index, r, authority) for r in index.rows("collection_requirements")]
    return sorted(
        views, key=lambda r: (r.jipcl_rank is None, r.jipcl_rank or 0, r.req_id)
    )


# ---------------------------------------------------------------- decision overview
def decision_overview(index: Index) -> DecisionOverviewView:
    ranking = index.ranking(BLUE_GAME_ID, BLUE_ACTOR_ID)
    recommended = index.strategies[ranking[0]] if ranking else None
    runner_up = index.strategies[ranking[1]] if len(ranking) > 1 else None
    criteria = _criteria(index, recommended, runner_up) if recommended else []
    requirements = [r for r in requirement_views(index) if r.jipcl_rank is not None]
    levels = index.risk_levels
    risk_rows = sorted(
        index.rows("risk_assessments"),
        key=lambda r: (-levels.index(r["risk_level"]), -r["p_raw"], r["he_id"]),
    )
    top_level = risk_rows[0]["risk_level"] if risk_rows else None
    game = index.by("games", "game_id")[BLUE_GAME_ID]
    return DecisionOverviewView(
        scenario_id=BLUE_GAME_ID,
        scenario_name=game["name"],
        friendly_force_id=BLUE_ACTOR_ID,
        friendly_force_name=index.entity_name(BLUE_ACTOR_ID) or BLUE_ACTOR_ID,
        adversary_id=next(
            actor_id for actor_id in game["actor_ids"] if actor_id != BLUE_ACTOR_ID
        ),
        adversary_name=index.entity_name(next(
            actor_id for actor_id in game["actor_ids"] if actor_id != BLUE_ACTOR_ID
        )) or "Unknown adversary",
        as_of=index.snapshot.as_of,
        batch=index.batch,
        marking=MARKING,
        caution=caution(),
        ranking=ranking,
        recommended=(
            RecommendedView(
                strategy_id=recommended["strategy_id"],
                name=recommended["name"],
                status=recommended["status"],
                value=recommended["value"],
                adversary_range=recommended["value_ci"],
                robustness=recommended["robustness"],
                risk_functional=recommended["risk_functional"],
                risk_alpha=recommended["risk_alpha"],
            )
            if recommended
            else None
        ),
        why=_why(index, recommended, runner_up, criteria) if recommended else None,
        highest_sensitivity_assumptions=(
            sorted(
                (
                    assumption_view(index, a)
                    for a in index.rows("assumptions")
                    if a["strategy_id"] == recommended["strategy_id"]
                ),
                key=lambda a: (-abs(a.sensitivity or 0.0), a.assumption_id),
            )[:3]
            if recommended
            else []
        ),
        top_collection_requirement=requirements[0] if requirements else None,
        highest_risks=[
            RiskHighlightView(
                he_id=row["he_id"],
                statement=index.harmful_events[row["he_id"]]["statement"],
                problem_set_id=index.harmful_events[row["he_id"]]["problem_set_id"],
                problem_set_name=index.problem_sets[
                    index.harmful_events[row["he_id"]]["problem_set_id"]
                ]["name"],
                jsps_horizon=row["jsps_horizon"],
                risk_level=row["risk_level"],
                trend=row["trend"],
                p_level=row["p_level"],
                c_level=row["c_level"],
            )
            for row in risk_rows[:5]
        ],
        problem_sets_at_highest_level=[
            ProblemSetAssessmentView(
                problem_set_id=row["problem_set_id"],
                jsps_horizon=row["jsps_horizon"],
                max_risk_level=row["max_risk_level"],
                he_ids=row["he_ids"],
                aggregated_statement_text=row["aggregated_statement_text"],
            )
            for row in index.rows("problem_set_assessments")
            if row["max_risk_level"] == top_level
        ],
    )


def _criteria(index: Index, recommended: dict, runner_up: dict | None) -> list[CriterionView]:
    mine = index.contributions(recommended["strategy_id"])
    theirs = index.contributions(runner_up["strategy_id"]) if runner_up else {}
    ratings = {
        (so["strategy_id"], so["objective_id"]): so.get("rating_1_to_3")
        for so in index.rows("strategy_objectives")
    }
    out = []
    for so in index.rows("strategy_objectives"):
        if so["strategy_id"] != recommended["strategy_id"]:
            continue
        objective_id = so["objective_id"]
        out.append(
            CriterionView(
                objective_id=objective_id,
                name=index.objectives[objective_id]["name"],
                weight=so["weight"],
                rating_1_to_3=so.get("rating_1_to_3"),
                contribution=mine.get(objective_id, 0.0),
                runner_up_contribution=theirs.get(objective_id) if runner_up else None,
                runner_up_rating=(
                    ratings.get((runner_up["strategy_id"], objective_id))
                    if runner_up
                    else None
                ),
            )
        )
    return sorted(out, key=lambda c: (-c.weight, c.objective_id))


def _why(
    index: Index, recommended: dict, runner_up: dict | None, criteria: list[CriterionView]
):
    from .contracts import TradeoffView, WhyView

    winning = [
        c
        for c in criteria
        if c.runner_up_contribution is None or c.contribution >= c.runner_up_contribution
    ]
    losing = [
        c
        for c in criteria
        if c.runner_up_contribution is not None and c.runner_up_contribution > c.contribution
    ]
    return WhyView(
        winning_criteria=winning,
        validity_evidence=validity_views(recommended),
        tradeoff=(
            TradeoffView(
                runner_up_id=runner_up["strategy_id"],
                runner_up_name=runner_up["name"],
                value_gap=recommended["value"] - runner_up["value"],
                objectives_favouring_runner_up=sorted(
                    losing,
                    key=lambda c: (
                        -(c.weight * (c.runner_up_contribution - c.contribution)),
                        c.objective_id,
                    ),
                ),
            )
            if runner_up
            else None
        ),
    )


# ---------------------------------------------------------------- claims
def claim_ref(index: Index, claim: dict) -> ClaimRefView:
    source = index.sources.get(claim["source_id"])
    return ClaimRefView(
        claim_id=claim["claim_id"],
        label=index.claim_label(claim),
        value=index.claim_value(claim),
        status=claim["status"],
        likelihood_icd203=claim.get("likelihood_icd203"),
        confidence=claim["confidence"],
        source_id=claim["source_id"],
        source_title=source["title"] if source else None,
        reliability=source["reliability"] if source else None,
    )


def claim_view(index: Index, claim: dict) -> ClaimView:
    contradicts = index.contradictions.get(claim["claim_id"], [])
    return ClaimView(
        claim_id=claim["claim_id"],
        subject_id=claim["subject_id"],
        subject_name=index.entity_name(claim["subject_id"]),
        predicate=claim["predicate"],
        object_id=claim.get("object_id"),
        object_name=index.entity_name(claim.get("object_id")),
        value=claim.get("value"),
        value_type=claim["value_type"],
        unit=claim.get("unit"),
        valid_from=claim["valid_from"],
        valid_to=claim.get("valid_to"),
        asserted_at=claim["asserted_at"],
        estimative=claim["estimative"],
        likelihood_icd203=claim.get("likelihood_icd203"),
        likelihood_surface_term=claim.get("likelihood_surface_term"),
        confidence_icd203=claim["confidence_icd203"],
        confidence=claim["confidence"],
        confidence_basis=CONFIDENCE_BASIS,
        status=claim["status"],
        supersedes_claim_id=claim.get("supersedes_claim_id"),
        truth_claim_id=claim.get("truth_claim_id"),
        span_start=claim["span_start"],
        span_end=claim["span_end"],
        span_text=index.span_text(claim),
        source_id=claim["source_id"],
        source=_source_view(index, claim["source_id"]),
        flags=ClaimFlagsView(
            proposed=claim["status"] == "proposed",
            contradiction=bool(contradicts),
            contradicts_claim_ids=sorted(contradicts),
            stale=index.is_stale(claim),
            superseded=index.is_superseded(claim),
            superseded_by_claim_id=index.superseded_by.get(claim["claim_id"]),
        ),
    )


def _edge(
    index: Index,
    edge_id: str,
    kind: str,
    to_type: str,
    to_id: str,
    mechanism: str,
    claim: dict,
) -> dict:
    return {
        "edge_id": edge_id,
        "kind": kind,
        "mechanism": mechanism,
        "from_type": "claim",
        "from_id": claim["claim_id"],
        "to_type": to_type,
        "to_id": to_id,
        "basis": "current_evidence",
    }


def current_evidence_edges(index: Index, claim: dict) -> list[dict]:
    """The links the evaluator itself makes from this claim at the batch's as_of date.

    An assumption is grounded by the approved claim on its (subject, predicate) that is
    valid at ``as_of`` — the selection ``eval.claimset.ClaimSet.current`` makes. A risk
    driver is driven by the approved claims that satisfy its (op, value) inside a horizon
    window, which is how ``eval.engine.assess_risk`` activates it. Neither relationship is
    in the frozen ``dependencies`` table, so inject evidence has no edge there.
    """
    if not index.is_current_evidence(claim):
        return []
    key = (claim["subject_id"], claim["predicate"])
    claim_id = claim["claim_id"]
    out: list[dict] = []
    for assumption in sorted(index.rows("assumptions"), key=lambda a: a["assumption_id"]):
        if (assumption["subject_id"], assumption["predicate"]) != key:
            continue
        selected = index.current_claim(*key)
        chosen = selected is not None and selected["claim_id"] == claim_id
        out.append(
            _edge(
                index,
                f"current:{claim_id}->{assumption['assumption_id']}",
                "grounds",
                "assumption",
                assumption["assumption_id"],
                (
                    "the approved claim the evaluator selects for this (subject, "
                    "predicate) at as_of; its tolerance test sets p_holds and status"
                    if chosen
                    else "an approved claim valid at as_of on the assumption's "
                    "(subject, predicate); the latest asserted one is selected"
                ),
                claim,
            )
        )
    for driver in sorted(index.rows("risk_drivers"), key=lambda d: d["driver_id"]):
        if (driver["claim_subject_id"], driver["claim_predicate"]) != key:
            continue
        horizons = [h for h in HORIZONS if claim in index.driver_claims(driver, h)]
        if not horizons:
            continue
        out.append(
            _edge(
                index,
                f"current:{claim_id}->{driver['driver_id']}",
                "drives",
                "harmful_event",
                driver["he_id"],
                f"driver {driver['driver_id']} ({driver['label']}): the claim satisfies "
                f"{driver['claim_predicate']} {driver['op']} {driver['value']}, adding "
                f"{driver['delta']} to P_raw in the {', '.join(horizons)} horizon window",
                claim,
            )
        )
    return out


def _trace_node(index: Index, node_type: str, node_id: str) -> TraceNodeView:
    status = None
    if node_type == "claim":
        row = index.claims.get(node_id)
        if row is not None:
            status = "superseded" if index.is_superseded(row) else row["status"]
    return TraceNodeView(
        type=node_type,
        id=node_id,
        name=index.display_name(node_type, node_id),
        status=status,
    )


def claim_trace(index: Index, claim: dict) -> ClaimTraceView:
    claim_id = claim["claim_id"]
    frozen = index.edges_from.get(claim_id, [])
    seen = {(e["kind"], e["to_type"], e["to_id"]) for e in frozen}
    first_hops = list(frozen) + [
        edge
        for edge in current_evidence_edges(index, claim)
        if (edge["kind"], edge["to_type"], edge["to_id"]) not in seen
    ]
    source = index.sources.get(claim["source_id"])
    head = [
        TraceNodeView(
            type="source",
            id=claim["source_id"],
            name=source["title"] if source else claim["source_id"],
        ),
        _trace_node(index, "claim", claim_id),
    ]
    paths = []
    for hop in first_hops:
        for onward in index.walk(hop["to_id"], depth=2) or [[]]:
            chain = [hop, *onward]
            paths.append(
                TracePathView(
                    nodes=head
                    + [_trace_node(index, e["to_type"], e["to_id"]) for e in chain],
                    edges=[_chain_edge(index, e) for e in chain],
                )
            )
    return ClaimTraceView(
        claim_id=claim_id,
        claim_node=head[1],
        edges=[_chain_edge(index, e) for e in first_hops],
        paths=paths,
    )


def filter_claims(
    index: Index,
    *,
    entity: str | None = None,
    source: str | None = None,
    status: str | None = None,
    min_confidence: float | None = None,
    relationship: str | None = None,
    assumption: str | None = None,
    harmful_event: str | None = None,
) -> list[dict]:
    rows = sorted(index.rows("claims"), key=lambda c: c["claim_id"])
    if entity:
        rows = [c for c in rows if entity in (c["subject_id"], c.get("object_id"))]
    if source:
        rows = [c for c in rows if c["source_id"] == source]
    if status:
        rows = [c for c in rows if c["status"] == status]
    if min_confidence is not None:
        rows = [c for c in rows if c["confidence"] >= min_confidence]
    if relationship:
        linked = {
            node
            for edge in index.rows("dependencies")
            if edge["kind"] == relationship
            for node, node_type in (
                (edge["from_id"], edge["from_type"]),
                (edge["to_id"], edge["to_type"]),
            )
            if node_type == "claim"
        }
        rows = [c for c in rows if c["claim_id"] in linked]
    if assumption:
        grounding = {
            edge["from_id"]
            for edge in index.rows("dependencies")
            if edge["kind"] == "grounds"
            and edge["to_type"] == "assumption"
            and edge["to_id"] == assumption
        }
        rows = [c for c in rows if c["claim_id"] in grounding]
    if harmful_event:
        driving = {
            edge["from_id"]
            for edge in index.rows("dependencies")
            if edge["to_type"] == "harmful_event" and edge["to_id"] == harmful_event
        }
        rows = [c for c in rows if c["claim_id"] in driving]
    return rows


# ---------------------------------------------------------------- risk
def _escalation_edge(index: Index, edge: dict) -> EscalationEdgeView:
    events = index.harmful_events
    return EscalationEdgeView(
        edge_id=edge["edge_id"],
        from_he_id=edge["from_he_id"],
        from_statement=events[edge["from_he_id"]]["statement"] if edge["from_he_id"] in events else None,
        to_he_id=edge["to_he_id"],
        to_statement=events[edge["to_he_id"]]["statement"] if edge["to_he_id"] in events else None,
        lift=edge["lift"],
        mechanism=edge["mechanism"],
    )


def _driver_view(index: Index, driver: dict, horizon: str, dominant: bool) -> RiskDriverView:
    return RiskDriverView(
        driver_id=driver["driver_id"],
        driver_kind=driver["driver_kind"],
        locus=driver["locus"],
        label=driver["label"],
        op=driver["op"],
        value=driver.get("value"),
        delta=driver["delta"],
        claim_subject_id=driver["claim_subject_id"],
        claim_subject_name=index.entity_name(driver["claim_subject_id"]),
        claim_predicate=driver["claim_predicate"],
        dominant=dominant,
        claims=[claim_ref(index, c) for c in index.driver_claims(driver, horizon)],
    )


def harmful_event_views(index: Index) -> list[HarmfulEventView]:
    drivers = index.by("risk_drivers", "driver_id")
    out = []
    for he in index.rows("harmful_events"):
        he_id = he["he_id"]
        problem_set = index.problem_sets.get(he["problem_set_id"])
        horizons = []
        for horizon in HORIZONS:
            row = index.risk_rows.get((he_id, horizon))
            if row is None:
                continue
            horizons.append(
                HorizonAssessmentView(
                    jsps_horizon=horizon,
                    p_raw=row["p_raw"],
                    p_level=row["p_level"],
                    c_level=row["c_level"],
                    risk_level=row["risk_level"],
                    trend=row["trend"],
                    statement_text=row["statement_text"],
                    forced_choice_applied=row["forced_choice_applied"],
                    posture_rationale=row.get("posture_rationale"),
                    dominant_driver_id=row.get("dominant_driver_id"),
                    active_drivers=[
                        _driver_view(
                            index,
                            drivers[driver_id],
                            horizon,
                            driver_id == row.get("dominant_driver_id"),
                        )
                        for driver_id in row["active_driver_ids"]
                        if driver_id in drivers
                    ],
                )
            )
        objective = index.objectives.get(he["thing_of_value_id"])
        out.append(
            HarmfulEventView(
                he_id=he_id,
                problem_set_id=he["problem_set_id"],
                problem_set_name=problem_set["name"] if problem_set else None,
                statement=he["statement"],
                risk_type=he["risk_type"],
                risk_subset=he.get("risk_subset"),
                thing_of_value_id=he["thing_of_value_id"],
                thing_of_value_name=objective["name"] if objective else None,
                consequence_basis=ConsequenceBasisView(
                    basis="msr" if he["risk_type"] == "MSR" else "mr",
                    strategic_value=he.get("strategic_value"),
                    damage_degree=he.get("damage_degree"),
                    fig28_row=he.get("fig28_row"),
                    fig28_cell=he.get("fig28_cell"),
                ),
                condition=he["condition"],
                base_p=he["base_p"],
                posture_subject_ids=he.get("posture_subject_ids") or [],
                posture_subject_names=[
                    index.entity_name(e) or e for e in he.get("posture_subject_ids") or []
                ],
                beneficial_counterpart_he_id=he.get("beneficial_counterpart_he_id"),
                beneficial_statement=he.get("beneficial_statement"),
                key_actions=he.get("key_actions"),
                horizons=horizons,
                sources_of_risk=[
                    RiskSourceView(
                        rs_id=rs["rs_id"],
                        source_kind=rs["source_kind"],
                        entity_id=rs["entity_id"],
                        entity_name=index.entity_name(rs["entity_id"]),
                        description=rs["description"],
                    )
                    for rs in index.rows("risk_sources")
                    if rs["he_id"] == he_id
                ],
                cascade=CascadeView(
                    upstream_paths=index.upstream_paths(he_id),
                    upstream_edges=[
                        _escalation_edge(index, e) for e in index.escalation_into.get(he_id, [])
                    ],
                    downstream_edges=[
                        _escalation_edge(index, e) for e in index.escalation_out_of.get(he_id, [])
                    ],
                ),
            )
        )
    return out


def problem_set_views(index: Index) -> list[ProblemSetView]:
    assessments: dict[str, list[dict]] = {}
    for row in index.rows("problem_set_assessments"):
        assessments.setdefault(row["problem_set_id"], []).append(row)
    out = []
    for ps in index.rows("problem_sets"):
        rows = {r["jsps_horizon"]: r for r in assessments.get(ps["problem_set_id"], [])}
        out.append(
            ProblemSetView(
                problem_set_id=ps["problem_set_id"],
                name=ps["name"],
                entity_id=ps["entity_id"],
                tier=ps["tier"],
                thing_of_value_ids=ps["thing_of_value_ids"],
                thing_of_value_names=[
                    index.objectives[o]["name"]
                    for o in ps["thing_of_value_ids"]
                    if o in index.objectives
                ],
                risk_owner_role=ps["risk_owner_role"],
                tolerance_statement=ps["tolerance_statement"],
                strategic_context=ps["strategic_context"],
                scope_and_boundaries=ps["scope_and_boundaries"],
                assumptions_and_constraints=ps["assumptions_and_constraints"],
                expected_outputs=ps["expected_outputs"],
                risk_context_source=_source_view(index, ps.get("risk_context_source_id")),
                horizons=[
                    ProblemSetHorizonView(
                        jsps_horizon=horizon,
                        max_risk_level=rows[horizon]["max_risk_level"],
                        he_ids=rows[horizon]["he_ids"],
                        aggregated_statement_text=rows[horizon]["aggregated_statement_text"],
                    )
                    for horizon in HORIZONS
                    if horizon in rows
                ],
            )
        )
    return out


# ---------------------------------------------------------------- inject diff
def _meridian(index: Index, table: str, key: str) -> dict[str, dict]:
    """Rows of one table that belong to the Meridian game, keyed by id."""
    if table == "strategies":
        return {
            s[key]: s for s in index.rows("strategies") if s["game_id"] == BLUE_GAME_ID
        }
    meridian = {s["strategy_id"] for s in index.rows("strategies") if s["game_id"] == BLUE_GAME_ID}
    return {r[key]: r for r in index.rows(table) if r["strategy_id"] in meridian}


def diff(before: Index, after: Index) -> dict[str, Any]:
    """What changed between two loaded snapshots. Field names follow the manifest's."""
    strategies_before = _meridian(before, "strategies", "strategy_id")
    strategies_after = _meridian(after, "strategies", "strategy_id")
    assumptions_before = _meridian(before, "assumptions", "assumption_id")
    assumptions_after = _meridian(after, "assumptions", "assumption_id")
    reqs_before = before.by("collection_requirements", "req_id")
    reqs_after = after.by("collection_requirements", "req_id")
    shared = sorted(set(strategies_before) & set(strategies_after))

    risks_changed = [
        (key, before.risk_rows[key], after.risk_rows[key])
        for key in sorted(set(before.risk_rows) & set(after.risk_rows))
        if (
            before.risk_rows[key]["risk_level"],
            before.risk_rows[key]["trend"],
            before.risk_rows[key]["p_raw"],
        )
        != (
            after.risk_rows[key]["risk_level"],
            after.risk_rows[key]["trend"],
            after.risk_rows[key]["p_raw"],
        )
    ]
    changed_events = {key[0] for key, _, _ in risks_changed}

    problem_before = {
        (r["problem_set_id"], r["jsps_horizon"]): r
        for r in before.rows("problem_set_assessments")
    }
    problem_after = {
        (r["problem_set_id"], r["jsps_horizon"]): r
        for r in after.rows("problem_set_assessments")
    }
    return {
        "evidence": _evidence(before, after),
        "assumptions_changed": [
            AssumptionChangeView(
                assumption_id=key,
                **{"from": assumptions_before[key]["status"]},
                to=assumptions_after[key]["status"],
                statement=assumptions_after[key]["statement"],
                p_holds_before=assumptions_before[key]["p_holds"],
                p_holds_after=assumptions_after[key]["p_holds"],
            )
            for key in sorted(set(assumptions_before) & set(assumptions_after))
            if assumptions_before[key]["status"] != assumptions_after[key]["status"]
        ],
        "validity_changed": [
            ValidityChangeView(
                strategy_id=key,
                name=strategies_after[key]["name"],
                test=test,
                before=strategies_before[key]["validity"][test]["pass"],
                after=strategies_after[key]["validity"][test]["pass"],
                evidence_after=strategies_after[key]["validity"][test]["evidence"],
            )
            for key in shared
            for test in strategies_before[key]["validity"]
            if strategies_before[key]["validity"][test]["pass"]
            != strategies_after[key]["validity"][test]["pass"]
        ],
        "strategies_restated": [
            StrategyRestatedView(
                strategy_id=key,
                name=strategies_after[key]["name"],
                value_before=strategies_before[key]["value"],
                value_after=strategies_after[key]["value"],
                status_before=strategies_before[key]["status"],
                status_after=strategies_after[key]["status"],
            )
            for key in shared
            if (strategies_before[key]["value"], strategies_before[key]["status"])
            != (strategies_after[key]["value"], strategies_after[key]["status"])
        ],
        "ranking_before": before.ranking(BLUE_GAME_ID, BLUE_ACTOR_ID),
        "ranking_after": after.ranking(BLUE_GAME_ID, BLUE_ACTOR_ID),
        "risk_assessments_changed": [
            RiskChangeView(
                he_id=key[0],
                horizon=key[1],
                level_before=old["risk_level"],
                level_after=new["risk_level"],
                trend_after=new["trend"],
                trend_before=old["trend"],
                p_before=old["p_raw"],
                p_after=new["p_raw"],
                statement=after.harmful_events[key[0]]["statement"],
                cascade_paths=[
                    path
                    for path in after.upstream_paths(key[0])
                    if set(path[:-1]) & changed_events
                ],
            )
            for key, old, new in risks_changed
        ],
        "problem_sets_moved": [
            ProblemSetMovedView(
                problem_set_id=key[0],
                jsps_horizon=key[1],
                level_before=problem_before[key]["max_risk_level"],
                level_after=problem_after[key]["max_risk_level"],
                name=after.problem_sets[key[0]]["name"],
            )
            for key in sorted(set(problem_before) & set(problem_after))
            if problem_before[key]["max_risk_level"] != problem_after[key]["max_risk_level"]
        ],
        "requirements_closed": [
            key
            for key in sorted(set(reqs_before) & set(reqs_after))
            if reqs_before[key]["status"] not in CLOSED_STATUSES
            and reqs_after[key]["status"] in CLOSED_STATUSES
        ],
        "jipcl_changed": _jipcl_changed(reqs_before, reqs_after),
    }


def _jipcl_changed(before: dict[str, dict], after: dict[str, dict]) -> list[JipclChangeView]:
    """A requirement created in this batch was unranked before: rank null, status unchanged."""
    out = []
    for key in sorted(after):
        old = before.get(key)
        rank_before = old["jipcl_rank"] if old else None
        status_before = old["status"] if old else after[key]["status"]
        if (rank_before, status_before) == (after[key]["jipcl_rank"], after[key]["status"]):
            continue
        out.append(
            JipclChangeView(
                req_id=key,
                rank_before=rank_before,
                rank_after=after[key]["jipcl_rank"],
                status_before=status_before,
                status_after=after[key]["status"],
                new=old is None,
            )
        )
    return out


def _evidence(before: Index, after: Index) -> EvidenceChangeView:
    added = [
        claim
        for claim_id, claim in sorted(after.claims.items())
        if claim_id not in before.claims
    ]
    superseded = [
        after.claims[claim["supersedes_claim_id"]]
        for claim in added
        if claim.get("supersedes_claim_id") in after.claims
    ]
    contradicted = [claim for claim in added if claim["claim_id"] in after.contradictions]
    return EvidenceChangeView(
        claims_added=[claim_ref(after, c) for c in added],
        claims_superseded=[claim_ref(after, c) for c in superseded],
        claims_contradicted=[claim_ref(after, c) for c in contradicted],
    )


# ---------------------------------------------------------------- product views
def report_view(report: dict) -> ReportView:
    return ReportView(
        report_id=report["report_id"], filename=report["filename"], format=report["format"],
        sha256=report["sha256"], uploaded_at=report["uploaded_at"], actor=report["actor"],
        report_date=report["report_date"], source_id=report["source_id"],
        extractor=report["extractor"], text_length=len(report["text"]),
    )


def proposed_claim_view(index: Index, record: dict, text: str) -> ProposedClaimView:
    """A proposed claim with its exact slice of the stored report text."""
    from .product.review import derived_confidence

    claim = record["claim"]
    return ProposedClaimView(
        claim_id=claim["claim_id"], report_id=record["report_id"], status=record["status"],
        subject_id=claim["subject_id"],
        subject_name=index.entity_name(claim["subject_id"]),
        predicate=claim["predicate"], object_id=claim.get("object_id"),
        object_name=index.entity_name(claim.get("object_id")), value=claim.get("value"),
        value_type=claim["value_type"], unit=claim.get("unit"),
        valid_from=claim.get("valid_from"), valid_to=claim.get("valid_to"),
        asserted_at=claim.get("asserted_at"), estimative=claim["estimative"],
        likelihood_icd203=claim.get("likelihood_icd203"),
        likelihood_surface_term=claim.get("likelihood_surface_term"),
        confidence_icd203=claim.get("confidence_icd203"),
        confidence=claim.get("confidence") or derived_confidence(claim),
        span_start=claim["span_start"], span_end=claim["span_end"],
        span_text=text[claim["span_start"] : claim["span_end"]],
        flags=record["flags"], notes=record.get("notes", []),
        contradicts=record.get("contradicts", []),
        contradicts_reason=record.get("contradicts_reason"),
        accepted_graph_version=record.get("accepted_graph_version"),
    )


def instruction_span_views(spans: list[dict]) -> list[InstructionLikeSpanView]:
    return [InstructionLikeSpanView(**span) for span in spans]


def planning_object_view(record: dict) -> PlanningObjectView:
    return PlanningObjectView(
        object_id=record["object_id"], kind=record["kind"],
        strategy_id=record["strategy_id"], text=record["text"],
        subject_id=record["subject_id"], predicate=record["predicate"],
        status=record["status"],
        source_links=[SourceLinkView(**link) for link in record["source_links"]],
        validity=ValidityWindowView(**record["validity"]) if record["validity"] else None,
        confidence=(
            ObjectConfidenceView(**record["confidence"]) if record["confidence"] else None
        ),
        review_status=record["review_status"], provenance=record["provenance"],
        review=PlanningReviewView(**record["review"]) if record.get("review") else None,
    )


def planning_flag_views(flags: list[dict]) -> list[PlanningFlagView]:
    return [PlanningFlagView(**flag) for flag in flags]
