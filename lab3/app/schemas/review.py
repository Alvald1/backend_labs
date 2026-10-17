from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    rating: int = Field(ge=1, le=5, examples=[5])
    text: str | None = Field(default=None, max_length=1000)


class ReviewReplace(ReviewCreate):
    pass


class ReviewPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Значение по умолчанию разрешает пропуск поля, но не явный null в запросе.
    product_id: UUID = Field(default=None)
    rating: int = Field(default=None, ge=1, le=5, examples=[4])
    text: str | None = Field(default=None, max_length=1000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    product_id: UUID
    rating: int
    text: str | None
