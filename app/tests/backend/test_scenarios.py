"""The scenario registry: two scenarios, one server, and Meridian unchanged.

``client`` here is the pinned Meridian client every other module uses (conftest adds
``scenario=meridian``); ``default_client`` is a plain one, so a test can see what an
omitted ``scenario=`` actually resolves to.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.backend.scenarios import (
    AMBER_SHIELD,
    CRITERION_KEYS,
    DEFAULT_SCENARIO,
    FALLBACK_SCENARIO,
    MERIDIAN,
    ScenarioRegistry,
    coerce_criteria,
)

GOLDEN = Path(__file__).parent / "golden" / "meridian_replay_sha256.json"

BATCH_SCOPED = (
    "/api/snapshot",
    "/api/strategies",
    "/api/claims",
    "/api/risks",
    "/api/collection",
    "/api/planning",
    "/api/options",
    "/api/options/rank",
    "/api/options/outcome-distribution",
)


# ---------------------------------------------------------------- registry
def test_the_registry_holds_exactly_the_two_scenarios(adapter):
    registry = ScenarioRegistry(adapter)
    assert registry.ids == [MERIDIAN, AMBER_SHIELD]


def test_meridian_is_served_by_the_apps_own_adapter(adapter):
    """Not a second DatasetAdapter: a test that points the app at a copy still gets it."""
    registry = ScenarioRegistry(adapter)
    assert registry.adapter(MERIDIAN) is adapter


def test_the_default_is_a_single_constant_with_a_named_fallback(adapter):
    registry = ScenarioRegistry(adapter)
    assert DEFAULT_SCENARIO == AMBER_SHIELD
    assert FALLBACK_SCENARIO == MERIDIAN
    expected = DEFAULT_SCENARIO if registry.is_available(DEFAULT_SCENARIO) else FALLBACK_SCENARIO
    assert registry.default_id() == expected


def test_meta_lists_both_scenarios_with_availability(client):
    body = client.get("/api/meta").json()
    rows = {row["id"]: row for row in body["scenarios"]}
    assert set(rows) == {MERIDIAN, AMBER_SHIELD}
    assert body["default_scenario"] in rows
    assert rows[body["default_scenario"]]["default"] is True
    meridian = rows[MERIDIAN]
    assert meridian["available"] is True
    assert meridian["as_of"]
    assert meridian["marking"]
    assert meridian["counts"]["strategies"] > 0
    for row in rows.values():
        # An unavailable scenario says why instead of pretending it has data.
        assert row["available"] or row["unavailable_reason"]


@pytest.mark.parametrize("url", BATCH_SCOPED)
def test_an_unknown_scenario_is_422_and_names_the_valid_ids(client, url):
    response = client.get(url, params={"scenario": "no_such_scenario"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "unknown_scenario"
    assert error["detail"]["valid_scenarios"] == [MERIDIAN, AMBER_SHIELD]
    assert MERIDIAN in error["message"]


def test_an_omitted_scenario_resolves_to_the_registry_default(default_client):
    meta = default_client.get("/api/meta").json()
    body = default_client.get("/api/options").json()
    assert body["scenario"] == meta["default_scenario"]


def test_the_overlay_cache_is_keyed_on_the_scenario(adapter, workspace_id):
    """Two scenarios must never share a cache entry."""
    from app.backend.product.overlay import _CACHE, clear_cache, evaluate

    clear_cache()
    registry = ScenarioRegistry(adapter)
    evaluate(registry.adapter(MERIDIAN), 0, workspace_id, MERIDIAN)
    keys = list(_CACHE)
    assert len(keys) == 1
    scenario_id, identity, batch, workspace, graph_version, state_version = keys[0]
    assert scenario_id == MERIDIAN
    assert (batch, workspace) == (0, workspace_id)
    assert identity == adapter.identity.key
    assert isinstance(graph_version, int) and isinstance(state_version, int)


def test_criteria_accept_the_three_declared_shapes():
    from app.backend.scenarios import Criterion

    ids = coerce_criteria(["o1", "o2", "o3", "o4", "o5"], "x")
    assert [c.key for c in ids] == list(CRITERION_KEYS)
    assert ids[0].objectives == ("o1",)

    dicts = coerce_criteria(
        [{"key": key, "objectives": [key]} for key in CRITERION_KEYS], "x"
    )
    assert [c.key for c in dicts] == list(CRITERION_KEYS)

    rows = coerce_criteria(list(dicts), "x")
    assert rows == dicts
    assert all(isinstance(c, Criterion) for c in rows)


def test_criteria_in_the_wrong_order_are_refused():
    from app.backend.errors import ScenarioUnavailable

    with pytest.raises(ScenarioUnavailable):
        coerce_criteria(["a", "b", "c"], "x")


def test_a_scenario_whose_package_is_missing_reports_unavailable_not_a_crash(adapter):
    from app.backend.errors import ScenarioUnavailable
    from app.backend.scenarios import Scenario, _load_package

    registry = ScenarioRegistry(adapter)
    registry.scenarios["ghost"] = Scenario(
        id="ghost", name="Ghost",
        loader=_load_package("ghost", "app.scenarios.definitely_not_there.build"),
    )
    assert registry.is_available("ghost") is False
    row = next(r for r in registry.describe() if r["id"] == "ghost")
    assert row["available"] is False
    assert "not importable" in row["unavailable_reason"]
    with pytest.raises(ScenarioUnavailable):
        registry.adapter("ghost")


# ---------------------------------------------------------------- Meridian unchanged
def test_meridian_replay_bodies_are_unchanged_by_the_registry(client):
    """The default moved to amber_shield, so this is the proof Meridian did not move.

    The golden holds one SHA-256 per read-endpoint body, recorded from commit 5aa1f0e --
    the last commit before the scenario registry existed -- with ``load_ms`` and
    ``response_ms`` stripped, since those are timings and not content. Regenerate with
    ``docs``-free steps: check that commit out into a scratch tree, dump the same URLs, and
    hash each body the way ``_digest`` does.
    """
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["endpoints"]
    for url, expected in sorted(golden.items()):
        response = client.get(url)
        assert response.status_code == 200, url
        assert _digest(response.json()) == expected, (
            f"{url} changed against the pre-registry recording"
        )


def _digest(body: dict) -> str:
    return hashlib.sha256(
        json.dumps(_strip(body), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _strip(node):
    """Drop the two timing fields; everything else must match exactly."""
    if isinstance(node, dict):
        return {k: _strip(v) for k, v in node.items() if k not in ("load_ms", "response_ms")}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def test_the_golden_covers_every_read_endpoint_and_every_batch():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["endpoints"]
    for prefix in ("/api/snapshot", "/api/strategies?", "/api/risks", "/api/collection",
                   "/api/planning", "/api/claims?"):
        for batch in (0, 1, 2, 3):
            assert any(url.startswith(prefix) and f"batch={batch}" in url for url in golden), (
                f"{prefix} batch {batch} is not in the golden"
            )
    assert "/api/injects" in golden
    assert "/api/injects/3/diff" in golden


# ---------------------------------------------------------------- amber_shield smoke
def _amber_shield_reason() -> str | None:
    """None when it can be served; otherwise why not."""
    from app.backend.adapter import DatasetAdapter

    registry = ScenarioRegistry(DatasetAdapter())
    if registry.is_available(AMBER_SHIELD):
        return None
    return registry.scenarios[AMBER_SHIELD]._error or "not available"


AMBER_SHIELD_REASON = _amber_shield_reason()
amber_shield = pytest.mark.skipif(
    AMBER_SHIELD_REASON is not None,
    reason=f"the amber_shield package is not servable yet: {AMBER_SHIELD_REASON}",
)


@amber_shield
@pytest.mark.parametrize("url", BATCH_SCOPED)
def test_every_batch_scoped_endpoint_answers_for_amber_shield(default_client, url):
    response = default_client.get(url, params={"scenario": AMBER_SHIELD})
    assert response.status_code == 200, response.text


@amber_shield
def test_amber_shield_serves_its_own_options_not_meridians(default_client):
    body = default_client.get("/api/options", params={"scenario": AMBER_SHIELD}).json()
    assert body["scenario"] == AMBER_SHIELD
    assert body["options"], "amber_shield served no options"
    assert [o["number"] for o in body["options"]] == list(
        range(1, len(body["options"]) + 1)
    )
    meridian = default_client.get("/api/options", params={"scenario": MERIDIAN}).json()
    assert {o["strategy_id"] for o in body["options"]}.isdisjoint(
        {o["strategy_id"] for o in meridian["options"]}
    )


@amber_shield
def test_amber_shield_and_meridian_do_not_share_a_batch_cache(default_client):
    amber = default_client.get("/api/snapshot", params={"scenario": AMBER_SHIELD}).json()
    meridian = default_client.get("/api/snapshot", params={"scenario": MERIDIAN}).json()
    assert amber["decision_overview"]["scenario_id"] != (
        meridian["decision_overview"]["scenario_id"]
    )
    assert amber["as_of"] != meridian["as_of"]
