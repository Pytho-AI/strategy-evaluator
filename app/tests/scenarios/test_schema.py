"""Every row validates against the dataset's pydantic models, and all twenty invariants pass.

Both checks reuse `dataset/gen/validate.py` rather than restating the rules. The corpus-reading
invariants (02 spans, 11-13 markings and vocabulary, 15-17 decision matrix, comparison tables and
the App. F caution, 20 acronyms) resolve `sources.path` against the scenario package rather than
against `dataset/`, so they take `scenario_root`.
"""
from __future__ import annotations

import pytest

SCENARIO_INVARIANTS = [f"{n:02d}" for n in range(1, 21)]
CORPUS_INVARIANTS = ["02", "11", "12", "13", "15", "16", "17", "20"]


def test_every_row_validates_against_its_model(validate, computed):
    result = validate.schema_load(computed)
    assert result.passed, result.detail


def test_authored_rows_validate_before_recompute(validate, authored):
    result = validate.schema_load(authored)
    assert result.passed, result.detail


@pytest.mark.parametrize("invariant", SCENARIO_INVARIANTS)
def test_dataset_invariant(validate, computed, scenario_root, S, invariant):
    results = validate.run_all(computed, scenario_root, S.AS_OF, S.WORLD_VERSION, only={invariant})
    assert len(results) == 1
    assert results[0].passed, f"invariant {invariant}: {results[0].detail}"


def test_the_corpus_reading_invariants_are_actually_exercised(computed, CORPUS=CORPUS_INVARIANTS):
    """They only mean something because there is a corpus to read: guard against them passing
    vacuously if the source rows ever went back to a single stand-in document."""
    assert set(CORPUS) <= set(SCENARIO_INVARIANTS)
    assert len(computed["sources"]) >= 10
    assert all(s["path"].startswith("corpus/") for s in computed["sources"])


def test_every_table_the_api_reads_is_populated(computed):
    from app.scenarios.amber_shield._dataset import eval_module

    assert set(computed) == set(eval_module("tables").TABLE_FILES)
    empty = sorted(name for name, rows in computed.items() if not rows)
    assert empty == [], f"empty tables: {empty}"


def test_entity_ids_use_typed_prefixes(computed):
    prefix_for = {
        "actor": "ent_", "polity": "ent_", "problem_set": "ent_", "location": "loc_",
        "infrastructure": "inf_", "unit": "unit_", "system": "sys_", "organization_role": "role_",
    }
    bad = [e["entity_id"] for e in computed["entities"]
           if not e["entity_id"].startswith(prefix_for[e["entity_type"]])]
    assert bad == []
    assert 60 <= len(computed["entities"]) <= 90


def test_marking_and_fiction_notice(build):
    assert build.SCENARIO["id"] == "amber_shield"
    assert build.SCENARIO["marking"].startswith("UNCLASSIFIED")
    assert "SYNTHETIC" in build.SCENARIO["marking"]
    assert "Not a real plan" in build.SCENARIO["fiction_notice"]


def test_registry_surface_the_backend_reads(build, S):
    """app/backend/scenarios.py::PackageAdapter reads these off the package."""
    assert build.BATCHES == (0,)
    assert build.as_of(0) == S.AS_OF.isoformat()
    assert build.GAME_ID == "amber_shield"
    assert build.ACTOR_ID == "ent_useucom"
    assert build.CRITERIA == ["obj_mission", "obj_personnel", "obj_escalation", "obj_time", "obj_resources"]
    assert build.load(through_batch=0)["strategies"]
    with pytest.raises(ValueError):
        build.load(through_batch=1)
