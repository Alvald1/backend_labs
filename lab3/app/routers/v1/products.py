from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies.services import get_product_service, get_user_id
from app.exceptions.handlers import ERROR_RESPONSES
from app.schemas.product import (
    ProductCondition,
    ProductCreate,
    ProductRead,
    ProductReplace,
    ProductSort,
)
from app.use_cases.products import ProductService

Service = Annotated[ProductService, Depends(get_product_service)]

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
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    condition: ProductCondition | None = None,
    min_price: Annotated[float | None, Query(ge=0, allow_inf_nan=False)] = None,
    max_price: Annotated[float | None, Query(ge=0, allow_inf_nan=False)] = None,
    sort_by: ProductSort = ProductSort.NAME,
) -> list[ProductRead]:
    items = await service.list_all(limit, offset, condition, min_price, max_price, sort_by)
    return [ProductRead.model_validate(item) for item in items]


@router.post(
    "",
    response_model=ProductRead,
    status_code=201,
    summary="Создать товар",
    description="Создаёт товар с серверными id и seller_id. Отсутствующая категория "
    "даёт 404, неверные поля или скидка выше цены — 422. "
    "Дубликат или превышение лимита — 409.",
    responses={404: ERROR_RESPONSES[404], 409: ERROR_RESPONSES[409]},
)
async def create_product(
    service: Service,
    payload: ProductCreate,
    response: Response,
    user_id: Annotated[UUID, Depends(get_user_id)],
) -> ProductRead:
    item = await service.create(payload, user_id)
    response.headers["Location"] = f"/api/v1/products/{item.id}"
    return ProductRead.model_validate(item)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Прочитать товар",
    description="Возвращает товар. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_product(service: Service, product_id: UUID) -> ProductRead:
    item = await service.get(product_id)
    return ProductRead.model_validate(item)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Заменить товар",
    description="Заменяет все доступные для записи поля, сохраняя id и продавца. "
    "Пропущенная скидка станет null, состояние — new. Неизвестный товар "
    "или категория даёт 404, неверные данные — 422. Дубликат или превышение лимита — 409.",
    responses={404: ERROR_RESPONSES[404], 409: ERROR_RESPONSES[409]},
)
async def replace_product(
    service: Service, product_id: UUID, payload: ProductReplace
) -> ProductRead:
    item = await service.replace(product_id, payload)
    return ProductRead.model_validate(item)


@router.delete(
    "/{product_id}",
    response_model=None,
    status_code=204,
    summary="Удалить товар",
    description="Удаляет товар вместе с отзывами. Неизвестный UUID даёт 404, неверный UUID — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def delete_product(service: Service, product_id: UUID) -> Response:
    await service.delete(product_id)
    return Response(status_code=204)
