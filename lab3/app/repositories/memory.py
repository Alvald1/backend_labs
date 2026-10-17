from uuid import UUID

from app.models import Category, Product, Review


class MemoryCategoryRepository:
    def __init__(self):
        self._items: dict[UUID, Category] = {}

    async def list_all(self) -> list[Category]:
        return list(self._items.values())

    async def get(self, object_id: UUID) -> Category | None:
        return self._items.get(object_id)

    async def add(self, item: Category) -> None:
        self._items[item.id] = item

    async def save(self, item: Category) -> None:
        self._items[item.id] = item

    async def delete(self, item: Category) -> None:
        del self._items[item.id]


class MemoryReviewRepository:
    def __init__(self):
        self._items: dict[UUID, Review] = {}

    async def list_all(self) -> list[Review]:
        return list(self._items.values())

    async def get(self, object_id: UUID) -> Review | None:
        return self._items.get(object_id)

    async def add(self, item: Review) -> None:
        self._items[item.id] = item

    async def save(self, item: Review) -> None:
        self._items[item.id] = item

    async def delete(self, item: Review) -> None:
        del self._items[item.id]

    async def list_for_product(self, product_id: UUID) -> list[Review]:
        return [item for item in self._items.values() if item.product_id == product_id]


class MemoryProductRepository:
    def __init__(self, reviews: MemoryReviewRepository):
        self._items: dict[UUID, Product] = {}
        self._reviews = reviews

    async def list_all(self) -> list[Product]:
        return list(self._items.values())

    async def get(self, object_id: UUID) -> Product | None:
        return self._items.get(object_id)

    async def add(self, item: Product) -> None:
        self._items[item.id] = item

    async def save(self, item: Product) -> None:
        self._items[item.id] = item

    async def delete(self, item: Product) -> None:
        for review in await self._reviews.list_for_product(item.id):
            await self._reviews.delete(review)
        del self._items[item.id]

    async def list_for_category(self, category_id: UUID) -> list[Product]:
        return [item for item in self._items.values() if item.category_id == category_id]
