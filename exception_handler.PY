from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
import logging
from schemas.errors import ERROR_CODES

import traceback

def error_response(request, status_code, code=None, message=None):
    default_code, default_message = ERROR_CODES.get(
        status_code,
        ("INTERNAL_ERROR", "An unexpected error occurred")
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "code": code or default_code,
            "message": message or default_message,
            "correlation_id": getattr(
                request.state, "correlation_id", "unavailable"
            )
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return error_response(
        request,
        exc.status_code
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return error_response(request, 422)


async def database_exception_handler(
    request: Request,
    exc: OperationalError
):
    return error_response(request, 503)


async def unexpected_exception_handler(
    request: Request,
    exc: Exception
):
    print("\n========== ACTUAL ERROR ==========", flush=True)
    traceback.print_exception(
        type(exc),
        exc,
        exc.__traceback__
    )
    print("==================================\n", flush=True)

    return error_response(request, 500)