"""The scenario registry: which datasets this server can serve, and how it loads them.

Two entries ship:

``meridian``
    The frozen ``dataset/`` checkout, loaded through the existing ``DatasetAdapter``
    (``dataset.load`` -> ``eval.engine.recompute``). Unchanged behaviour; it stays the
    regression fixture, and a response served with ``scenario=meridian`` is the same body
    the server returned before the registry existed.

``amber_shield``
    Loaded from ``app.scenarios.amber_shield.build``. That package is being authored
    separately, so the import is lazy: until it exists ``/api/meta`` reports
    ``available: false`` with the import error, and asking for it returns 503
    ``scenario_unavailable`` rather than crashing the server.

What a scenario package must provide
------------------------------------
``app/scenarios/<id>/build.py`` (see ``PACKAGE_CONTRACT`` for the served version):

===============================  =========  ==================================================
name                             required   meaning
===============================  =========  ==================================================
``load(*, through_batch=0)``     yes        ``{table_name: pandas.DataFrame}`` with the same
                                            tables and columns ``dataset.load`` returns; the
                                            computed columns must already be filled by
                                            ``eval.engine.recompute``, exactly as
                                            ``dataset/loader.py`` does it
``BATCHES``                      no         batches it can load; default ``(0,)``
``as_of(batch)`` / ``AS_OF``     yes        the evaluation date of each batch (ISO)
``NAME``                         no         display name; default the scenario id
``VERSION`` / ``identity()``     no         cache-key component; default a SHA-256 over the
                                            package's own files, so an edit invalidates the
                                            cache without the package doing anything
``MARKING``                      no         default ``branding.MARKING``
``CRITERIA``                     for        the five UI criteria, as ``Criterion`` rows or
                                 /api/      plain dicts -- see ``Criterion`` and
                                 options    ``MERIDIAN_CRITERIA``
``GAME_ID`` / ``ACTOR_ID``       no         the friendly (game, actor) pair whose strategies
                                            are the options; default ``meridian``/``ent_blue``
``manifests()``                  no         inject manifests, for ``/api/injects``
``ROOT``                         no         directory that ``sources.path`` is relative to
===============================  =========  ==================================================
"""
from __future__ import annotations

import hashlib
import importlib
import inspect
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .adapter import (
    BATCHES as DATASET_BATCHES,
    BLUE_ACTOR_ID,
    BLUE_GAME_ID,
    BatchSnapshot,
    DatasetAdapter,
    DatasetIdentity,
    _records,
)
from .branding import MARKING
from .errors import ScenarioUnavailable, UnknownScenario

MERIDIAN = "meridian"
AMBER_SHIELD = "amber_shield"

#: What a ``scenario=`` that is not supplied resolves to, when it is available.
DEFAULT_SCENARIO = AMBER_SHIELD
#: What it resolves to instead while the default is still being authored.
FALLBACK_SCENARIO = MERIDIAN

PACKAGE_CONTRACT = (
    "app/scenarios/<id>/build.py must define load(*, through_batch=0) returning the same "
    "tables dataset.load returns with the computed columns already filled by "
    "eval.engine.recompute, as_of(batch) or AS_OF, and CRITERIA (the five UI criteria). "
    "BATCHES, NAME, VERSION/identity(), MARKING, GAME_ID, ACTOR_ID, manifests() and ROOT "
    "are optional."
)


# ---------------------------------------------------------------- criteria
@dataclass(frozen=True)
class Criterion:
    """One of the five comparison criteria the v3 UI scores an option on.

    Exactly one of ``objectives`` or ``resources`` is set.

    ``objectives``
        The scenario objectives this criterion covers. The criterion's expected value is
        ``eval.value.value`` with the option's own weights on those objectives, renormalised
        to sum to one (a single objective therefore reduces to E[u_k] exactly).
    ``resources``
        The scenario resources this criterion covers. The criterion's expected value is
        ``1 - max_r(worst_case_use_r / budget_r)`` -- the headroom left under the tightest
        budget, with ``worst_case_use`` from ``eval.validity.worst_case_cost``.
    """

    key: str
    label: str
    objectives: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()

    @property
    def basis(self) -> str:
        if self.objectives:
            return "objectives"
        return "resources"

    @property
    def members(self) -> tuple[str, ...]:
        return self.objectives or self.resources


#: The order the v3 UI lists them in, and the keys it sends weights under.
CRITERION_KEYS = ("mission", "personnel", "escalation", "time", "resources")

#: The labels the v3 UI prints, used when a scenario declares only the member ids.
CRITERION_LABELS = {
    "mission": "Risk to mission",
    "personnel": "Risk to personnel",
    "escalation": "Risk of escalation",
    "time": "Time to end state",
    "resources": "Force demand vs GFM",
}

# Meridian's map. Every objective the Blue options carry weight on appears exactly once;
# ``time`` and ``resources`` are read off the resource budgets because the Meridian
# objectives do not measure schedule or force demand.
MERIDIAN_CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        "mission",
        CRITERION_LABELS["mission"],
        objectives=("obj_deter", "obj_navigation"),
    ),
    Criterion("personnel", CRITERION_LABELS["personnel"],
              objectives=("obj_preserve_force",)),
    Criterion("escalation", CRITERION_LABELS["escalation"],
              objectives=("obj_limit_escalation",)),
    Criterion("time", CRITERION_LABELS["time"], resources=("res_sustain_days",)),
    Criterion(
        "resources",
        CRITERION_LABELS["resources"],
        resources=("res_isr_hours", "res_lift", "res_munitions", "res_sorties"),
    ),
)


def coerce_criteria(raw: Any, scenario_id: str) -> tuple[Criterion, ...]:
    """Accept any of the three shapes a scenario package may declare ``CRITERIA`` in.

    * ``Criterion`` rows -- the full form;
    * dicts ``{key, label, objectives | resources}`` -- the same thing without importing us;
    * five objective ids in the UI's own order, when the scenario authors one objective per
      criterion (which is what ``amber_shield`` does: ``obj_mission`` .. ``obj_resources``).
    """
    items = list(raw or ())
    if items and all(isinstance(item, str) for item in items):
        if len(items) != len(CRITERION_KEYS):
            raise ScenarioUnavailable(
                f"scenario {scenario_id!r} declares CRITERIA as {len(items)} objective ids; "
                f"the five UI criteria {list(CRITERION_KEYS)} need five, in that order.",
                {"scenario": scenario_id, "found": items},
            )
        items = [
            {"key": key, "label": CRITERION_LABELS[key], "objectives": [objective_id]}
            for key, objective_id in zip(CRITERION_KEYS, items)
        ]
    out: list[Criterion] = []
    for item in items:
        if isinstance(item, Criterion):
            out.append(item)
            continue
        if not isinstance(item, dict):
            raise ScenarioUnavailable(
                f"scenario {scenario_id!r} declares a criterion that is neither a "
                f"Criterion, a dict nor an objective id: {item!r}.",
                {"scenario": scenario_id},
            )
        out.append(
            Criterion(
                key=item["key"],
                label=item.get("label") or CRITERION_LABELS.get(item["key"], item["key"]),
                objectives=tuple(item.get("objectives") or ()),
                resources=tuple(item.get("resources") or ()),
            )
        )
    keys = [c.key for c in out]
    if keys != list(CRITERION_KEYS):
        raise ScenarioUnavailable(
            f"scenario {scenario_id!r} must declare exactly the five criteria "
            f"{list(CRITERION_KEYS)} in that order; it declares {keys}.",
            {"scenario": scenario_id, "expected": list(CRITERION_KEYS), "found": keys},
        )
    return tuple(out)


# ---------------------------------------------------------------- package attributes
def package_attr(module: Any, *names: str, default: Any = None) -> Any:
    """Read a declaration off a scenario package, in the three places one can sit.

    ``build.<NAME>`` first, then ``build.SCENARIO[<name lowercased>]`` (the dict shape
    ``amber_shield`` uses), then ``<package>.scenario.<NAME>``. Everything is optional; the
    first hit wins, and ``None`` counts as absent.
    """
    for name in names:
        value = getattr(module, name, None)
        if value is not None:
            return value
    scenario_dict = getattr(module, "SCENARIO", None)
    if isinstance(scenario_dict, dict):
        for name in names:
            value = scenario_dict.get(name.lower())
            if value is not None:
                return value
    package = getattr(module, "__package__", "") or ""
    if package:
        try:
            sibling = importlib.import_module(f"{package}.scenario")
        except Exception:
            sibling = None
        if sibling is not None:
            for name in names:
                value = getattr(sibling, name, None)
                if value is not None:
                    return value
    return default


def call_load(module: Any, batch: int) -> dict:
    """``load(through_batch=batch)`` when the package takes batches, else ``load()``."""
    load = module.load
    try:
        parameters = inspect.signature(load).parameters
    except (TypeError, ValueError):
        parameters = {}
    if "through_batch" in parameters:
        return load(through_batch=batch)
    return load()


# ---------------------------------------------------------------- package adapter
class PackageAdapter(DatasetAdapter):
    """A ``DatasetAdapter`` whose tables come from a scenario package, not from ``dataset/``.

    Only the loading half is replaced. Caching, deep-copy handout, the ``Index`` join layer
    and every eval bridge are the base class's, so a package scenario is served by the same
    code path the frozen dataset is.
    """

    def __init__(self, scenario_id: str, module: Any) -> None:
        root = package_attr(module, "ROOT") or Path(module.__file__).resolve().parent
        super().__init__(Path(root))
        self.scenario_id = scenario_id
        self.module = module
        self._batches = tuple(package_attr(module, "BATCHES", default=(0,)))

    @property
    def batches(self) -> tuple[int, ...]:
        return self._batches

    @property
    def identity(self) -> DatasetIdentity:
        if self._identity is None:
            version = package_attr(self.module, "VERSION")
            if version is None:
                identity_fn = getattr(self.module, "identity", None)
                version = identity_fn() if callable(identity_fn) else None
            if version is None:
                version = _package_digest(Path(self.module.__file__).resolve().parent)
            key = f"{self.scenario_id}:{version}"
            self._identity = DatasetIdentity(
                archive_sha256=None, git_head=None, key=key
            )
        return self._identity

    def check(self) -> None:
        if self._checked:
            return
        if not callable(getattr(self.module, "load", None)):
            raise ScenarioUnavailable(
                f"scenario {self.scenario_id!r} has no load(). {PACKAGE_CONTRACT}",
                {"scenario": self.scenario_id},
            )
        self._checked = True

    def as_of(self, batch: int) -> str:
        as_of_fn = getattr(self.module, "as_of", None)
        if callable(as_of_fn):
            return str(as_of_fn(batch))
        table = package_attr(self.module, "AS_OF")
        if isinstance(table, dict):
            if batch in table:
                return str(table[batch])
        elif table is not None:
            return str(table)
        raise ScenarioUnavailable(
            f"scenario {self.scenario_id!r} states no as-of date for batch {batch}. "
            "Define as_of(batch) or AS_OF = {batch: 'YYYY-MM-DD'}.",
            {"scenario": self.scenario_id, "batch": batch},
        )

    def manifest(self, batch: int) -> dict:
        manifest_fn = getattr(self.module, "manifest", None)
        if callable(manifest_fn):
            return manifest_fn(batch)
        return {"batch": batch, "as_of": self.as_of(batch), "docs": [],
                "change_events": [], "expected_effects": {}}

    def manifests(self) -> list[dict]:
        manifests_fn = getattr(self.module, "manifests", None)
        if callable(manifests_fn):
            return list(manifests_fn())
        return [self.manifest(b) for b in self._batches if b != 0]

    def snapshot(self, batch: int) -> BatchSnapshot:
        if batch not in self._batches:
            raise UnknownScenario(
                f"scenario {self.scenario_id!r} has no batch {batch}; it loads "
                f"{list(self._batches)}.",
                {"scenario": self.scenario_id, "batch": batch,
                 "valid_batches": list(self._batches)},
            )
        self.check()
        key = (self.identity.key, batch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        started = time.perf_counter()
        try:
            frames = call_load(self.module, batch)
        except Exception as exc:  # the package is still being written
            raise ScenarioUnavailable(
                f"scenario {self.scenario_id!r} failed to load batch {batch}: "
                f"{type(exc).__name__}: {exc}",
                {"scenario": self.scenario_id, "batch": batch},
            ) from exc
        tables = {
            name: (frame if isinstance(frame, list) else _records(frame))
            for name, frame in frames.items()
        }
        try:
            self._verify_loaded(tables)
        except Exception as exc:
            raise ScenarioUnavailable(
                f"scenario {self.scenario_id!r} loaded tables the API cannot read: {exc}",
                {"scenario": self.scenario_id, "batch": batch},
            ) from exc
        snapshot = BatchSnapshot(
            batch=batch,
            as_of=self.as_of(batch),
            load_ms=round((time.perf_counter() - started) * 1000.0, 3),
            _tables=tables,
        )
        self._cache[key] = snapshot
        return snapshot


def _package_digest(root: Path) -> str:
    """SHA-256 over a package's own files: an edit changes the cache key by itself."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


# ---------------------------------------------------------------- registry
@dataclass
class Scenario:
    """One registry entry. ``loader`` is called at most once per registry."""

    id: str
    name: str
    loader: Callable[["ScenarioRegistry"], DatasetAdapter]
    criteria: tuple[Criterion, ...] | None = None
    game_id: str = BLUE_GAME_ID
    actor_id: str = BLUE_ACTOR_ID
    marking: str = MARKING
    batches: tuple[int, ...] = DATASET_BATCHES
    _adapter: DatasetAdapter | None = field(default=None, repr=False)
    _error: str | None = field(default=None, repr=False)
    _available: bool | None = field(default=None, repr=False)


def _load_meridian(registry: "ScenarioRegistry") -> DatasetAdapter:
    """The frozen dataset, through the adapter the server was constructed with."""
    return registry.root_adapter


def _load_package(scenario_id: str, module_path: str):
    def loader(registry: "ScenarioRegistry") -> DatasetAdapter:
        try:
            module = importlib.import_module(module_path)
        except Exception as exc:  # ModuleNotFoundError while it is being authored
            raise ScenarioUnavailable(
                f"scenario {scenario_id!r} is registered but {module_path} is not "
                f"importable yet ({type(exc).__name__}: {exc}). {PACKAGE_CONTRACT}",
                {"scenario": scenario_id, "module": module_path},
            ) from exc
        return PackageAdapter(scenario_id, module)

    return loader


class ScenarioRegistry:
    """Scenario id -> loaded adapter. One per app; lives on ``app.state.scenarios``."""

    def __init__(self, root_adapter: DatasetAdapter) -> None:
        self.root_adapter = root_adapter
        self.scenarios: dict[str, Scenario] = {
            MERIDIAN: Scenario(
                id=MERIDIAN,
                name="Meridian Sea",
                loader=_load_meridian,
                criteria=MERIDIAN_CRITERIA,
                batches=DATASET_BATCHES,
            ),
            AMBER_SHIELD: Scenario(
                id=AMBER_SHIELD,
                name="Operation Amber Shield",
                loader=_load_package(AMBER_SHIELD, "app.scenarios.amber_shield.build"),
                criteria=None,
                batches=DATASET_BATCHES,
            ),
        }

    # ------------------------------------------------------------------ ids
    @property
    def ids(self) -> list[str]:
        return list(self.scenarios)

    def resolve(self, scenario_id: str | None) -> str:
        """Validate an id, or pick the default: ``amber_shield`` when it loads, else ``meridian``."""
        if scenario_id is None:
            return self.default_id()
        if scenario_id not in self.scenarios:
            raise UnknownScenario(
                f"unknown scenario {scenario_id!r}. Valid ids: {', '.join(self.ids)}.",
                {"scenario": scenario_id, "valid_scenarios": self.ids},
            )
        return scenario_id

    def default_id(self) -> str:
        return DEFAULT_SCENARIO if self.is_available(DEFAULT_SCENARIO) else FALLBACK_SCENARIO

    # ------------------------------------------------------------------ adapters
    def entry(self, scenario_id: str) -> Scenario:
        return self.scenarios[self.resolve(scenario_id)]

    def adapter(self, scenario_id: str | None = None) -> DatasetAdapter:
        entry = self.entry(self.resolve(scenario_id))
        if entry._adapter is None:
            adapter = entry.loader(self)
            entry._adapter = adapter
            entry.batches = tuple(getattr(adapter, "batches", entry.batches))
            module = getattr(adapter, "module", None)
            if module is not None:
                entry.name = str(package_attr(module, "NAME", default=entry.name))
                entry.marking = str(package_attr(module, "MARKING", default=entry.marking))
                entry.game_id = str(package_attr(module, "GAME_ID", default=entry.game_id))
                # ``BLUE`` is what a package that names its actors by colour calls the
                # friendly one; ``ACTOR_ID`` is the neutral spelling.
                entry.actor_id = str(
                    package_attr(module, "ACTOR_ID", "BLUE", default=entry.actor_id)
                )
                if entry.criteria is None:
                    entry.criteria = coerce_criteria(
                        package_attr(module, "CRITERIA"), entry.id
                    )
        return entry._adapter

    def criteria(self, scenario_id: str) -> tuple[Criterion, ...]:
        entry = self.entry(scenario_id)
        self.adapter(entry.id)
        if not entry.criteria:
            raise ScenarioUnavailable(
                f"scenario {entry.id!r} declares no CRITERIA, so the five comparison "
                f"criteria cannot be scored. {PACKAGE_CONTRACT}",
                {"scenario": entry.id, "expected": list(CRITERION_KEYS)},
            )
        return entry.criteria

    def is_available(self, scenario_id: str) -> bool:
        """Can this scenario actually be served?

        Importing the package is not enough -- a half-written ``load()`` imports fine and
        then raises. The probe loads the scenario's first batch, which is what every
        endpoint needs, and caches the answer. It is why an unfinished package cannot
        become the default and 503 every request.
        """
        entry = self.scenarios[scenario_id]
        if entry._available is not None:
            return entry._available
        try:
            adapter = self.adapter(scenario_id)
            adapter.snapshot(min(entry.batches))
        except Exception as exc:
            entry._error = str(exc)
            entry._available = False
            return False
        entry._available = True
        return True

    def check_batch(self, scenario_id: str, batch: int) -> None:
        entry = self.entry(scenario_id)
        self.adapter(entry.id)
        if batch not in entry.batches:
            raise UnknownScenario(
                f"scenario {entry.id!r} has no batch {batch}; it loads "
                f"{list(entry.batches)}.",
                {"scenario": entry.id, "batch": batch,
                 "valid_batches": list(entry.batches)},
            )

    # ------------------------------------------------------------------ meta
    def describe(self) -> list[dict]:
        """One row per registered scenario for ``/api/meta``. Never raises."""
        out = []
        for scenario_id, entry in self.scenarios.items():
            available = self.is_available(scenario_id)
            row: dict[str, Any] = {
                "id": scenario_id,
                "name": entry.name,
                "available": available,
                "default": scenario_id == self.default_id(),
                "marking": entry.marking,
                "batches": list(entry.batches),
                "as_of": None,
                "counts": {},
                "unavailable_reason": entry._error,
            }
            if available:
                snapshot = self.adapter(scenario_id).snapshot(max(entry.batches))
                row["as_of"] = snapshot.as_of
                row["counts"] = snapshot.table_counts
            out.append(row)
        return out
