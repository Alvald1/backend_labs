"""Один сценарий удаления для ORM-каскада и ON DELETE CASCADE в базе."""

import argparse
import asyncio
from uuid import uuid4

from sqlalchemy import event, func, insert, select

from app.core.database import engine, session_factory
from app.models import Category, Product, ProductCondition, Review


async def main(mode: str) -> None:
    expected_passive_deletes = mode == "database"
    if Product.reviews.property.passive_deletes != expected_passive_deletes:
        raise ValueError(f"Для --mode {mode} нужен passive_deletes={expected_passive_deletes}.")

    queries: list[str] = []

    def capture_sql(conn, cursor, statement, parameters, context, executemany) -> None:
        queries.append(" ".join(statement.split()))

    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            category_id = uuid4()
            product_id = uuid4()
            await connection.execute(insert(Category), {"id": category_id, "name": "Cascade demo"})
            await connection.execute(
                insert(Product),
                {
                    "id": product_id,
                    "seller_id": uuid4(),
                    "category_id": category_id,
                    "name": "Товар с отзывами",
                    "price": 100,
                    "stock": 1,
                    "condition": ProductCondition.NEW,
                },
            )
            await connection.execute(
                insert(Review),
                [
                    {
                        "id": uuid4(),
                        "user_id": uuid4(),
                        "product_id": product_id,
                        "rating": rating,
                        "text": f"Отзыв {rating}",
                    }
                    for rating in (3, 4, 5)
                ],
            )
            review_count = (
                select(func.count()).select_from(Review).where(Review.product_id == product_id)
            )
            print(f"Режим: {mode}; отзывов до удаления: {await connection.scalar(review_count)}")

            # Связь reviews не загружаем: в режиме database дочерние строки удаляет БД.
            async with session_factory(bind=connection) as session:
                event.listen(engine.sync_engine, "before_cursor_execute", capture_sql)
                try:
                    product = await session.get(Product, product_id)
                    await session.delete(product)
                    await session.flush()
                finally:
                    event.remove(engine.sync_engine, "before_cursor_execute", capture_sql)
                print("SQL удаления:")
                for query in queries:
                    print(f"  {query}")
                product_count = (
                    select(func.count()).select_from(Product).where(Product.id == product_id)
                )
                print(f"Товаров после удаления: {await session.scalar(product_count)}")
                print(f"Отзывов после удаления: {await session.scalar(review_count)}")
        finally:
            await transaction.rollback()
            print("Учебные данные удалены откатом транзакции.")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("orm", "database"), default="database")
    asyncio.run(main(parser.parse_args().mode))
