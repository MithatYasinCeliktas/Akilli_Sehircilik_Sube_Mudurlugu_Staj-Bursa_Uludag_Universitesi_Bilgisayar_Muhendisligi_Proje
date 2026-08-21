"""
Veritabanı tablolarını oluşturan ve ilk seed verilerini yükleyen setup scripti.
Alembic yerine direkt SQLAlchemy kullanır.
"""
import asyncio
import logging
import sys
import os

# Backend klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash

# Tüm modelleri import et (Base.metadata'ya kaydolsunlar)
from app.models.unit import Unit  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.report import ActivityReport, ReportItem  # noqa: F401
from app.models.report_share import ReportShare  # noqa: F401
from app.models.institution import Institution  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Tüm tabloları oluştur (varsa geç)."""
    logger.info("Veritabanı bağlantısı kuruluyor...")
    engine = create_async_engine(
        str(settings.ASYNC_SQLALCHEMY_DATABASE_URI),
        echo=True
    )
    
    async with engine.begin() as conn:
        logger.info("Tablolar oluşturuluyor...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("✅ Tablolar başarıyla oluşturuldu!")


async def create_admin_user():
    """İlk admin kullanıcısını oluştur."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy import select
    
    engine = create_async_engine(
        str(settings.ASYNC_SQLALCHEMY_DATABASE_URI),
        echo=False
    )
    
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with SessionLocal() as session:
        # Admin kullanıcı var mı?
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info(f"✅ Admin kullanıcı zaten mevcut: {settings.FIRST_SUPERUSER_EMAIL}")
        else:
            admin = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="Sistem Yöneticisi",
                role=UserRole.ADMIN,
                is_superuser=True,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info(f"✅ Admin kullanıcı oluşturuldu: {settings.FIRST_SUPERUSER_EMAIL}")
            logger.info(f"   Şifre: {settings.FIRST_SUPERUSER_PASSWORD}")
    
    await engine.dispose()


async def main():
    logger.info("=" * 60)
    logger.info("Bursa Faaliyet Raporu - Veritabanı Kurulum Scripti")
    logger.info("=" * 60)
    
    await create_tables()
    await create_admin_user()
    
    logger.info("=" * 60)
    logger.info("✅ Kurulum tamamlandı!")
    logger.info(f"   Admin E-posta: {settings.FIRST_SUPERUSER_EMAIL}")
    logger.info(f"   Admin Şifre  : {settings.FIRST_SUPERUSER_PASSWORD}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
