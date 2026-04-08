from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import *  # noqa: F401,F403

# Replace only the database name (last path segment)
_base = settings.DATABASE_URL.rsplit("/", 1)[0]
TEST_DATABASE_URL = f"{_base}/evaluator_test"


@pytest.fixture(scope="session", autouse=True)
def _create_test_database():
    """Synchronously create the test database before the session starts."""
    import asyncio

    async def _setup():
        admin_engine = create_async_engine(
            f"{_base}/evaluator", isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS evaluator_test"))
            await conn.execute(text("CREATE DATABASE evaluator_test"))
        await admin_engine.dispose()

        engine = create_async_engine(TEST_DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    async def _teardown():
        admin_engine = create_async_engine(
            f"{_base}/evaluator", isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS evaluator_test"))
        await admin_engine.dispose()

    asyncio.run(_setup())
    yield
    asyncio.run(_teardown())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Per-test session using a nested transaction for rollback isolation."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    conn = await engine.connect()
    txn = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)

    yield session

    await session.close()
    await txn.rollback()
    await conn.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
