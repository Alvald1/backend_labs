from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.product import ProductCondition


class ProductSort(StrEnum):
    NAME = "name"
    PRICE = "price"
    STOCK = "stock"


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: UUID
    name: str = Field(min_length=1, max_length=100, examples=["Учебник Python"])
    price: float = Field(gt=0, allow_inf_nan=False, examples=[1000])
    discount_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    stock: int = Field(ge=0, examples=[10])
    condition: ProductCondition = ProductCondition.NEW

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не должно быть пустым")
        return value

    @model_validator(mode="after")
    def check_discount(self) -> Self:
        if self.discount_price is not None and self.discount_price > self.price:
            raise ValueError("Цена со скидкой не должна превышать обычную цену")
        return self


class ProductReplace(ProductCreate):
    pass


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    category_id: UUID
    name: str
    price: float
    discount_price: float | None
    stock: int
    condition: ProductCondition
