from uuid import UUID, uuid4

from app.exceptions.domain import CategoryNotEmpty, NotFound
from app.models import Category
from app.repositories.categories import CategoryRepository
from app.repositories.products import ProductRepository
from app.schemas.category import CategoryCreate, CategoryPatch, CategoryReplace


class CategoryService:
    def __init__(self, categories: CategoryRepository, products: ProductRepository):
        self._categories = categories
        self._products = products

    async def list_all(self) -> list[Category]:
        return await self._categories.list_all()

    async def get(self, category_id: UUID) -> Category:
        category = await self._categories.get(category_id)
        if category is None:
            raise NotFound("Категория", category_id)
        return category

    async def create(self, payload: CategoryCreate) -> Category:
        category = Category(id=uuid4(), **payload.model_dump())
        await self._categories.add(category)
        return category

    async def replace(self, category_id: UUID, payload: CategoryReplace) -> Category:
        category = await self.get(category_id)
        category.name = payload.name
        category.description = payload.description
        await self._categories.save(category)
        return category

    async def patch(self, category_id: UUID, payload: CategoryPatch) -> Category:
        category = await self.get(category_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        await self._categories.save(category)
        return category

    async def delete(self, category_id: UUID) -> None:
        category = await self.get(category_id)
        if await self._products.list_for_category(category_id):
            raise CategoryNotEmpty(category_id)
        await self._categories.delete(category)
