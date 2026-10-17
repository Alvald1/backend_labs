from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.dependencies.repositories import (
    get_category_repository,
    get_product_repository,
    get_review_repository,
)
from app.repositories.categories import CategoryRepository
from app.repositories.products import ProductRepository
from app.repositories.reviews import ReviewRepository
from app.use_cases.categories import CategoryService
from app.use_cases.products import ProductService
from app.use_cases.reviews import ReviewService


def get_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


def get_category_service(
    categories: Annotated[CategoryRepository, Depends(get_category_repository)],
    products: Annotated[ProductRepository, Depends(get_product_repository)],
) -> CategoryService:
    return CategoryService(categories, products)


def get_product_service(
    products: Annotated[ProductRepository, Depends(get_product_repository)],
    categories: Annotated[CategoryRepository, Depends(get_category_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ProductService:
    return ProductService(products, categories, settings.max_product_stock)


def get_review_service(
    reviews: Annotated[ReviewRepository, Depends(get_review_repository)],
    products: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ReviewService:
    return ReviewService(reviews, products)
