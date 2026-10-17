"""Четыре способа получить название категории для списка товаров."""

import asyncio
from uuid import uuid4

from sqlalchemy import event, insert, select
from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.orm import joinedload, selectinload

from app.core.database import engine, session_factory
from app.models import Category, Product, ProductCondition


async def main() -> None:
    queries: list[str] = []

    def count_queries(conn, cursor, statement, parameters, context, executemany) -> None:
        queries.append(" ".join(statement.split()))

    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            product_ids = []
            seller_id = uuid4()
            for number in range(1, 4):
                category_id = uuid4()
                product_id = uuid4()
                product_ids.append(product_id)
                await connection.execute(
                    insert(Category), {"id": category_id, "name": f"Категория N+1 {number}"}
                )
                await connection.execute(
                    insert(Product),
                    {
                        "id": product_id,
                        "seller_id": seller_id,
                        "category_id": category_id,
                        "name": f"Товар N+1 {number}",
                        "price": 100,
                        "stock": 1,
                        "condition": ProductCondition.NEW,
                    },
                )

            event.listen(engine.sync_engine, "before_cursor_execute", count_queries)
            try:
                for strategy in ("direct", "awaitable_attrs", "selectinload", "joinedload"):
                    queries.clear()
                    statement = (
                        select(Product).where(Product.id.in_(product_ids)).order_by(Product.name)
                    )
                    if strategy == "selectinload":
                        statement = statement.options(selectinload(Product.category))
                    elif strategy == "joinedload":
                        statement = statement.options(joinedload(Product.category))

                    # Новая сессия для каждого способа исключает влияние identity map.
                    async with session_factory(bind=connection) as session:
                        print(f"\n{strategy}:")
                        products = list(await session.scalars(statement))
                        try:
                            for product in products:
                                if strategy == "awaitable_attrs":
                                    category = await product.awaitable_attrs.category
                                else:
                                    category = product.category
                                print(f"  {product.name}: {category.name}")
                        except MissingGreenlet:
                            print("  MissingGreenlet: обычный атрибут не может ожидать SQL.")
                        print(f"  Вызовов before_cursor_execute: {len(queries)}")
                        for query in queries:
                            print(f"  {query}")
                        if strategy == "direct":
                            print("  Последний SELECT связи прерван до выполнения: нужен await.")
            finally:
                event.remove(engine.sync_engine, "before_cursor_execute", count_queries)
        finally:
            await transaction.rollback()
            print("\nУчебные данные удалены откатом транзакции.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
