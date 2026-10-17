from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response

from app import storage
from app.errors import ERROR_RESPONSES
from app.models import Product
from app.schemas.product import (
    ProductCondition,
    ProductCreate,
    ProductRead,
    ProductReplace,
    ProductSort,
)

router = APIRouter(
    prefix="/api/v1/products",
    tags=["products"],
    responses={422: ERROR_RESPONSES[422], 405: ERROR_RESPONSES[405]},
)


@router.get(
    "",
    response_model=list[ProductRead],
    summary="Список товаров",
    description="Сначала фильтрует по состоянию и включительным границам обычной цены, "
    "затем сортирует по возрастанию и выбирает страницу. limit: 1–100, "
    "offset: от 0. Неверные параметры дают 422.",
)
async def list_products(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    condition: ProductCondition | None = None,
    min_price: Annotated[float | None, Query(ge=0, allow_inf_nan=False)] = None,
    max_price: Annotated[float | None, Query(ge=0, allow_inf_nan=False)] = None,
    sort_by: ProductSort = ProductSort.NAME,
) -> list[ProductRead]:
    products = list(storage.products.values())
    if condition is not None:
        products = [product for product in products if product.condition == condition]
    if min_price is not None:
        products = [product for product in products if product.price >= min_price]
    if max_price is not None:
        products = [product for product in products if product.price <= max_price]
    products.sort(key=lambda product: getattr(product, sort_by.value))
    return [ProductRead(**product.model_dump()) for product in products[offset : offset + limit]]


@router.post(
    "",
    response_model=ProductRead,
    status_code=201,
    summary="Создать товар",
    description="Создаёт товар с серверными id и seller_id. Отсутствующая категория "
    "даёт 404, неверные поля или скидка выше цены — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def create_product(payload: ProductCreate, response: Response) -> ProductRead:
    if payload.category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    product = Product(**payload.model_dump())
    storage.products[product.id] = product
    response.headers["Location"] = f"/api/v1/products/{product.id}"
    return ProductRead(**product.model_dump())


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Прочитать товар",
    description="Возвращает товар. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_product(product_id: UUID) -> ProductRead:
    if product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    return ProductRead(**storage.products[product_id].model_dump())


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Заменить товар",
    description="Заменяет все доступные для записи поля, сохраняя id и продавца. "
    "Пропущенная скидка станет null, состояние — new. Неизвестный товар "
    "или категория даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def replace_product(product_id: UUID, payload: ProductReplace) -> ProductRead:
    if product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    if payload.category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    product = Product(
        id=product_id,
        seller_id=storage.products[product_id].seller_id,
        **payload.model_dump(),
    )
    storage.products[product_id] = product
    return ProductRead(**product.model_dump())


@router.delete(
    "/{product_id}",
    response_model=None,
    status_code=204,
    summary="Удалить товар",
    description="Удаляет товар без отзывов. Неизвестный UUID даёт 404, неверный UUID "
    "— 422. Если есть отзывы, возвращает 409.",
    responses={404: ERROR_RESPONSES[404], 409: ERROR_RESPONSES[409]},
)
async def delete_product(product_id: UUID) -> Response:
    if product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    if any(review.product_id == product_id for review in storage.reviews.values()):
        raise HTTPException(409, "У товара есть отзывы")
    del storage.products[product_id]
    return Response(status_code=204)
