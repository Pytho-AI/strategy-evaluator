"""Missing dataset and incompatible schema must fail loudly, never fall back to mocks."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import MeridianClient
from fastapi.testclient import TestClient

from app.backend.adapter import DatasetAdapter
from app.backend.errors import DatasetMissing, SchemaIncompatible
from app.backend.main import create_app


def _client(dataset_dir: Path) -> TestClient:
    return MeridianClient(create_app(DatasetAdapter(dataset_dir)))


def test_missing_dataset_directory_returns_503(tmp_path: Path):
    client = _client(tmp_path / "not-here")
    for url in ("/api/health", "/api/meta", "/api/injects", "/api/snapshot?batch=0"):
        response = client.get(url)
        assert response.status_code == 503, url
        error = response.json()["error"]
        assert error["code"] == "dataset_missing"
        assert "not-here" in error["message"]
        assert "STRATEGY_DATASET_DIR" in error["message"]


def test_dataset_directory_without_truth_returns_503(tmp_path: Path):
    root = tmp_path / "dataset"
    root.mkdir()
    response = _client(root).get("/api/snapshot?batch=0")
    assert response.status_code == 503
    assert response.json()["error"]["detail"]["missing"] == "truth"


def test_missing_inject_manifest_returns_503(dataset_copy: Path):
    (dataset_copy / "injects" / "batch_2" / "manifest.json").unlink()
    response = _client(dataset_copy).get("/api/snapshot?batch=0")
    assert response.status_code == 503
    assert response.json()["error"]["detail"]["batch"] == 2


def test_tampered_schema_drops_a_column_the_api_reads(dataset_copy: Path):
    path = dataset_copy / "schema" / "strategies.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema["properties"].pop("value_ci")
    path.write_text(json.dumps(schema), encoding="utf-8")

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    assert "value_ci" in str(caught.value)

    response = _client(dataset_copy).get("/api/snapshot?batch=1")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "schema_incompatible"
    assert error["detail"]["missing_columns"] == ["value_ci"]


def _tamper(dataset_copy: Path, table: str, edit) -> Path:
    """Edit a copy of one schema file. dataset/ itself is never touched."""
    path = dataset_copy / "schema" / f"{table}.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    edit(schema)
    path.write_text(json.dumps(schema), encoding="utf-8")
    return path


def test_the_untampered_schema_passes_the_shape_check(dataset_copy: Path):
    """Control for the mutation tests below: an unedited copy preflights clean."""
    DatasetAdapter(dataset_copy).check()


def test_tampered_schema_changes_the_type_of_strategies_value(dataset_copy: Path):
    _tamper(dataset_copy, "strategies",
            lambda s: s["properties"].update(value={"type": "object"}))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    message = str(caught.value)
    assert "strategies" in message and "value" in message
    assert "number" in message and "object" in message

    response = _client(dataset_copy).get("/api/snapshot?batch=1")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "schema_incompatible"
    assert error["detail"]["property"] == "value"
    assert error["detail"]["expected"] == ["null", "number"]
    assert error["detail"]["found"] == ["object"]


def test_tampered_schema_changes_the_type_of_strategies_status(dataset_copy: Path):
    _tamper(dataset_copy, "strategies",
            lambda s: s["properties"].update(status={"type": "object"}))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    assert "status" in str(caught.value)


def test_tampered_schema_renames_a_strategy_status_enum_value(dataset_copy: Path):
    def rename(schema: dict) -> None:
        values = schema["$defs"]["StrategyStatus"]["enum"]
        values[values.index("invalid")] = "not_valid"

    _tamper(dataset_copy, "strategies", rename)

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    message = str(caught.value)
    assert "status" in message and "invalid" in message and "not_valid" in message


def test_tampered_schema_drops_a_strategy_status_enum_value(dataset_copy: Path):
    _tamper(dataset_copy, "strategies",
            lambda s: s["$defs"]["StrategyStatus"]["enum"].remove("infeasible"))

    with pytest.raises(SchemaIncompatible):
        DatasetAdapter(dataset_copy).check()


def test_tampered_schema_changes_the_nested_validity_structure(dataset_copy: Path):
    """validity.acceptable.pass is read as a boolean by the API."""
    _tamper(dataset_copy, "strategies",
            lambda s: s["$defs"]["ValidityResult"]["properties"].update(
                {"pass": {"type": "string"}}))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    message = str(caught.value)
    assert "validity" in message and "pass" in message and "boolean" in message


def test_tampered_schema_drops_a_nested_validity_test(dataset_copy: Path):
    _tamper(dataset_copy, "strategies",
            lambda s: s["$defs"]["Validity"]["properties"].pop("acceptable"))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    assert "acceptable" in str(caught.value)


def test_tampered_schema_changes_an_assumption_status_enum(dataset_copy: Path):
    _tamper(dataset_copy, "assumptions",
            lambda s: s["$defs"]["AssumptionStatus"]["enum"].remove("violated"))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    assert "violated" in str(caught.value)


def test_tampered_schema_changes_a_collection_requirement_status_enum(dataset_copy: Path):
    _tamper(dataset_copy, "collection_requirements",
            lambda s: s["$defs"]["ReqStatus"]["enum"].remove("satisfaction"))

    with pytest.raises(SchemaIncompatible) as caught:
        DatasetAdapter(dataset_copy).check()
    assert "satisfaction" in str(caught.value)


def test_tampered_schema_changes_a_primary_key(dataset_copy: Path):
    path = dataset_copy / "schema" / "collection_requirements.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    schema["x-primary-key"] = ["requirement_id"]
    path.write_text(json.dumps(schema), encoding="utf-8")

    response = _client(dataset_copy).get("/api/meta")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "schema_incompatible"


def test_deleted_schema_file_is_reported(dataset_copy: Path):
    (dataset_copy / "schema" / "assumptions.json").unlink()
    with pytest.raises(SchemaIncompatible):
        DatasetAdapter(dataset_copy).check()


def test_an_intact_copy_still_loads(dataset_copy: Path):
    response = _client(dataset_copy).get("/api/snapshot?batch=3")
    assert response.status_code == 200
    assert response.json()["strategies"]


def test_out_of_range_batch_raises_in_the_adapter(adapter: DatasetAdapter):
    with pytest.raises(ValueError):
        adapter.snapshot(4)


def test_dataset_missing_is_a_typed_error():
    assert DatasetMissing("x").http_status == 503
    assert SchemaIncompatible("x").http_status == 500
