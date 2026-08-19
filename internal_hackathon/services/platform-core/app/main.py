"""FastAPI app factory — mounts every module's router. See module_1 spec §4."""
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Platform API", version="0.1.0")
    # TODO(M1): observability middleware (request id, structured logging)
    # TODO(M1): exception handlers -> ErrorEnvelope
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()


@app.get("/healthz", tags=["ops"])
async def healthz() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
