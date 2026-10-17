import argparse
import asyncio

from app import models  # noqa: F401 — регистрирует таблицы в Base.metadata
from app.core.database import Base, engine


async def main(recreate: bool):
    try:
        async with engine.begin() as connection:
            if recreate:
                await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        print("Таблицы пересозданы" if recreate else "Таблицы созданы, существующие сохранены")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Создание схемы учебной базы")
    parser.add_argument(
        "--recreate", action="store_true", help="Удалить данные и пересоздать таблицы"
    )
    args = parser.parse_args()
    asyncio.run(main(args.recreate))
