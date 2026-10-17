from uuid import UUID, uuid4

from app.exceptions.domain import NotFound
from app.models import Review
from app.repositories.products import ProductRepository
from app.repositories.reviews import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewPatch, ReviewReplace


class ReviewService:
    def __init__(self, reviews: ReviewRepository, products: ProductRepository):
        self._reviews = reviews
        self._products = products

    async def list_all(self) -> list[Review]:
        return await self._reviews.list_all()

    async def get(self, review_id: UUID) -> Review:
        review = await self._reviews.get(review_id)
        if review is None:
            raise NotFound("Отзыв", review_id)
        return review

    async def _check_product(self, product_id: UUID) -> None:
        if await self._products.get(product_id) is None:
            raise NotFound("Товар", product_id)

    async def create(self, payload: ReviewCreate, user_id: UUID) -> Review:
        await self._check_product(payload.product_id)
        review = Review(id=uuid4(), user_id=user_id, **payload.model_dump())
        await self._reviews.add(review)
        return review

    async def replace(self, review_id: UUID, payload: ReviewReplace) -> Review:
        review = await self.get(review_id)
        await self._check_product(payload.product_id)
        for field, value in payload.model_dump().items():
            setattr(review, field, value)
        await self._reviews.save(review)
        return review

    async def patch(self, review_id: UUID, payload: ReviewPatch) -> Review:
        review = await self.get(review_id)
        product_id = payload.product_id if payload.product_id is not None else review.product_id
        await self._check_product(product_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(review, field, value)
        await self._reviews.save(review)
        return review

    async def delete(self, review_id: UUID) -> None:
        review = await self.get(review_id)
        await self._reviews.delete(review)
