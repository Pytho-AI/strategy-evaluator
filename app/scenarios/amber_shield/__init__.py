"""USEUCOM Operation AMBER SHIELD: the computed scenario model behind the v3 UI.

    from app.scenarios.amber_shield import SCENARIO, load
    rows = load()            # {table_name: [row dict, ...]} with every computed column filled

`build` is imported lazily so that `python -m app.scenarios.amber_shield.build` does not execute
the module twice.
"""
from __future__ import annotations

__all__ = ["SCENARIO", "load", "tables"]


def __getattr__(name: str):
    if name in __all__:
        from . import build
        return getattr(build, name)
    raise AttributeError(name)
