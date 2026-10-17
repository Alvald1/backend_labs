from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response

from app import storage
from app.errors import ERROR_RESPONSES
from app.schemas.category import CategoryCreate, CategoryPatch, CategoryRead, CategoryReplace

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
async def list_categories() -> list[CategoryRead]:
    return list(storage.categories.values())


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Создать категорию",
    description="Создаёт категорию. Лишние поля и неверное название дают 422.",
)
async def create_category(payload: CategoryCreate, response: Response) -> CategoryRead:
    category = CategoryRead(id=uuid4(), **payload.model_dump())
    storage.categories[category.id] = category
    response.headers["Location"] = f"/api/v1/categories/{category.id}"
    return category


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Прочитать категорию",
    description="Возвращает категорию. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_category(category_id: UUID) -> CategoryRead:
    if category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    return storage.categories[category_id]


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Заменить категорию",
    description="Полностью заменяет поля, сохраняя id. Пропущенное описание станет null. "
    "Неизвестный UUID даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def replace_category(category_id: UUID, payload: CategoryReplace) -> CategoryRead:
    if category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    category = CategoryRead(id=category_id, **payload.model_dump())
    storage.categories[category_id] = category
    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Изменить категорию",
    description="Меняет только переданные поля. description=null очищает описание; "
    "name=null запрещено. Неизвестный UUID даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def patch_category(category_id: UUID, payload: CategoryPatch) -> CategoryRead:
    if category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    category = storage.categories[category_id].model_copy(
        update=payload.model_dump(exclude_unset=True)
    )
    storage.categories[category_id] = category
    return category


@router.delete(
    "/{category_id}",
    response_model=None,
    status_code=204,
    summary="Удалить категорию",
    description="Удаляет пустую категорию. Неизвестный UUID даёт 404, неверный UUID — "
    "422. Если в категории есть товары, возвращает 409.",
    responses={404: ERROR_RESPONSES[404], 409: ERROR_RESPONSES[409]},
)
async def delete_category(category_id: UUID) -> Response:
    if category_id not in storage.categories:
        raise HTTPException(404, "Категория не найдена")
    if any(product.category_id == category_id for product in storage.products.values()):
        raise HTTPException(409, "В категории есть товары")
    del storage.categories[category_id]
    return Response(status_code=204)
