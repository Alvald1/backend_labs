from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Response

from app import storage
from app.errors import ERROR_RESPONSES
from app.models import DEMO_USER_ID
from app.schemas.review import ReviewCreate, ReviewPatch, ReviewRead, ReviewReplace

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
async def list_reviews() -> list[ReviewRead]:
    return list(storage.reviews.values())


@router.post(
    "",
    response_model=ReviewRead,
    status_code=201,
    summary="Создать отзыв",
    description="Создаёт отзыв с серверными id и user_id. Неизвестный товар даёт 404, "
    "неверная оценка или другие поля — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def create_review(payload: ReviewCreate, response: Response) -> ReviewRead:
    if payload.product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    review = ReviewRead(id=uuid4(), user_id=DEMO_USER_ID, **payload.model_dump())
    storage.reviews[review.id] = review
    response.headers["Location"] = f"/api/v1/reviews/{review.id}"
    return review


@router.get(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Прочитать отзыв",
    description="Возвращает отзыв. Неизвестный UUID даёт 404, неверный формат — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def get_review(review_id: UUID) -> ReviewRead:
    if review_id not in storage.reviews:
        raise HTTPException(404, "Отзыв не найден")
    return storage.reviews[review_id]


@router.put(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Заменить отзыв",
    description="Полностью заменяет поля, сохраняя id и автора. Пропущенный текст станет "
    "null. Неизвестный отзыв или товар даёт 404, неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def replace_review(review_id: UUID, payload: ReviewReplace) -> ReviewRead:
    if review_id not in storage.reviews:
        raise HTTPException(404, "Отзыв не найден")
    if payload.product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    review = ReviewRead(
        id=review_id,
        user_id=storage.reviews[review_id].user_id,
        **payload.model_dump(),
    )
    storage.reviews[review_id] = review
    return review


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    summary="Изменить отзыв",
    description="Меняет только переданные поля. text=null очищает текст; rating и "
    "product_id не могут быть null. Неизвестный отзыв или товар даёт 404, "
    "неверные данные — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def patch_review(review_id: UUID, payload: ReviewPatch) -> ReviewRead:
    if review_id not in storage.reviews:
        raise HTTPException(404, "Отзыв не найден")
    if payload.product_id is not None and payload.product_id not in storage.products:
        raise HTTPException(404, "Товар не найден")
    review = storage.reviews[review_id].model_copy(update=payload.model_dump(exclude_unset=True))
    storage.reviews[review_id] = review
    return review


@router.delete(
    "/{review_id}",
    response_model=None,
    status_code=204,
    summary="Удалить отзыв",
    description="Удаляет отзыв без тела ответа. Неизвестный UUID даёт 404, "
    "неверный формат UUID — 422.",
    responses={404: ERROR_RESPONSES[404]},
)
async def delete_review(review_id: UUID) -> Response:
    if review_id not in storage.reviews:
        raise HTTPException(404, "Отзыв не найден")
    del storage.reviews[review_id]
    return Response(status_code=204)
