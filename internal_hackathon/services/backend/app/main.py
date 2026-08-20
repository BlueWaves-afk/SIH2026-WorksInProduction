"""The only FastAPI composition root for KisanSetu."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, check_database, engine

# Import models once so SQLAlchemy metadata and Alembic see every table.
from app import models as _models  # noqa: F401

logger = logging.getLogger("kisansetu")
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.env.lower() in {"local", "test"} and settings.database_url.startswith("sqlite"):
        # GeoAlchemy's PostGIS management functions are not available in the
        # SQLite fixture database used by local API tests.  The geography
        # tables are optional for replay/scoring and are created by Alembic in
        # Supabase/Postgres deployments.
        try:
            from geoalchemy2 import Geometry

            tables = [
                table
                for table in Base.metadata.sorted_tables
                if not any(isinstance(column.type, Geometry) for column in table.columns)
            ]
        except ImportError:  # pragma: no cover
            tables = list(Base.metadata.sorted_tables)
        Base.metadata.create_all(bind=engine, tables=tables)
    scheduler = None
    if settings.env.lower() != "test":
        from app.outreach.scheduler import start_scheduler

        scheduler = start_scheduler()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.project_name,
    version="2.0.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)


def _error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limited",
    }.get(status_code, "request_failed")


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": _error_code(exc.status_code), "message": message, "request_id": request_id},
        headers=exc.headers,
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_error(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": _error_code(exc.status_code), "message": message, "request_id": request_id},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Request validation failed",
            "request_id": request_id,
            "details": exc.errors(),
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled request failure", extra={"request_id": request_id})
        response = JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "Unexpected server error", "request_id": request_id},
        )
    logger.info(
        "request complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health", tags=["health"])
@app.get("/healthz", tags=["health"])
def health_check():
    return {"status": "ok", "service": "kisansetu-backend", "version": "2.0.0"}


@app.get("/readyz", tags=["health"])
def readiness_check():
    ready = check_database()
    return JSONResponse(status_code=200 if ready else 503, content={"status": "ready" if ready else "not_ready", "database": ready})


app.include_router(api_router, prefix=settings.api_v1_str)
