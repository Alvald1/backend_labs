from uuid import UUID

from app.models import Product
from app.schemas.category import CategoryRead
from app.schemas.review import ReviewRead

categories: dict[UUID, CategoryRead] = {}
products: dict[UUID, Product] = {}
reviews: dict[UUID, ReviewRead] = {}
