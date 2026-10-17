from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.database import engine
from app.exceptions.handlers import (
    ERROR_RESPONSES,
    http_error_handler,
    integrity_error_handler,
    validation_error_handler,
)
from app.routers.v1 import categories, products, reviews

get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    lifespan=lifespan,
    title="Каталог товаров",
    version="0.3.0",
    description="Учебный API каталога товаров, категорий и отзывов. "
    "Хранилище выбирается настройкой: PostgreSQL или память. "
    "Вместо аутентификации используется фиксированный пользователь.",
    openapi_tags=[
        {"name": "categories", "description": "Категории каталога"},
        {"name": "products", "description": "Товары, цены и остатки"},
        {"name": "reviews", "description": "Отзывы покупателей о товарах"},
        {"name": "health", "description": "Проверка доступности приложения"},
    ],
)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(reviews.router)


class HealthRead(BaseModel):
    status: str
    service: str
    version: str


@app.get(
    "/health",
    response_model=HealthRead,
    tags=["health"],
    summary="Проверить состояние",
    description="Возвращает состояние и версию работающего приложения.",
    responses={405: ERROR_RESPONSES[405]},
)
async def health() -> HealthRead:
    return HealthRead(status="ok", service="product-catalog", version="0.3.0")
