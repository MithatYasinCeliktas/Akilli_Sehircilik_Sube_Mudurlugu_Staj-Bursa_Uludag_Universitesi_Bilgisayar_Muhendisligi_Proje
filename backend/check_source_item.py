import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.report import ReportItem

async def check():
    async with async_session_maker() as session:
        query = select(ReportItem).where(ReportItem.source_item_id.isnot(None))
        res = await session.execute(query)
        items = res.scalars().all()
        print(f"Total items with source_item_id: {len(items)}")
        for i in items:
            print(f"Item ID: {i.id}, source: {i.source_item_id}, status: {i.status}, creator: {i.creator_id}")

if __name__ == "__main__":
    asyncio.run(check())
