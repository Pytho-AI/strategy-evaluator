"""FastAPI app and static UI for the Strategy Option Evaluation workbench."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .adapter import DatasetAdapter
from .branding import MARKING, PRODUCT_NAME
from .contracts import ErrorResponse
from .errors import DatasetError
from .routes import ROUTERS
from .routes.meta import DATASET_NAME
from .scenarios import ScenarioRegistry


def create_app(adapter: DatasetAdapter | None = None) -> FastAPI:
    if adapter is None:
        configured = os.environ.get("STRATEGY_DATASET_DIR")
        adapter = DatasetAdapter(Path(configured)) if configured else DatasetAdapter()

    app = FastAPI(
        title=f"{PRODUCT_NAME} — Strategy Option Evaluation API",
        description=(
            f"Read-only replay over {DATASET_NAME}. {MARKING}. "
            "Every computed value comes from dataset.load()/eval."
        ),
        version="0.2.0",
    )
    app.state.adapter = adapter
    # The scenario registry. ``meridian`` is served by exactly this adapter, so a test that
    # points the app at a copied dataset directory still gets that copy.
    app.state.scenarios = ScenarioRegistry(adapter)

    @app.exception_handler(DatasetError)
    async def _dataset_error(_: Request, exc: DatasetError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=ErrorResponse.model_validate(
                {"error": {"code": exc.code, "message": exc.message, "detail": exc.detail}}
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def _bad_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse.model_validate(
                {
                    "error": {
                        "code": "invalid_request",
                        "message": _validation_message(exc),
                        "detail": {"errors": _jsonable_errors(exc)},
                    }
                }
            ).model_dump(),
        )

    for router in ROUTERS:
        app.include_router(router)
    app_dir = Path(__file__).resolve().parents[1]
    wired_dir = app_dir / "ui-wired"
    if wired_dir.is_dir():
        # The API-backed workbench (Meridian Sea dataset). Mounted before "/" so it
        # keeps its own path while the demo shell owns the root.
        app.mount("/wired", StaticFiles(directory=wired_dir, html=True), name="wired")
    app.mount("/", StaticFiles(directory=app_dir / "ui", html=True), name="workbench")
    return app


def _validation_message(exc: RequestValidationError) -> str:
    locations = [str(error.get("loc", ())) for error in exc.errors()]
    if any("batch" in location for location in locations):
        return "batch must be an integer 0, 1, 2 or 3."
    if any("scenario" in location for location in locations):
        return "scenario must be a registered scenario id; GET /api/meta lists them."
    return "request parameters failed validation."


def _jsonable_errors(exc: RequestValidationError) -> list[dict]:
    return [
        {
            "loc": [str(part) for part in error.get("loc", ())],
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", "")),
        }
        for error in exc.errors()
    ]


app = create_app()
