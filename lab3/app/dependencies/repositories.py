from app.repositories.memory import (
    MemoryCategoryRepository,
    MemoryProductRepository,
    MemoryReviewRepository,
)

categories = MemoryCategoryRepository()
reviews = MemoryReviewRepository()
products = MemoryProductRepository(reviews)


def get_category_repository():
    return categories


def get_product_repository():
    return products


def get_review_repository():
    return reviews
