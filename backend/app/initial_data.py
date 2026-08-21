import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(db: AsyncSession) -> None:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        superuser = User(
            email=settings.FIRST_SUPERUSER_EMAIL,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name="Sistem Yöneticisi",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
        )
        db.add(superuser)
        await db.commit()
        logger.info("İlk süper kullanıcı (admin) başarıyla oluşturuldu.")
    else:
        logger.info("Süper kullanıcı zaten mevcut.")


async def main() -> None:
    logger.info("Veritabanı başlangıç verileri yükleniyor...")
    async with AsyncSessionLocal() as session:
        await init_db(session)
    logger.info("Veritabanı başlangıç verileri başarıyla yüklendi.")


if __name__ == "__main__":
    asyncio.run(main())