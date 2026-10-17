from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorBody, ErrorDetail, ErrorResponse

ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Объект или связанный объект не найден"},
    405: {"model": ErrorResponse, "description": "Метод не поддерживается"},
    409: {"model": ErrorResponse, "description": "Объект используется другими записями"},
    422: {"model": ErrorResponse, "description": "Ошибка в теле, пути или параметрах запроса"},
}


def error_response(status_code, code, message, details=None, headers=None):
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in error["loc"]),
            rule=error["type"],
            message=error["msg"],
        )
        for error in exc.errors()
    ]
    return error_response(422, "validation_error", "Запрос не прошёл проверку", details)


async def http_error_handler(request: Request, exc: StarletteHTTPException):
    codes = {404: "not_found", 405: "method_not_allowed", 409: "conflict"}
    return error_response(
        exc.status_code,
        codes.get(exc.status_code, "http_error"),
        str(exc.detail),
        details=getattr(exc, "details", []),
        headers=exc.headers,
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    if getattr(exc.orig, "sqlstate", None) == "23503":
        return error_response(
            409, "conflict", "Операция запрещена: объект связан с другими записями"
        )
    return error_response(500, "internal_error", "Ошибка сохранения данных")
