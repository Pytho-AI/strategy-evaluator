"""FastAPI app for the Strategy Option Evaluation workbench (read-only replay API)."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .adapter import DatasetAdapter
from .branding import MARKING, PRODUCT_NAME
from .contracts import ErrorResponse
from .errors import DatasetError
from .routes import ROUTERS
from .routes.meta import DATASET_NAME


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
                        "message": (
                            "batch must be an integer 0, 1, 2 or 3."
                            if any("batch" in str(e.get("loc", ())) for e in exc.errors())
                            else "request parameters failed validation."
                        ),
                        "detail": {"errors": _jsonable_errors(exc)},
                    }
                }
            ).model_dump(),
        )

    for router in ROUTERS:
        app.include_router(router)
    return app


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
