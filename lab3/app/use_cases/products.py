from uuid import UUID, uuid4

from app.exceptions.domain import DuplicateProduct, NotFound, StockLimitExceeded
from app.models import Product
from app.repositories.categories import CategoryRepository
from app.repositories.products import ProductRepository
from app.schemas.product import ProductCondition, ProductCreate, ProductReplace, ProductSort


class ProductService:
    def __init__(self, products: ProductRepository, categories: CategoryRepository, max_stock: int):
        self._products = products
        self._categories = categories
        self._max_stock = max_stock

    async def list_all(
        self,
        limit: int,
        offset: int,
        condition: ProductCondition | None,
        min_price: float | None,
        max_price: float | None,
        sort_by: ProductSort,
    ) -> list[Product]:
        products = await self._products.list_all()
        if condition is not None:
            products = [product for product in products if product.condition == condition]
        if min_price is not None:
            products = [product for product in products if product.price >= min_price]
        if max_price is not None:
            products = [product for product in products if product.price <= max_price]
        products.sort(key=lambda product: getattr(product, sort_by.value))
        return products[offset : offset + limit]

    async def get(self, product_id: UUID) -> Product:
        product = await self._products.get(product_id)
        if product is None:
            raise NotFound("Товар", product_id)
        return product

    async def _check_rules(
        self, payload: ProductCreate, seller_id: UUID, except_id: UUID | None = None
    ):
        if await self._categories.get(payload.category_id) is None:
            raise NotFound("Категория", payload.category_id)
        if payload.stock > self._max_stock:
            raise StockLimitExceeded(self._max_stock)
        for other in await self._products.list_for_category(payload.category_id):
            if (
                other.id != except_id
                and other.seller_id == seller_id
                and other.name == payload.name
            ):
                raise DuplicateProduct(other.id)

    async def create(self, payload: ProductCreate, seller_id: UUID) -> Product:
        await self._check_rules(payload, seller_id)
        product = Product(id=uuid4(), seller_id=seller_id, **payload.model_dump())
        await self._products.add(product)
        return product

    async def replace(self, product_id: UUID, payload: ProductReplace) -> Product:
        product = await self.get(product_id)
        await self._check_rules(payload, product.seller_id, except_id=product_id)
        for field, value in payload.model_dump().items():
            setattr(product, field, value)
        await self._products.save(product)
        return product

    async def delete(self, product_id: UUID) -> None:
        product = await self.get(product_id)
        await self._products.delete(product)
