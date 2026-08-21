import asyncio
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def delete_test_users():
    async with AsyncSessionLocal() as session:
        # Delete all users except ADMIN
        stmt = delete(User).where(User.role != 'ADMIN')
        await session.execute(stmt)
        await session.commit()
        print("Test users deleted successfully.")

if __name__ == "__main__":
    asyncio.run(delete_test_users())
