from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Product, Review


class SqlAlchemyCategoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[Category]:
        result = await self._session.scalars(
            select(Category).order_by(Category.created_at, Category.id)
        )
        return list(result)

    async def get(self, object_id: UUID) -> Category | None:
        return await self._session.get(Category, object_id)

    async def add(self, item: Category) -> None:
        self._session.add(item)
        await self._session.flush()

    async def save(self, item: Category) -> None:
        await self._session.flush()

    async def delete(self, item: Category) -> None:
        await self._session.delete(item)
        await self._session.flush()


class SqlAlchemyProductRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[Product]:
        result = await self._session.scalars(
            select(Product).order_by(Product.created_at, Product.id)
        )
        return list(result)

    async def get(self, object_id: UUID) -> Product | None:
        return await self._session.get(Product, object_id)

    async def add(self, item: Product) -> None:
        self._session.add(item)
        await self._session.flush()

    async def save(self, item: Product) -> None:
        await self._session.flush()

    async def delete(self, item: Product) -> None:
        await self._session.delete(item)
        await self._session.flush()

    async def list_for_category(self, category_id: UUID) -> list[Product]:
        result = await self._session.scalars(
            select(Product).where(Product.category_id == category_id)
        )
        return list(result)


class SqlAlchemyReviewRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self) -> list[Review]:
        result = await self._session.scalars(select(Review).order_by(Review.created_at, Review.id))
        return list(result)

    async def get(self, object_id: UUID) -> Review | None:
        return await self._session.get(Review, object_id)

    async def add(self, item: Review) -> None:
        self._session.add(item)
        await self._session.flush()

    async def save(self, item: Review) -> None:
        await self._session.flush()

    async def delete(self, item: Review) -> None:
        await self._session.delete(item)
        await self._session.flush()
