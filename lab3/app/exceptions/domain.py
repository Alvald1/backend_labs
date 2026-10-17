from uuid import UUID

from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, status_code: int, message: str, field: str, value: object):
        super().__init__(status_code, message)
        self.details = [{"field": field, "rule": "business_rule", "message": str(value)}]


class NotFound(AppError):
    def __init__(self, entity: str, object_id: UUID):
        super().__init__(404, f"{entity} не найден(а)", "id", object_id)


class DuplicateProduct(AppError):
    def __init__(self, product_id: UUID):
        super().__init__(
            409,
            "У продавца уже есть товар с таким названием в этой категории",
            "product_id",
            product_id,
        )


class StockLimitExceeded(AppError):
    def __init__(self, limit: int):
        super().__init__(
            409, f"Остаток товара не должен превышать {limit}", "max_product_stock", limit
        )


class CategoryNotEmpty(AppError):
    def __init__(self, category_id: UUID):
        super().__init__(
            409, "Нельзя удалить категорию, в которой есть товары", "category_id", category_id
        )
