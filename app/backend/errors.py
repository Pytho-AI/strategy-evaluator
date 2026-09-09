"""Typed errors. The API maps each to a JSON body with an actionable message."""
from __future__ import annotations


class DatasetError(Exception):
    """Base class for anything that makes the dataset unusable."""

    code = "dataset_error"
    http_status = 500

    def __init__(self, message: str, detail: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class DatasetMissing(DatasetError):
    """The dataset directory, or a directory the loader needs, is not there."""

    code = "dataset_missing"
    http_status = 503


class SchemaIncompatible(DatasetError):
    """The dataset is present but its schema no longer matches what the API reads."""

    code = "schema_incompatible"
    http_status = 500


class UnknownId(DatasetError):
    """A route was asked for an id the loaded batch does not contain."""

    code = "unknown_id"
    http_status = 404


class UnknownScenario(DatasetError):
    """A request named a scenario the registry does not have."""

    code = "unknown_scenario"
    http_status = 422


class ScenarioUnavailable(DatasetError):
    """A registered scenario's package is not importable yet, or is incomplete."""

    code = "scenario_unavailable"
    http_status = 503
