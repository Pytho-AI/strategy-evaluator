"""The comparison screen: options, criterion levels, weighted ranking, outcome
distribution, and the "if this assumption fails" recomputation.

Every number here comes out of a function in ``dataset/eval`` applied to the loaded tables.
Nothing is sampled, nothing is simulated, and no formula is copied:

* option value, ``adversary_range``, robustness, validity and status are columns the loader
  already filled through ``eval.engine.recompute``;
* a criterion's expected value is ``eval.value.value`` (objectives) or
  ``eval.validity.worst_case_cost`` (resources);
* the four-level scale is JRAM's own: ``eval.jram.p_bin`` bins the shortfall with the
  Fig. 6 probability bands and the band is read across to the like-ranked Fig. 8 risk level
  (``eval.jram.P_LEVELS[i]`` -> ``eval.jram.RISK_LEVELS[i]``). The band edges are read from
  ``eval.jram.P_BANDS`` at run time, so no threshold is typed here;
* the outcome distribution is ``eval.value.outcomes_for``: the exact enumeration of
  (assumption world, adversary COA) with its probability. There is no Monte Carlo anywhere,
  and the spread reported is the true probability-weighted standard deviation;
* the what-if conditions theta_k = 0 through ``eval.value.value(cond=...)``, and -- for the
  risk tables, which are computed from the claim set and not from theta -- re-runs
  ``eval.engine.recompute`` with the assumption's evidence withdrawn.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

from .adapter import eval_module
from .derive import Index
from .errors import UnknownId
from .scenarios import CRITERION_KEYS, Criterion

#: The weighting the v3 UI ships with. It is an operator preference, not dataset content:
#: every endpoint that uses it accepts an override, and reports the weights it applied.
DEFAULT_WEIGHTS: dict[str, int] = {
    "mission": 4, "personnel": 3, "escalation": 4, "time": 2, "resources": 1,
}

#: The perturbation applied to each weight, independently, for weight-stability. The full
#: Cartesian product of the clamped, de-duplicated per-weight values is enumerated, so the
#: answer is exact and deterministic rather than sampled. At most 5**5 = 3125 weightings;
#: fewer when a base weight sits near an end of the 0-5 range and the clamp collapses
#: values, which is why the response reports ``weightings_evaluated``.
WEIGHT_PERTURBATIONS = (-2, -1, 0, 1, 2)
WEIGHT_MIN, WEIGHT_MAX = 0, 5

WEIGHT_STABILITY_METHOD = (
    "exhaustive enumeration, no sampling: each of the five weights independently takes "
    f"w + d for d in {list(WEIGHT_PERTURBATIONS)}, clamped to "
    f"[{WEIGHT_MIN}, {WEIGHT_MAX}] and de-duplicated, and every combination in the "
    "Cartesian product of those value sets is scored (weightings_evaluated says how "
    "many). Ties on the weighted total go to the higher expected value, then the lower "
    "option number."
)

#: Ten bins over the utility scale, matching the histogram the UI draws.
BIN_COUNT = 10
BIN_DOMAIN = (0.0, 1.0)
BIN_NOTE = (
    "ten equal bins over the utility scale [0, 1]; an outcome below 0 falls in the first "
    "bin and one at or above 1 in the last, and the unclamped extremes are reported as "
    "outcome_range"
)

ADVERSARY_RANGE_BASIS = (
    "min and max of the option's expected value across the adversary COAs in its opponent "
    "model (eval.value.value_range). It is a spread over adversary behaviour, not a "
    "statistical confidence interval and not a casualty estimate."
)

P_MEETS_ASPIRATION_BASIS = (
    "the probability mass, over the enumerated assumption worlds weighted by P(theta) and "
    "the adversary COAs weighted by the opponent model, of the outcomes whose weighted "
    "utility is at or above the commander's aspiration w.tau. It is the probability the "
    "option meets the stated aspiration inside this model's enumerated worlds -- not a "
    "probability of success in the real world."
)

CRITERION_LEVEL_BASIS = (
    "shortfall = 1 - expected_value, binned by eval.jram.p_bin with the JRAM Fig. 6 "
    "probability bands, then read across to the like-ranked JRAM risk level "
    "(very_unlikely->low, unlikely->moderate, likely->significant, very_likely->high). "
    "Objective utilities are already stated as probabilities or fractions in the "
    "objectives table's metric column, which is the quantity Fig. 6 bins."
)

WHAT_IF_METHOD = {
    "value": (
        "eval.value.value with cond={k: 0}: the option's value conditioned on the "
        "assumption's world bit being false, exactly the quantity the assumption's "
        "sensitivity is a difference of. Risk assessments are held at their current values "
        "because they are computed from the claim set, not from theta."
    ),
    "status_ranking_and_risk": (
        "eval.engine.recompute re-run over the same tables with every approved claim on the "
        "assumption's (subject, predicate) withdrawn from the claim set: the evidence that "
        "grounds the assumption is gone, so statuses, the ranking, the risk assessments and "
        "the problem-set rollups are the engine's own output under that counterfactual."
    ),
}


# ---------------------------------------------------------------- JRAM level scale
def _jram():
    return eval_module("jram")


def level_scale() -> list[str]:
    """JRAM's low -> high risk levels (eval.jram.RISK_LEVELS)."""
    return list(_jram().RISK_LEVELS)


def level_score(level: str) -> int:
    """The UI's 4/3/2/1 mapping, derived from the scale's own order (best level = 4)."""
    levels = level_scale()
    return len(levels) - levels.index(level)


MAX_LEVEL_SCORE = 4  # len(jram.RISK_LEVELS); asserted in the tests against jram itself


def level_for(shortfall: float) -> str:
    """Bin a shortfall in [0, 1] onto the JRAM risk scale. No threshold is typed here."""
    jram = _jram()
    return list(jram.RISK_LEVELS)[list(jram.P_LEVELS).index(jram.p_bin(shortfall))]


def level_label(level: str) -> str:
    return _jram().RISK_LABEL[level]


def level_thresholds() -> list[dict]:
    """The documented threshold table, read out of ``eval.jram.P_BANDS``."""
    jram = _jram()
    rows, lower = [], 0.0
    for (p_level, upper), risk_level in zip(jram.P_BANDS, jram.RISK_LEVELS):
        rows.append({
            "level": risk_level,
            "label": jram.RISK_LABEL[risk_level],
            "score": level_score(risk_level),
            "shortfall_from": round(lower, 6),
            "shortfall_to": round(upper, 6),
            "jram_probability_band": p_level,
        })
        lower = upper
    return rows


# ---------------------------------------------------------------- option set
@dataclass(frozen=True)
class CriterionOutcome:
    criterion: Criterion
    expected_value: float
    shortfall: float
    level: str
    members: list[dict]


class OptionSet:
    """The friendly options of one loaded batch, scored on the five criteria."""

    def __init__(self, index: Index, criteria: tuple[Criterion, ...],
                 game_id: str, actor_id: str) -> None:
        self.index = index
        self.criteria = criteria
        self.game_id = game_id
        self.actor_id = actor_id
        self.value_mod = eval_module("value")
        self.engine = eval_module("engine")
        self.validity_mod = eval_module("validity")
        self.ids = sorted(
            s["strategy_id"]
            for s in index.rows("strategies")
            if (s["game_id"], s["actor_id"]) == (game_id, actor_id)
        )
        self.numbers = {sid: n for n, sid in enumerate(self.ids, start=1)}
        self.order = index.objective_order(game_id, actor_id)
        tables = index.snapshot.raw
        self.n_worlds, self.probabilities, _ = self.engine.assumption_vector(
            tables, game_id, actor_id, index.claimset, index.as_of
        )
        self.actions = index.by("actions", "action_id")
        self.resources = index.by("resources", "resource_id")
        self.objectives = index.objectives

    # ------------------------------------------------------------------ helpers
    def row(self, strategy_id: str) -> dict:
        if strategy_id not in self.numbers:
            raise UnknownId(
                f"no option {strategy_id!r} in this scenario at batch "
                f"{self.index.batch}. GET /api/options lists them.",
                {"strategy_id": strategy_id, "batch": self.index.batch,
                 "options": self.ids},
            )
        return self.index.strategies[strategy_id]

    def weights_for(self, strategy_id: str) -> list[float]:
        return self.engine.weights_for(
            self.index.snapshot.raw, strategy_id, self.order
        )

    def opponents(self, strategy_id: str) -> dict[str, float]:
        return self.index.opponent_dist(self.index.strategies[strategy_id])

    def value(self, strategy_id: str, cond: dict[int, int] | None = None) -> float:
        row = self.index.strategies[strategy_id]
        return self.value_mod.value(
            strategy_id, self.index.payoff_index, self.weights_for(strategy_id),
            self.opponents(strategy_id), self.probabilities, self.n_worlds,
            row["risk_functional"], row.get("risk_alpha"), cond,
        )

    def outcomes(self, strategy_id: str) -> list[tuple[float, float]]:
        """(probability, weighted utility) over every (assumption world, adversary COA)."""
        return self.value_mod.outcomes_for(
            strategy_id, self.index.payoff_index, self.weights_for(strategy_id),
            self.opponents(strategy_id), self.probabilities, self.n_worlds,
        )

    def tasks(self, strategy_id: str) -> list[str]:
        """The option's 'how': its policy rules as action names, in scheduled order."""
        rules = [
            r for r in self.index.rows("policy_rules")
            if r["strategy_id"] == strategy_id
        ]
        rules.sort(key=lambda r: (min(r["periods"]) if r.get("periods") else 10**6,
                                  r["rule_id"]))
        return [self.actions[r["action_id"]]["name"] for r in rules]

    # ------------------------------------------------------------------ criteria
    def criterion_outcome(self, strategy_id: str, criterion: Criterion) -> CriterionOutcome:
        if criterion.basis == "objectives":
            return self._objective_criterion(strategy_id, criterion)
        return self._resource_criterion(strategy_id, criterion)

    def _objective_criterion(self, strategy_id: str, criterion: Criterion) -> CriterionOutcome:
        own = dict(zip(self.order, self.weights_for(strategy_id)))
        members = [o for o in criterion.objectives if o in own]
        share = [own[o] for o in members]
        total = sum(share)
        if total <= 0:  # the option carries no weight there: score the members evenly
            share = [1.0] * len(members)
            total = float(len(members)) or 1.0
        weights = [
            (dict(zip(members, share)).get(objective_id, 0.0)) / total
            for objective_id in self.order
        ]
        expected = self.value_mod.value(
            strategy_id, self.index.payoff_index, weights, self.opponents(strategy_id),
            self.probabilities, self.n_worlds, "expected",
        )
        per_objective = self.index.contributions(strategy_id)
        detail = [
            {
                "id": objective_id,
                "name": self.objectives[objective_id]["name"],
                "weight_share": round(
                    (own.get(objective_id, 0.0) / total) if total else 0.0, 9
                ),
                "expected_value": round(per_objective.get(objective_id, 0.0), 9),
                "aspiration": self.objectives[objective_id].get("aspiration"),
            }
            for objective_id in members
        ]
        return CriterionOutcome(
            criterion=criterion,
            expected_value=expected,
            shortfall=1.0 - expected,
            level=level_for(1.0 - expected),
            members=detail,
        )

    def _resource_criterion(self, strategy_id: str, criterion: Criterion) -> CriterionOutcome:
        used = self.index.worst_case_cost(strategy_id)
        budgets = {
            sr["resource_id"]: sr["budget"]
            for sr in self.index.rows("strategy_resources")
            if sr["strategy_id"] == strategy_id
        }
        detail, utilisations = [], []
        for resource_id in criterion.resources:
            budget = budgets.get(resource_id, 0.0)
            need = used.get(resource_id, 0.0)
            utilisation = (need / budget) if budget > 0 else (1.0 if need > 0 else 0.0)
            utilisations.append(utilisation)
            resource = self.resources.get(resource_id, {})
            detail.append({
                "id": resource_id,
                "name": resource.get("name", resource_id),
                "unit": resource.get("unit"),
                "budget": budget,
                "worst_case_use": need,
                "utilisation": round(utilisation, 9),
            })
        shortfall = max(utilisations) if utilisations else 0.0
        shortfall = min(1.0, max(0.0, shortfall))
        return CriterionOutcome(
            criterion=criterion,
            expected_value=1.0 - shortfall,
            shortfall=shortfall,
            level=level_for(shortfall),
            members=detail,
        )

    def criterion_outcomes(self, strategy_id: str) -> list[CriterionOutcome]:
        return [self.criterion_outcome(strategy_id, c) for c in self.criteria]

    # ------------------------------------------------------------------ scoring
    def scores(self) -> dict[str, dict[str, int]]:
        """option id -> criterion key -> 4/3/2/1 level score. Computed once, reused."""
        return {
            sid: {out.criterion.key: level_score(out.level)
                  for out in self.criterion_outcomes(sid)}
            for sid in self.ids
        }

    def weighted_total(self, scores: dict[str, int], weights: dict[str, int]) -> int:
        return sum(weights[key] * scores[key] for key in CRITERION_KEYS)

    def weighted_max(self, weights: dict[str, int]) -> int:
        return sum(weights.values()) * MAX_LEVEL_SCORE

    def rank(self, scores: dict[str, dict[str, int]],
             weights: dict[str, int]) -> list[str]:
        """Best weighted total first; ties broken by expected value, then option number.

        The ordinal 4/3/2/1 scale is coarse enough that two options can tie on it while
        their expected values differ, so the tie-break names the one the evaluator's own
        value ordering prefers. It is deterministic either way.
        """
        return sorted(
            self.ids,
            key=lambda sid: (
                -self.weighted_total(scores[sid], weights),
                -self.index.strategies[sid]["value"],
                self.numbers[sid],
            ),
        )

    def weight_stability(self, scores: dict[str, dict[str, int]],
                         weights: dict[str, int]) -> dict:
        """Fraction of the enumerated perturbed weightings each option leads."""
        wins = {sid: 0 for sid in self.ids}
        axes = [
            sorted({min(WEIGHT_MAX, max(WEIGHT_MIN, weights[key] + d))
                    for d in WEIGHT_PERTURBATIONS})
            for key in CRITERION_KEYS
        ]
        # Pre-sort by the tie-break so only the weighted total has to be compared.
        ordered = sorted(self.ids, key=lambda sid: (-self.index.strategies[sid]["value"],
                                                    self.numbers[sid]))
        rows = [(sid, [scores[sid][key] for key in CRITERION_KEYS]) for sid in ordered]
        evaluated = 0
        for combination in itertools.product(*axes):
            evaluated += 1
            best_sid, best_total = None, None
            for sid, row in rows:
                total = sum(w * s for w, s in zip(combination, row))
                if best_total is None or total > best_total:
                    best_sid, best_total = sid, total
            wins[best_sid] += 1
        top = self.rank(scores, weights)[0]
        return {
            "top_option_id": top,
            "fraction_top": round(wins[top] / evaluated, 9),
            "weightings_evaluated": evaluated,
            "method": WEIGHT_STABILITY_METHOD,
            "per_option": [
                {"strategy_id": sid, "number": self.numbers[sid],
                 "fraction_top": round(wins[sid] / evaluated, 9)}
                for sid in sorted(self.ids, key=lambda s: (-wins[s], self.numbers[s]))
            ],
        }

    # ------------------------------------------------------------------ distribution
    def distribution(self, strategy_id: str) -> dict:
        outcomes = self.outcomes(strategy_id)
        row = self.index.strategies[strategy_id]
        aspiration = row["aspiration"]
        lower, upper = BIN_DOMAIN
        width = (upper - lower) / BIN_COUNT
        mass = [0.0] * BIN_COUNT
        count = [0] * BIN_COUNT
        total_mass = 0.0
        mean = 0.0
        for probability, outcome in outcomes:
            slot = min(BIN_COUNT - 1, max(0, int(math.floor((outcome - lower) / width))))
            mass[slot] += probability
            count[slot] += 1
            total_mass += probability
            mean += probability * outcome
        variance = sum(p * (x - mean) ** 2 for p, x in outcomes)
        supported = [x for p, x in outcomes if p > 0.0]
        meets = sum(p for p, x in outcomes if x >= aspiration - 1e-12)
        return {
            "strategy_id": strategy_id,
            "number": self.numbers[strategy_id],
            "title": row["name"],
            "aspiration": aspiration,
            "expected_value": row["value"],
            "mean_outcome": round(mean, 9),
            "std_dev": round(math.sqrt(max(0.0, variance)), 9),
            "p_meets_aspiration": round(meets, 9),
            "total_mass": round(total_mass, 12),
            "outcome_range": [round(min(supported), 9), round(max(supported), 9)],
            "assumption_worlds": 2 ** self.n_worlds,
            "adversary_coas": len(self.opponents(strategy_id)),
            "worlds": len(outcomes),
            "bins": [
                {
                    "index": i,
                    "lower": round(lower + i * width, 9),
                    "upper": round(lower + (i + 1) * width, 9),
                    "mass": round(mass[i], 12),
                    "count": count[i],
                }
                for i in range(BIN_COUNT)
            ],
        }


# ---------------------------------------------------------------- what-if
def _assumption_row(index: Index, assumption_id: str) -> dict:
    row = index.assumptions.get(assumption_id)
    if row is None:
        raise UnknownId(
            f"no assumption {assumption_id!r} in batch {index.batch}. "
            "GET /api/options lists each option's assumptions.",
            {"assumption_id": assumption_id, "batch": index.batch},
        )
    return row


def what_if(options: OptionSet, assumption_id: str) -> dict:
    """Recompute the comparison with one assumption failing.

    Two mechanisms, both named in the response's ``method``:

    * theta_k = 0 for the values, which is the exact conditional
      ``eval.value.value(cond={k: 0})``;
    * the assumption's evidence withdrawn for statuses, ranking and the risk tables, which
      ``eval.engine.recompute`` produces on its own.
    """
    index = options.index
    row = _assumption_row(index, assumption_id)
    k = row["index_k"]
    engine = options.engine

    before = {sid: index.strategies[sid]["value"] for sid in options.ids}
    conditioned = {sid: round(options.value(sid, {k: 0}), 9) for sid in options.ids}

    # --- the evidence-withdrawn recompute -----------------------------------------
    tables = index.snapshot.tables  # deep copy: the cache is never touched
    withdrawn = [
        claim["claim_id"] for claim in tables["claims"]
        if claim["subject_id"] == row["subject_id"]
        and claim["predicate"] == row["predicate"]
    ]
    remaining = [c for c in tables["claims"] if c["claim_id"] not in set(withdrawn)]
    after_tables = engine.recompute(tables, index.as_of, index.batch, claims=remaining)

    after_strategies = {s["strategy_id"]: s for s in after_tables["strategies"]}
    ranking_before = index.ranking(options.game_id, options.actor_id)
    ranking_withdrawn = list(
        engine.ranking(after_tables, options.game_id, options.actor_id)
    )
    # theta_k = 0 leaves validity alone, so the conditioned ranking re-sorts the options
    # that are valid today by their conditioned value, through eval.engine.ranking itself.
    conditioned_tables = {
        "strategies": [
            dict(index.strategies[sid], value=conditioned[sid]) for sid in options.ids
        ]
    }
    ranking_conditioned = list(
        engine.ranking(conditioned_tables, options.game_id, options.actor_id)
    )

    option_rows = []
    for sid in options.ids:
        current = index.strategies[sid]
        after = after_strategies[sid]
        option_rows.append({
            "strategy_id": sid,
            "number": options.numbers[sid],
            "title": current["name"],
            "value_before": current["value"],
            "value_after_conditioned": conditioned[sid],
            "delta_conditioned": round(conditioned[sid] - current["value"], 9),
            "value_after_withdrawn": after["value"],
            "status_before": current["status"],
            "status_after_withdrawn": after["status"],
            "status_changed": current["status"] != after["status"],
            "gates_failed_before": [
                name for name, r in current["validity"].items() if not r["pass"]
            ],
            "gates_failed_after_withdrawn": [
                name for name, r in after["validity"].items() if not r["pass"]
            ],
        })

    risk_before = index.risk_rows
    risk_after = {(r["he_id"], r["jsps_horizon"]): r
                  for r in after_tables["risk_assessments"]}
    events = index.harmful_events
    harmful_events_moved = [
        {
            "he_id": he_id,
            "statement": events[he_id]["statement"],
            "jsps_horizon": horizon,
            "level_before": risk_before[(he_id, horizon)]["risk_level"],
            "level_after": after["risk_level"],
            "p_before": risk_before[(he_id, horizon)]["p_raw"],
            "p_after": after["p_raw"],
        }
        for (he_id, horizon), after in sorted(risk_after.items(), key=lambda kv: kv[0])
        if (he_id, horizon) in risk_before
        and risk_before[(he_id, horizon)]["risk_level"] != after["risk_level"]
    ]

    ps_before = {(p["problem_set_id"], p["jsps_horizon"]): p
                 for p in index.rows("problem_set_assessments")}
    problem_sets = index.problem_sets
    problem_sets_moved = [
        {
            "problem_set_id": problem_set_id,
            "name": problem_sets[problem_set_id]["name"],
            "jsps_horizon": horizon,
            "level_before": ps_before[(problem_set_id, horizon)]["max_risk_level"],
            "level_after": after["max_risk_level"],
        }
        for (problem_set_id, horizon), after in sorted(
            (((p["problem_set_id"], p["jsps_horizon"]), p)
             for p in after_tables["problem_set_assessments"]),
            key=lambda kv: kv[0],
        )
        if (problem_set_id, horizon) in ps_before
        and ps_before[(problem_set_id, horizon)]["max_risk_level"] != after["max_risk_level"]
    ]

    after_assumption = next(
        (a for a in after_tables["assumptions"] if a["assumption_id"] == assumption_id),
        row,
    )
    return {
        "assumption": {
            "assumption_id": assumption_id,
            "index_k": k,
            "statement": row["statement"],
            "subject_id": row["subject_id"],
            "subject_name": index.entity_name(row["subject_id"]),
            "predicate": row["predicate"],
            "status": row["status"],
            "p_holds": row["p_holds"],
            "p_holds_after_withdrawn": after_assumption.get("p_holds"),
            "sensitivity": row["sensitivity"],
            "evpi": row["evpi"],
        },
        "method": dict(WHAT_IF_METHOD),
        "withdrawn_claim_ids": sorted(withdrawn),
        "options": option_rows,
        "ranking_before": ranking_before,
        "ranking_after_conditioned": ranking_conditioned,
        "ranking_after_withdrawn": ranking_withdrawn,
        "status_changes": [
            {
                "strategy_id": r["strategy_id"],
                "from_status": r["status_before"],
                "to": r["status_after_withdrawn"],
                "gates_failed_after": r["gates_failed_after_withdrawn"],
            }
            for r in option_rows if r["status_changed"]
        ],
        "harmful_events_moved": harmful_events_moved,
        "problem_sets_moved": problem_sets_moved,
    }
