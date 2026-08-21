from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Async Engine Tanımlaması
engine = create_async_engine(
    str(settings.ASYNC_SQLALCHEMY_DATABASE_URI),
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async Oturum (Session) Fabrikası
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
# Alias for backward compatibility
async_session = AsyncSessionLocal


class Base(DeclarativeBase):
    """
    Tüm SQLAlchemy 2.0 modelleri için temel bildirimsel (declarative) taban sınıfı.
    """
    pass


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI endpoint'lerinde kullanılacak async veritabanı oturum bağımlılığı (dependency).
    İşlem sonunda oturumu güvenli bir şekilde kapatır ve hata durumunda rollback yapar.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Backward-compatible alias for the async database dependency."""
    async for session in get_async_db():
        yield session