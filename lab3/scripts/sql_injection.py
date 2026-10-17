"""Сравнение SQL-инъекции и специальных символов ILIKE."""

import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine, session_factory
from app.models import Category, Product, ProductCondition


async def search_unsafe(session: AsyncSession, seller_id: UUID, name: str) -> list[str]:
    # Намеренно небезопасная подстановка только для учебной демонстрации.
    query = text(
        f"SELECT name FROM products WHERE seller_id = :seller_id AND (name = '{name}') "  # noqa: S608
        "ORDER BY name"
    )
    return list(await session.scalars(query, {"seller_id": seller_id}))


async def search_bound(session: AsyncSession, seller_id: UUID, name: str) -> list[str]:
    query = text(
        "SELECT name FROM products WHERE seller_id = :seller_id AND (name = :name) ORDER BY name"
    )
    return list(await session.scalars(query, {"seller_id": seller_id, "name": name}))


async def search_orm(session: AsyncSession, seller_id: UUID, name: str) -> list[str]:
    query = (
        select(Product.name)
        .where(Product.seller_id == seller_id, Product.name == name)
        .order_by(Product.name)
    )
    return list(await session.scalars(query))


async def main() -> None:
    async with session_factory() as session:
        try:
            category_id = uuid4()
            seller_id = uuid4()
            session.add(Category(id=category_id, name="SQL injection demo"))
            await session.flush()
            for name in ("Телефон", "Наушники", "Скидка 10%", "Кабель_USB"):
                session.add(
                    Product(
                        id=uuid4(),
                        seller_id=seller_id,
                        category_id=category_id,
                        name=name,
                        price=100,
                        stock=1,
                        condition=ProductCondition.NEW,
                    )
                )
            await session.flush()

            for name in ("Телефон", "' OR '1'='1"):
                print(f"\nПоиск по имени {name!r}:")
                for search in (search_unsafe, search_bound, search_orm):
                    print(f"  {search.__name__}: {await search(session, seller_id, name)}")

            for fragment in ("Тел", "' OR '1'='1", "%", "_"):
                pattern = f"%{fragment}%"
                escaped = fragment.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                escaped_pattern = f"%{escaped}%"
                before = (
                    select(Product.name)
                    .where(Product.seller_id == seller_id, Product.name.ilike(pattern))
                    .order_by(Product.name)
                )
                after = (
                    select(Product.name)
                    .where(
                        Product.seller_id == seller_id,
                        Product.name.ilike(escaped_pattern, escape="\\"),
                    )
                    .order_by(Product.name)
                )
                print(f"\nILIKE, фрагмент {fragment!r}:")
                print("  SQL до:", " ".join(str(before.compile(dialect=engine.dialect)).split()))
                print(f"  Шаблон {pattern!r}: {list(await session.scalars(before))}")
                print("  SQL после:", " ".join(str(after.compile(dialect=engine.dialect)).split()))
                print(f"  Шаблон {escaped_pattern!r}: {list(await session.scalars(after))}")
        finally:
            await session.rollback()
            print("\nУчебные данные удалены откатом транзакции.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
