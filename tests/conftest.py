import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.db.session import open_session
from src.db.redis_cache import get_redis
from src.db.base import Base
from src.services.auth import create_access_token, Hash
from src.models.user import User, Role

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "Test User",
    "email": "testuser@example.com",
    "password": "12345678",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar="",
                role=Role.ADMIN,
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Dependency override

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    app.dependency_overrides[open_session] = override_get_db

    class FakeRedis:
        async def get(self, key):
            return None

        async def set(self, key, value, ex=None):
            return True

        async def delete(self, key):
            return 1

    async def override_get_redis():
        return FakeRedis()

    app.dependency_overrides[get_redis] = override_get_redis

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token():
    token = create_access_token(data={"sub": test_user["email"]})
    return token

