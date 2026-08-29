import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import document, health, incident
from app.error_handlers import register_error_handlers
from app.logging_config import configure_logging

from time import perf_counter

from fastapi import Request

from app.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_started")
    yield
    logger.info("application_stopped")


app = FastAPI(
    debug=False,
    lifespan=lifespan,
)

@app.middleware("http")
async def record_http_metrics(
    request: Request,
    call_next,
):
    start_time = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = perf_counter() - start_time

        route = request.scope.get("route")
        route_path = getattr(
            route,
            "path",
            "unmatched",
        )

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            route=route_path,
            status_code=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            route=route_path,
        ).observe(duration)

@app.get("/metrics",include_in_schema=False,)
def metrics():
    return Response(
        content=generate_latest(),
        headers={
            "Content-Type": CONTENT_TYPE_LATEST,
        },
    )

register_error_handlers(app)

app.include_router(document.router)
app.include_router(health.router)
app.include_router(incident.router)

