import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.core.security import get_password_hash

engine = create_async_engine(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def fix_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id FROM users WHERE email='admin@bursa.bel.tr'"))
        u1 = result.scalar()
        hashed = get_password_hash('admin123!')
        if u1:
            await session.execute(text("UPDATE users SET hashed_password=:h WHERE id=:id"), {'h': hashed, 'id': u1})
        else:
            await session.execute(text("INSERT INTO users (email, hashed_password, is_active, is_superuser, first_name, last_name, role) VALUES ('admin@bursa.bel.tr', :h, true, true, 'Admin', 'Bursa', 'ADMIN')"), {'h': hashed})
            
        result2 = await session.execute(text("SELECT id FROM users WHERE email='admin@belediye.gov.tr'"))
        u2 = result2.scalar()
        if u2:
            await session.execute(text("UPDATE users SET hashed_password=:h WHERE id=:id"), {'h': hashed, 'id': u2})
        else:
            await session.execute(text("INSERT INTO users (email, hashed_password, is_active, is_superuser, first_name, last_name, role) VALUES ('admin@belediye.gov.tr', :h, true, true, 'Admin', 'Belediye', 'ADMIN')"), {'h': hashed})
            
        await session.commit()
        print('Users fixed!')

asyncio.run(fix_users())