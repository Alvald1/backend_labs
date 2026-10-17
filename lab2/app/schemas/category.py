from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80, examples=["Книги"])
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не должно быть пустым")
        return value


class CategoryReplace(CategoryCreate):
    pass


class CategoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # None используется только для пропущенного поля; явный null не проходит проверку str.
    name: str = Field(default=None, min_length=1, max_length=80, examples=["Учебники"])
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Название не должно быть пустым")
        return value.strip()


class CategoryRead(BaseModel):
    id: UUID
    name: str
    description: str | None
