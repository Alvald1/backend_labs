from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_backend: Literal["memory", "database"] = "database"
    database_url: str = "postgresql+asyncpg://catalog:catalog@127.0.0.1:5433/catalog"
    sql_echo: bool = False
    max_product_stock: int = Field(default=1000, ge=1, le=1000000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
