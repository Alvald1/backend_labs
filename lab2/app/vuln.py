"""Отдельный учебный пример массового присвоения из задачи 4."""

from fastapi import APIRouter, FastAPI, Response

from app.models import Product
from app.schemas.product import ProductRead

app = FastAPI(
    title="Пример mass assignment",
    version="0.2.0",
    description="Намеренно уязвимый обработчик для задачи 4. "
    "Принимает владельца из тела и только возвращает созданную модель.",
    openapi_tags=[{"name": "vuln", "description": "Учебная демонстрация уязвимости"}],
)
router = APIRouter(prefix="/api/v1/products", tags=["vuln"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=201,
    summary="Уязвимое создание товара",
    description="Распаковывает произвольный словарь во внутреннюю модель, включая "
    "seller_id. Используется только для сравнения с основным приложением.",
)
async def create_product_vuln(payload: dict, response: Response) -> ProductRead:
    product = Product(**payload)
    response.headers["Location"] = f"/api/v1/products/{product.id}"
    return ProductRead(**product.model_dump())


app.include_router(router)
