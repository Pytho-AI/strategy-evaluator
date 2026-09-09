"""The v3 comparison screen: the option set, the weighted ranking, the enumerated outcome
distribution, and the "if this assumption fails" recomputation.

Nothing here samples. ``/api/options/outcome-distribution`` is the honest replacement for
the UI's Monte Carlo: it enumerates every (assumption world, adversary COA) pair with its
own probability, so ``p_meets_aspiration`` is a real probability over this model's worlds
rather than a count of simulated runs.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Body, Depends, Query

from ..contracts import (
    AdversaryRangeView,
    ExcludedOptionView,
    CriterionMemberView,
    CriterionOutcomeView,
    LevelThresholdView,
    OptionAssumptionView,
    OptionStabilityShareView,
    OptionView,
    OptionsResponse,
    OutcomeBinView,
    OutcomeDistributionResponse,
    OutcomeDistributionView,
    RankRequest,
    RankResponse,
    RankedOptionView,
    ValidityTestView,
    WeightStabilityView,
    WhatIfAssumptionView,
    WhatIfOptionView,
    WhatIfProblemSetMoveView,
    WhatIfResponse,
    WhatIfRiskMoveView,
    WhatIfStatusChangeView,
)
from ..derive import caution
from ..options import (
    BIN_DOMAIN,
    BIN_NOTE,
    CRITERION_LEVEL_BASIS,
    DEFAULT_WEIGHTS,
    OptionSet,
    level_label,
    level_score,
    level_thresholds,
    what_if,
)
from ..scenarios import CRITERION_KEYS, ScenarioRegistry
from ..adapter import VALIDITY_TESTS
from .common import BATCH_QUERY, SCENARIO_QUERY, WORKSPACE_QUERY, envelope, get_registry, view

router = APIRouter()


def _weight_query(key: str):
    return Query(
        None,
        ge=0,
        le=5,
        description=(
            f"weight on the {key} criterion (0-5). Omitted keeps the v3 UI's shipped "
            f"default of {DEFAULT_WEIGHTS[key]}. Weights are an operator input, not data."
        ),
    )


def _weights(supplied: dict[str, int | None]) -> dict[str, int]:
    return {
        key: DEFAULT_WEIGHTS[key] if supplied.get(key) is None else int(supplied[key])
        for key in CRITERION_KEYS
    }


def _option_set(registry: ScenarioRegistry, batch: int, workspace: str,
                scenario: str | None):
    scenario_id = registry.resolve(scenario)
    overlay = view(registry, batch, workspace, scenario)
    entry = registry.entry(scenario_id)
    options = OptionSet(
        overlay.index, registry.criteria(scenario_id), entry.game_id, entry.actor_id
    )
    return overlay, entry, options


def _criterion_views(options: OptionSet, strategy_id: str,
                     weights: dict[str, int]) -> list[CriterionOutcomeView]:
    out = []
    for outcome in options.criterion_outcomes(strategy_id):
        score = level_score(outcome.level)
        weight = weights[outcome.criterion.key]
        out.append(
            CriterionOutcomeView(
                key=outcome.criterion.key,
                label=outcome.criterion.label,
                basis=outcome.criterion.basis,
                expected_value=round(outcome.expected_value, 9),
                shortfall=round(outcome.shortfall, 9),
                level=outcome.level,
                level_label=level_label(outcome.level),
                score=score,
                weight=weight,
                contribution=weight * score,
                members=[CriterionMemberView(**member) for member in outcome.members],
            )
        )
    return out


@router.get("/api/options", response_model=OptionsResponse)
def options_endpoint(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    mission: int | None = _weight_query("mission"),
    personnel: int | None = _weight_query("personnel"),
    escalation: int | None = _weight_query("escalation"),
    time_weight: int | None = Query(None, ge=0, le=5, alias="time"),
    resources: int | None = _weight_query("resources"),
    registry: ScenarioRegistry = Depends(get_registry),
) -> OptionsResponse:
    """The scenario's COAs, each scored on the five criteria the comparison screen shows."""
    started = time.perf_counter()
    overlay, entry, options = _option_set(registry, batch, workspace, scenario)
    weights = _weights({
        "mission": mission, "personnel": personnel, "escalation": escalation,
        "time": time_weight, "resources": resources,
    })
    index = overlay.index
    rows = []
    for strategy_id in options.ids:
        row = index.strategies[strategy_id]
        criteria = _criterion_views(options, strategy_id, weights)
        failed = [name for name in VALIDITY_TESTS if not row["validity"][name]["pass"]]
        rows.append(
            OptionView(
                strategy_id=strategy_id,
                number=options.numbers[strategy_id],
                title=row["name"],
                approach=f"{row['main_effort']} · {row['sequencing']}",
                concept=row["summary"],
                tasks=options.tasks(strategy_id),
                status=row["status"],
                validity=[
                    ValidityTestView(
                        test=name,
                        passed=row["validity"][name]["pass"],
                        evidence=row["validity"][name]["evidence"],
                    )
                    for name in VALIDITY_TESTS
                ],
                gate_failed=failed[0] if failed else None,
                gates_failed=failed,
                expected_value=row["value"],
                aspiration=row["aspiration"],
                adversary_range=AdversaryRangeView(
                    min=row["value_ci"][0], max=row["value_ci"][1]
                ),
                robustness=row["robustness"],
                criteria=criteria,
                weighted_total=sum(c.contribution for c in criteria),
                weighted_max=options.weighted_max(weights),
                assumptions=[
                    OptionAssumptionView(
                        assumption_id=a["assumption_id"],
                        index_k=a["index_k"],
                        statement=a["statement"],
                        status=a["status"],
                        p_holds=a["p_holds"],
                        sensitivity=a["sensitivity"],
                        evpi=a["evpi"],
                        subject_id=a["subject_id"],
                        subject_name=index.entity_name(a["subject_id"]),
                        predicate=a["predicate"],
                    )
                    for a in sorted(
                        (a for a in index.rows("assumptions")
                         if a["strategy_id"] == strategy_id),
                        key=lambda a: a["index_k"],
                    )
                ],
            )
        )
    return OptionsResponse(
        **envelope(overlay, started),
        scenario=entry.id,
        scenario_name=entry.name,
        caution=caution(),
        weights=weights,
        weighted_max=options.weighted_max(weights),
        level_thresholds=[LevelThresholdView(**t) for t in level_thresholds()],
        level_basis=CRITERION_LEVEL_BASIS,
        options=rows,
    )


def _rank(registry, batch, workspace, scenario, weights, started) -> RankResponse:
    overlay, entry, options = _option_set(registry, batch, workspace, scenario)
    scores = options.scores()
    ordered = options.rank(scores, weights)
    weighted_max = options.weighted_max(weights)
    index = overlay.index
    ranked = []
    for position, strategy_id in enumerate(ordered, start=1):
        row = index.strategies[strategy_id]
        criteria = _criterion_views(options, strategy_id, weights)
        total = sum(c.contribution for c in criteria)
        ranked.append(
            RankedOptionView(
                rank=position,
                strategy_id=strategy_id,
                number=options.numbers[strategy_id],
                title=row["name"],
                status=row["status"],
                weighted_total=total,
                weighted_pct=round(total / weighted_max * 100) if weighted_max else 0,
                expected_value=row["value"],
                criteria=criteria,
            )
        )
    excluded = []
    for strategy_id in options.ids:
        row = index.strategies[strategy_id]
        if row["status"] == "valid":
            continue
        failed = [name for name in VALIDITY_TESTS if not row["validity"][name]["pass"]]
        excluded.append(
            ExcludedOptionView(
                strategy_id=strategy_id,
                number=options.numbers[strategy_id],
                title=row["name"],
                status=row["status"],
                gate_failed=failed[0] if failed else None,
                gates_failed=failed,
                reason=(
                    f"status {row['status']}: failed the JP 5-0 "
                    f"{', '.join(failed)} test{'s' if len(failed) != 1 else ''}. "
                    "An option that fails a validity test is not ranked."
                ),
            )
        )
    stability = options.weight_stability(scores, weights)
    return RankResponse(
        **envelope(overlay, started),
        scenario=entry.id,
        scenario_name=entry.name,
        caution=caution(),
        weights=weights,
        weighted_max=weighted_max,
        level_thresholds=[LevelThresholdView(**t) for t in level_thresholds()],
        ranked=ranked,
        excluded=excluded,
        weight_stability=WeightStabilityView(
            top_option_id=stability["top_option_id"],
            fraction_top=stability["fraction_top"],
            weightings_evaluated=stability["weightings_evaluated"],
            method=stability["method"],
            per_option=[
                OptionStabilityShareView(**row) for row in stability["per_option"]
            ],
        ),
    )


@router.post("/api/options/rank", response_model=RankResponse)
def rank_options(
    body: RankRequest = Body(default_factory=RankRequest),
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> RankResponse:
    """Rank the options under one weighting, with the exact weight-stability fraction."""
    started = time.perf_counter()
    return _rank(
        registry, batch, workspace, scenario,
        _weights(body.model_dump()), started,
    )


@router.get("/api/options/rank", response_model=RankResponse)
def rank_options_get(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    mission: int | None = _weight_query("mission"),
    personnel: int | None = _weight_query("personnel"),
    escalation: int | None = _weight_query("escalation"),
    time_weight: int | None = Query(None, ge=0, le=5, alias="time"),
    resources: int | None = _weight_query("resources"),
    registry: ScenarioRegistry = Depends(get_registry),
) -> RankResponse:
    started = time.perf_counter()
    weights = _weights({
        "mission": mission, "personnel": personnel, "escalation": escalation,
        "time": time_weight, "resources": resources,
    })
    return _rank(registry, batch, workspace, scenario, weights, started)


def _distribution_view(options: OptionSet, strategy_id: str) -> OutcomeDistributionView:
    row = options.distribution(strategy_id)
    bins = row.pop("bins")
    return OutcomeDistributionView(
        **row, bins=[OutcomeBinView(**b) for b in bins]
    )


@router.get(
    "/api/options/outcome-distribution", response_model=OutcomeDistributionResponse
)
def outcome_distribution(
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    strategy: str | None = Query(
        None, description="one option id; omitted returns every option"
    ),
    registry: ScenarioRegistry = Depends(get_registry),
) -> OutcomeDistributionResponse:
    """The enumerated outcome distribution. No random sampling anywhere."""
    started = time.perf_counter()
    overlay, entry, options = _option_set(registry, batch, workspace, scenario)
    ids = [options.row(strategy)["strategy_id"]] if strategy else options.ids
    return OutcomeDistributionResponse(
        **envelope(overlay, started),
        scenario=entry.id,
        scenario_name=entry.name,
        bin_domain=list(BIN_DOMAIN),
        bin_note=BIN_NOTE,
        options=[_distribution_view(options, sid) for sid in ids],
    )


@router.get("/api/options/what-if", response_model=WhatIfResponse)
def what_if_endpoint(
    assumption: str = Query(..., description="the assumption id to fail"),
    batch: int = BATCH_QUERY,
    workspace: str = WORKSPACE_QUERY,
    scenario: str | None = SCENARIO_QUERY,
    registry: ScenarioRegistry = Depends(get_registry),
) -> WhatIfResponse:
    """Recompute the comparison with one assumption failing. ``method`` names both mechanisms."""
    started = time.perf_counter()
    overlay, entry, options = _option_set(registry, batch, workspace, scenario)
    result = what_if(options, assumption)
    return WhatIfResponse(
        **envelope(overlay, started),
        scenario=entry.id,
        scenario_name=entry.name,
        caution=caution(),
        assumption=WhatIfAssumptionView(**result["assumption"]),
        method=result["method"],
        withdrawn_claim_ids=result["withdrawn_claim_ids"],
        options=[WhatIfOptionView(**row) for row in result["options"]],
        ranking_before=result["ranking_before"],
        ranking_after_conditioned=result["ranking_after_conditioned"],
        ranking_after_withdrawn=result["ranking_after_withdrawn"],
        status_changes=[
            WhatIfStatusChangeView(**row) for row in result["status_changes"]
        ],
        harmful_events_moved=[
            WhatIfRiskMoveView(**row) for row in result["harmful_events_moved"]
        ],
        problem_sets_moved=[
            WhatIfProblemSetMoveView(**row) for row in result["problem_sets_moved"]
        ],
    )
