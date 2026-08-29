import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    OperationalError,
    SQLAlchemyError,
    TimeoutError as SQLAlchemyTimeoutError,
)


logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    @app.exception_handler(OperationalError)
    @app.exception_handler(SQLAlchemyTimeoutError)
    async def database_unavailable_handler(
        request: Request,
        exception: Exception,
    ):
        logger.exception(
            "Database unavailable during %s %s",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database temporarily unavailable",
            },
        )
    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(
        request: Request,
        exception: SQLAlchemyError,
    ):
        logger.exception(
            "Database error during %s %s",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
            },
        )
    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request,
        exception: Exception,
    ):
        logger.exception(
            "Unexpected error during %s %s",
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
            },
        )