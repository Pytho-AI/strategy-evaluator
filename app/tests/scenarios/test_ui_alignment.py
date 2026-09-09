"""The scenario says what the shipped v3 UI and the demo OPORD say.

If someone edits `app/ui/src/app.logic.js` or the OPORD without updating the scenario, these fail.
"""
from __future__ import annotations

import pytest

COA_DEPS = {"str_coa_1": [1, 2, 4, 5], "str_coa_2": [1, 4, 6, 8],
            "str_coa_3": [2, 4, 7], "str_coa_4": [1, 3, 6], "str_coa_5": [1, 3, 7, 8]}


def test_coa_names_approaches_and_concepts_are_verbatim_from_the_ui(S, ui_js):
    for sid, _ui, name, approach, *_ in S.COAS:
        assert f"'{name}'" in ui_js, name
        assert f"'{approach}'" in ui_js, approach
        assert f"'{S.CONCEPTS[sid]}'" in ui_js, sid


def test_coa_summary_carries_the_approach_and_the_concept(computed, S):
    for sid, _ui, _name, approach, *_ in S.COAS:
        s = next(x for x in computed["strategies"] if x["strategy_id"] == sid)
        assert s["summary"] == f"{approach}. {S.CONCEPTS[sid]}"


def test_assumption_dependencies_match_coa_lib(computed):
    by_strategy = {}
    for a in computed["assumptions"]:
        if a["strategy_id"].startswith("str_coa"):
            by_strategy.setdefault(a["strategy_id"], []).append(a["index_k"] + 1)
    assert {k: sorted(v) for k, v in by_strategy.items()} == COA_DEPS


def test_authored_constants_match_coa_lib(P, ui_js):
    for sid, values in P.AUTHORED.items():
        for field, value in values.items():
            token = f"{field}: {value:g}" if field != "days" and field != "res" else f"{field}: {value}"
            assert token in ui_js, f"{sid} {field}={value}"


def test_the_eight_assumptions_are_the_opord_assumptions(S, opord_text):
    assert len(S.ASSUMPTIONS) == 8
    for k, aid, *_rest in S.ASSUMPTIONS:
        statement = S.ASSUMPTIONS[k][-1]
        assert " ".join(statement.split()) in opord_text, aid
        assert aid == f"asm_a{k + 1}"


def test_assumption_ids_and_indices_are_the_ui_ordering(computed):
    rows = [a for a in computed["assumptions"] if a["strategy_id"].startswith("str_coa")]
    for a in rows:
        assert a["assumption_id"].startswith(f"asm_a{a['index_k'] + 1}_")
    assert {a["index_k"] for a in rows} == set(range(8))


def test_criteria_weights_are_the_ui_defaults(computed, S):
    assert S.UI_WEIGHTS_RAW == {"obj_mission": 4, "obj_personnel": 3, "obj_escalation": 4,
                                "obj_time": 2, "obj_resources": 1}
    for sid in [c[0] for c in S.COAS]:
        weights = {so["objective_id"]: so["weight"] for so in computed["strategy_objectives"]
                   if so["strategy_id"] == sid}
        assert sum(weights.values()) == pytest.approx(1.0)
        assert weights == pytest.approx(S.BLUE_WEIGHTS)


def test_constraints_and_restraints_come_from_the_ui_constraint_list(computed, S):
    assert len(S.CONSTRAINTS) == 4 and len(S.RESTRAINTS) == 4
    for s in computed["strategies"]:
        if not s["strategy_id"].startswith("str_coa"):
            continue
        assert S.CONSTRAINTS == s["constraints"][:4]
        assert len(s["constraints"]) == 5, "four command constraints plus one of the COA's own"
        assert s["restraints"] == S.RESTRAINTS


def test_the_ui_named_places_and_units_are_entities(computed):
    names = {e["canonical_name"] for e in computed["entities"]}
    names |= {alias for e in computed["entities"] for alias in e["aliases"]}
    for wanted in ("1st Armored Division", "2d Cavalry Regiment", "173rd Airborne Brigade",
                   "MND-N", "MND-NE", "Kaliningrad Oblast", "Suwalki corridor", "Daugava river line",
                   "Narva", "Klaipeda", "Gdansk", "Powidz", "Orzysz", "Baltic Sea",
                   "Army Prepositioned Stocks 2 site at Powidz", "S-400 surface-to-air missile system",
                   "Iskander-M missile system", "Kalibr land-attack cruise missile", "Baltic Fleet",
                   "Rail Baltica corridor", "Baltic sea line of communication"):
        assert wanted in names, wanted


def test_problem_set_entities_cover_the_ui_problem_set_map(computed, ui_js):
    assert "PROBLEM_SETS = {" in ui_js
    problem_sets = [e for e in computed["entities"] if e["entity_type"] == "problem_set"]
    assert len(problem_sets) == 8, "one problem-set entity per UI assumption cluster"
