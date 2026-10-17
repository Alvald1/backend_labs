from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.dependencies.services import get_review_service, get_user_id
from app.exceptions.handlers import ERROR_RESPONSES
from app.schemas.review import ReviewCreate, ReviewPatch, ReviewRead, ReviewReplace
from app.use_cases.reviews import ReviewService

Service = Annotated[ReviewService, Depends(get_review_service)]

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["reviews"],
    responses={422: ERROR_RESPONSES[422], 405: ERROR_RESPONSES[405]},
)


@router.get(
    "",
    response_model=list[ReviewRead],
    summary="Список отзывов",
    description="Возвращает все отзывы в порядке создания.",
)
async def list_reviews(service: Service) -> list[ReviewRead]:
    items = await service.list_all()
    return [ReviewRead.model_validate(item) for item in items]


@router.post(
    "",
    response_model=ReviewRead,
    status_code=201,
    summary="Создать отзыв",
    description="Создаёт отзыв с серверными id и user_id. Неизвестный товар даёт 404, "
    "неверная оценка или другие поля — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def create_review(
    service: Service,
    payload: ReviewCreate,
    response: Response,
    user_id: Annotated[UUID, Depends(get_user_id)],
) -> ReviewRead:
    item = await service.create(payload, user_id)
    response.headers["Location"] = f"/api/v1/reviews/{item.id}"
    return ReviewRead.model_validate(item)


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Прочитать отзыв",
    description="Возвращает отзыв. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_review(service: Service, review_id: UUID) -> ReviewRead:
    item = await service.get(review_id)
    return ReviewRead.model_validate(item)


@router.put(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Заменить отзыв",
    description="Полностью заменяет поля, сохраняя id и автора. Пропущенный текст станет "
    "null. Неизвестный отзыв или товар даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def replace_review(service: Service, review_id: UUID, payload: ReviewReplace) -> ReviewRead:
    item = await service.replace(review_id, payload)
    return ReviewRead.model_validate(item)


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Изменить отзыв",
    description="Меняет только переданные поля. text=null очищает текст; rating и "
    "product_id не могут быть null. Неизвестный отзыв или товар даёт 404, "
    "неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def patch_review(service: Service, review_id: UUID, payload: ReviewPatch) -> ReviewRead:
    item = await service.patch(review_id, payload)
    return ReviewRead.model_validate(item)


@router.delete(
    "/{review_id}",
    response_model=None,
    status_code=204,
    summary="Удалить отзыв",
    description="Удаляет отзыв без тела ответа. Неизвестный UUID даёт 404, "
    "неверный формат UUID — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def delete_review(service: Service, review_id: UUID) -> Response:
    await service.delete(review_id)
    return Response(status_code=204)
