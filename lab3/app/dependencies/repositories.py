from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.dependencies.database import get_session
from app.repositories.categories import CategoryRepository
from app.repositories.memory import (
    MemoryCategoryRepository,
    MemoryProductRepository,
    MemoryReviewRepository,
)
from app.repositories.products import ProductRepository
from app.repositories.reviews import ReviewRepository
from app.repositories.sqlalchemy import (
    SqlAlchemyCategoryRepository,
    SqlAlchemyProductRepository,
    SqlAlchemyReviewRepository,
)

categories = MemoryCategoryRepository()
reviews = MemoryReviewRepository()
products = MemoryProductRepository(reviews)

Session = Annotated[AsyncSession | None, Depends(get_session)]
Config = Annotated[Settings, Depends(get_settings)]


def get_category_repository(session: Session, settings: Config) -> CategoryRepository:
    if settings.storage_backend == "memory":
        return categories
    return SqlAlchemyCategoryRepository(session)


def get_product_repository(session: Session, settings: Config) -> ProductRepository:
    if settings.storage_backend == "memory":
        return products
    return SqlAlchemyProductRepository(session)


def get_review_repository(session: Session, settings: Config) -> ReviewRepository:
    if settings.storage_backend == "memory":
        return reviews
    return SqlAlchemyReviewRepository(session)
