from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import ActivityReport, ReportItem, ReportStatus, ItemCategory
from app.models.user import User
from app.schemas.report import ActivityReportCreate, ActivityReportUpdate, ReportFilter
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[ActivityReport, ActivityReportCreate, ActivityReportUpdate]):
    """
    Faaliyet Raporu ve Faaliyet Satırlarına ait veritabanı sorgularını
    ve gelişmiş arama/filtreleme fonksiyonlarını yöneten repository sınıfı.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(model=ActivityReport, db=db)

    async def get_with_items(self, report_id: int) -> Optional[ActivityReport]:
        """
        ID değerine göre faaliyet raporunu ilişkili tüm faaliyet satırları (items) 
        ve kullanıcı detaylarıyla birlikte getirir.
        """
        query = (
            select(ActivityReport)
            .where(ActivityReport.id == report_id)
            .options(
                selectinload(ActivityReport.user).selectinload(User.unit),
                selectinload(ActivityReport.items)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_and_period(
        self,
        user_id: int,
        year: int,
        month: int
    ) -> Optional[ActivityReport]:
        """
        Belirli bir kullanıcının ilgili yıl ve aya ait faaliyet raporunu getirir.
        """
        query = (
            select(ActivityReport)
            .where(
                and_(
                    ActivityReport.user_id == user_id,
                    ActivityReport.year == year,
                    ActivityReport.month == month
                )
            )
            .options(
                selectinload(ActivityReport.items)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_filtered_reports(
        self,
        filters: ReportFilter,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ActivityReport], int]:
        """
        Metin içi arama (ILIKE), tarih/kategori/birim/kullanıcı filtrelerine göre 
        faaliyet raporlarını sayfalı olarak sorgular ve [liste, toplam_sayı] döndürür.
        """
        query = (
            select(ActivityReport)
            .join(ActivityReport.user)
            .options(
                selectinload(ActivityReport.user).selectinload(User.unit),
                selectinload(ActivityReport.items)
            )
        )
        
        count_query = (
            select(func.count(func.distinct(ActivityReport.id)))
            .select_from(ActivityReport)
            .join(ActivityReport.user)
        )

        conditions = []

        # Yıl ve Ay Filtreleri
        if filters.year is not None:
            conditions.append(ActivityReport.year == filters.year)

        if filters.month is not None:
            conditions.append(ActivityReport.month == filters.month)

        # Durum (DRAFT / SAVED)
        if filters.status is not None:
            conditions.append(ActivityReport.status == filters.status)

        # Kullanıcı Bazlı Filtre
        if filters.user_ids:
            conditions.append(ActivityReport.user_id.in_(filters.user_ids))

        # Yetkili olunan kullanıcılar filtresi
        if getattr(filters, "allowed_user_ids", None) is not None:
            conditions.append(ActivityReport.user_id.in_(filters.allowed_user_ids))

        # Birim Bazlı Filtre (Tüm alt hiyerarşi ile birlikte)
        if filters.unit_id is not None:
            from app.models.unit import Unit
            from sqlalchemy.orm import aliased
            
            unit_cte = select(Unit.id).where(Unit.id == filters.unit_id).cte(name="unit_cte", recursive=True)
            unit_alias = aliased(Unit)
            unit_cte = unit_cte.union_all(
                select(unit_alias.id).where(unit_alias.parent_id == unit_cte.c.id)
            )
            conditions.append(User.unit_id.in_(select(unit_cte.c.id)))

        # Kategori Bazlı Filtre
        if filters.category is not None:
            query = query.join(ActivityReport.items)
            count_query = count_query.join(ActivityReport.items)
            conditions.append(ReportItem.category == filters.category)

        # Tarih Aralığı Filtresi (created_at bazlı)
        if filters.start_date:
            try:
                start_dt = datetime.strptime(f"{filters.start_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                conditions.append(ActivityReport.created_at >= start_dt)
            except ValueError:
                pass
        if filters.end_date:
            try:
                end_dt = datetime.strptime(f"{filters.end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
                conditions.append(ActivityReport.created_at <= end_dt)
            except ValueError:
                pass

        # Metin İçi Arama (Rapor Başlığı veya Satır İçeriğinde ILIKE Arama)
        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            # Eğer henüz ReportItem join edilmediyse ekleyelim
            if filters.category is None:
                query = query.outerjoin(ActivityReport.items)
                count_query = count_query.outerjoin(ActivityReport.items)
            
            conditions.append(
                or_(
                    ActivityReport.title.ilike(search_pattern),
                    ReportItem.content.ilike(search_pattern),
                    ReportItem.related_institutions.ilike(search_pattern),
                    ReportItem.solution_proposals.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )

        # Seçili Raporlar Filtresi
        if filters.report_ids:
            conditions.append(ActivityReport.id.in_(filters.report_ids))

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # Gruplama & Sayı Hesaplama
        query = query.group_by(ActivityReport.id)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sıralama ve Sayfalama
        query = query.order_by(
            ActivityReport.year.desc(),
            ActivityReport.month.desc(),
            ActivityReport.id.desc()
        ).offset(skip).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().unique().all())

        return items, total

    async def replace_report_items(
        self,
        report_id: int,
        new_items_data: List[dict]
    ) -> List[ReportItem]:
        """
        Belirtilen raporun mevcut detay satırlarını temizleyip güncel satırları ekler.
        """
        # Eski satırları sil
        delete_query = (
            select(ReportItem)
            .where(ReportItem.report_id == report_id)
        )
        old_items_result = await self.db.execute(delete_query)
        for item in old_items_result.scalars().all():
            await self.db.delete(item)

        await self.db.flush()

        # Yeni satırları oluştur
        created_items = []
        for idx, item_data in enumerate(new_items_data):
            new_item = ReportItem(
                report_id=report_id,
                category=item_data["category"],
                content=item_data["content"],
                related_institutions=item_data.get("related_institutions"),
                solution_proposals=item_data.get("solution_proposals"),
                display_order=item_data.get("display_order", idx)
            )
            self.db.add(new_item)
            created_items.append(new_item)

        await self.db.flush()
        return created_items