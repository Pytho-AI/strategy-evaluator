"""Routers, included by ``main.create_app``. Order matters: /api/strategies before /{id},
and /api/collection/drafts before /api/collection/{req_id}/..."""
from . import (
    claims, collection, injects, meta, options, planning, reports, risks, snapshot,
    strategies,
)

ROUTERS = (
    meta.router,
    injects.router,
    snapshot.router,
    strategies.router,
    options.router,
    reports.router,
    claims.router,
    risks.router,
    collection.router,
    planning.router,
)

__all__ = ["ROUTERS"]
