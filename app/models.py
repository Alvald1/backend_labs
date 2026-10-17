from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.schemas.product import ProductCondition

DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


class Product(BaseModel):
    name: str
    category_id: UUID
    price: float
    stock: int
    discount_price: float | None = None
    condition: ProductCondition = ProductCondition.NEW
    id: UUID = Field(default_factory=uuid4)
    seller_id: UUID = DEMO_USER_ID
