from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.dependencies.services import get_category_service
from app.exceptions.handlers import ERROR_RESPONSES
from app.schemas.category import CategoryCreate, CategoryPatch, CategoryRead, CategoryReplace
from app.use_cases.categories import CategoryService

Service = Annotated[CategoryService, Depends(get_category_service)]

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["categories"],
    responses={422: ERROR_RESPONSES[422], 405: ERROR_RESPONSES[405]},
)


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорий",
    description="Возвращает все категории в порядке создания.",
)
async def list_categories(service: Service) -> list[CategoryRead]:
    items = await service.list_all()
    return [CategoryRead.model_validate(item) for item in items]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Создать категорию",
    description="Создаёт категорию. Лишние поля и неверное название дают 422.",
)
async def create_category(
    service: Service, payload: CategoryCreate, response: Response
) -> CategoryRead:
    item = await service.create(payload)
    response.headers["Location"] = f"/api/v1/categories/{item.id}"
    return CategoryRead.model_validate(item)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Прочитать категорию",
    description="Возвращает категорию. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_category(service: Service, category_id: UUID) -> CategoryRead:
    item = await service.get(category_id)
    return CategoryRead.model_validate(item)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Заменить категорию",
    description="Полностью заменяет поля, сохраняя id. Пропущенное описание станет null. "
    "Неизвестный UUID даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def replace_category(
    service: Service, category_id: UUID, payload: CategoryReplace
) -> CategoryRead:
    item = await service.replace(category_id, payload)
    return CategoryRead.model_validate(item)


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Изменить категорию",
    description="Меняет только переданные поля. description=null очищает описание; "
    "name=null запрещено. Неизвестный UUID даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def patch_category(
    service: Service, category_id: UUID, payload: CategoryPatch
) -> CategoryRead:
    item = await service.patch(category_id, payload)
    return CategoryRead.model_validate(item)


@router.delete(
    "/{category_id}",
    response_model=None,
    status_code=204,
    summary="Удалить категорию",
    description="Удаляет пустую категорию. Неизвестный UUID даёт 404, неверный UUID — "
    "422. Если в категории есть товары, возвращает 409.",
    responses={404: ERROR_RESPONSES[404], 409: ERROR_RESPONSES[409]},
)
async def delete_category(service: Service, category_id: UUID) -> Response:
    await service.delete(category_id)
    return Response(status_code=204)
