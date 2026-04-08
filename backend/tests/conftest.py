import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import *  # noqa: F401,F403

TEST_DATABASE_URL = settings.DATABASE_URL.replace("/evaluator", "/evaluator_test")

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_test = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Create a connection to the default database to create the test database
    from sqlalchemy.ext.asyncio import create_async_engine as cae
    default_engine = cae(
        settings.DATABASE_URL.rsplit("/", 1)[0] + "/evaluator",
        isolation_level="AUTOCOMMIT",
    )
    async with default_engine.connect() as conn:
        # Drop test DB if exists, then create
        await conn.execute(
            __import__("sqlalchemy").text("DROP DATABASE IF EXISTS evaluator_test")
        )
        await conn.execute(__import__("sqlalchemy").text("CREATE DATABASE evaluator_test"))
    await default_engine.dispose()

    # Create tables
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()

    cleanup_engine = cae(
        settings.DATABASE_URL.rsplit("/", 1)[0] + "/evaluator",
        isolation_level="AUTOCOMMIT",
    )
    async with cleanup_engine.connect() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("DROP DATABASE IF EXISTS evaluator_test")
        )
    await cleanup_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_test() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
