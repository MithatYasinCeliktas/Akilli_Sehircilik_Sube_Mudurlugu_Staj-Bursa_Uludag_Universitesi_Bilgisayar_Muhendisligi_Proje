from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from app.repositories.report_repository import ReportRepository
from app.models.report_share import ReportShare
from app.models.notification import Notification
from app.schemas.common import PaginatedData
from app.schemas.report import (
    ActivityReportCreate,
    ActivityReportUpdate,
    ActivityReportResponse,
    ReportItemCreate,
    ReportItemUpdate,
    ReportItemReview,
    ReportItemResponse,
    ReportFilter,
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService
from app.models.report import ActivityReport, ReportItem, ReportStatus, ItemCategory
from app.models.user import User
from app.services.log_service import LogService


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.report_repo = ReportRepository(db)

    async def get_subordinate_ids_recursive(self, manager_id: int) -> List[int]:
        allowed_ids = {manager_id}
        current_check_ids = [manager_id]

        while current_check_ids:
            query = select(User.id).where(User.manager_id.in_(current_check_ids))
            result = await self.db.execute(query)
            new_ids = [row[0] for row in result.all()]
            
            new_unseen_ids = [nid for nid in new_ids if nid not in allowed_ids]
            if not new_unseen_ids:
                break
                
            allowed_ids.update(new_unseen_ids)
            current_check_ids = new_unseen_ids

        return list(allowed_ids)

    
    async def _attach_items_to_report(self, report: ActivityReport) -> ActivityReportResponse:
        from app.schemas.report import ReportItemResponse
        all_item_ids = set((report.yapilan_is_ids or []) + (report.yapilacak_is_ids or []) + (report.koordinasyon_is_ids or []))
        items = []
        if all_item_ids:
            items_result = await self.db.execute(select(ReportItem).where(ReportItem.id.in_(all_item_ids)))
            items = items_result.scalars().all()
        
        items_by_id = {i.id: i for i in items}
        
        yapilan = [items_by_id[i] for i in (report.yapilan_is_ids or []) if i in items_by_id]
        yapilacak = [items_by_id[i] for i in (report.yapilacak_is_ids or []) if i in items_by_id]
        koordinasyon = [items_by_id[i] for i in (report.koordinasyon_is_ids or []) if i in items_by_id]
        
        response = ActivityReportResponse.model_validate(report)
        response.yapilan_isler = [ReportItemResponse.model_validate(i) for i in yapilan]
        response.yapilacak_isler = [ReportItemResponse.model_validate(i) for i in yapilacak]
        response.koordinasyon_isleri = [ReportItemResponse.model_validate(i) for i in koordinasyon]
        return response

    async def get_report_by_id(self, report_id: int, current_user: Optional[User] = None) -> ActivityReportResponse:
        report = await self.report_repo.get_with_items(report_id)
        if not report:
            raise NotFoundException(detail=f"{report_id} ID'li faaliyet raporu bulunamadı.")
            
        if current_user and not (current_user.is_superuser or getattr(current_user.role, 'value', current_user.role) == "ADMIN"):
            # Normal user can see if they are the creator, their manager is the creator, or their subordinate is the creator
            is_allowed = (report.user_id == current_user.id) or (report.user_id == current_user.manager_id)
            if not is_allowed:
                subs = await self.get_subordinate_ids_recursive(current_user.id)
                if report.user_id in subs:
                    is_allowed = True

            if not is_allowed:
                from app.models.report_share import ReportShare, ShareStatus
                from sqlalchemy import select, or_
                share_query = select(ReportShare).where(
                    ReportShare.report_id == report_id,
                    ReportShare.status == ShareStatus.APPROVED,
                    or_(
                        ReportShare.target_user_id == current_user.id,
                        ReportShare.target_unit_id == current_user.unit_id
                    )
                )
                share_res = await self.db.execute(share_query)
                if share_res.scalars().first():
                    is_allowed = True
            
            if not is_allowed:
                raise ForbiddenException(detail="Bu faaliyet raporunu görüntüleme yetkiniz bulunmamaktadır.")
                
        return await self._attach_items_to_report(report)

    async def get_reports_paginated(
        self,
        filters: ReportFilter,
        page: int = 1,
        page_size: int = 10,
        current_user: Optional[User] = None
    ) -> PaginatedData[ActivityReportResponse]:
        if current_user and not (current_user.is_superuser or getattr(current_user.role, 'value', current_user.role) == "ADMIN"):
            # Users can see reports created by themselves, their managers, and their subordinates
            allowed_creators = [current_user.id]
            if current_user.manager_id:
                allowed_creators.append(current_user.manager_id)
            
            subs = await self.get_subordinate_ids_recursive(current_user.id)
            allowed_creators.extend(subs)
            
            filters.allowed_user_ids = allowed_creators

        skip = (page - 1) * page_size
        reports, total = await self.report_repo.get_filtered_reports(
            filters=filters,
            skip=skip,
            limit=page_size
        )

        items = [await self._attach_items_to_report(r) for r in reports]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginatedData[ActivityReportResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def create_report(self, user_id: int, report_in: ActivityReportCreate) -> ActivityReportResponse:
        # Check if user has subordinates (is manager)
        query = select(User).options(selectinload(User.unit)).where(User.id == user_id)
        res = await self.db.execute(query)
        creator_user = res.scalars().first()
        
        if not creator_user or not await self._has_subordinates(user_id):
            raise ForbiddenException("Yalnızca yöneticiler (altında çalışan bulunanlar) rapor dosyası açabilir.")

        report_data = report_in.model_dump()
        report_data["user_id"] = user_id
        
        unit_name = creator_user.unit.name if creator_user.unit else "Birim"
        report_data["title"] = f"{unit_name}-{report_data['year']}_{report_data['month']:02d}"

        created_report = await self.report_repo.create(report_data)
        
        await LogService.create_log(
            db=self.db,
            action="CREATE_REPORT",
            user_id=user_id,
            entity_type="REPORT",
            entity_id=created_report.id,
            details={"title": report_data["title"], "year": report_data["year"], "month": report_data["month"]}
        )
        
        await self.db.commit()

        full_report = await self.report_repo.get_with_items(created_report.id)
        return ActivityReportResponse.model_validate(full_report)
        
    async def _has_subordinates(self, user_id: int) -> bool:
        query = select(User.id).where(User.manager_id == user_id).limit(1)
        res = await self.db.execute(query)
        return res.scalars().first() is not None

    async def update_report(self, report_id: int, user_id: int, report_in: ActivityReportUpdate, is_admin: bool = False) -> ActivityReportResponse:
        report = await self.report_repo.get(report_id)
        if not report:
            raise NotFoundException(detail=f"{report_id} ID'li faaliyet raporu bulunamadı.")

        if not is_admin and report.user_id != user_id:
            raise ForbiddenException(detail="Bu rapor dosyasını güncelleme yetkiniz bulunmamaktadır.")

        update_data = report_in.model_dump(exclude_unset=True)
        if update_data:
            await self.report_repo.update(report, update_data)
            await LogService.create_log(
                db=self.db,
                action="UPDATE_REPORT",
                user_id=user_id,
                entity_type="REPORT",
                entity_id=report_id,
                details=update_data
            )
        await self.db.commit()

        full_report = await self.report_repo.get_with_items(report_id)
        return ActivityReportResponse.model_validate(full_report)

    async def delete_report(self, report_id: int, user_id: int, is_admin: bool = False) -> bool:
        report = await self.report_repo.get(report_id)
        if not report:
            raise NotFoundException(detail=f"{report_id} ID'li faaliyet raporu bulunamadı.")
        if not is_admin and report.user_id != user_id:
            raise ForbiddenException(detail="Bu raporu silme yetkiniz bulunmamaktadır.")
        await self.report_repo.remove(report_id)
        await LogService.create_log(
            db=self.db,
            action="DELETE_REPORT",
            user_id=user_id,
            entity_type="REPORT",
            entity_id=report_id,
            details={"title": report.title}
        )
        await self.db.commit()
        return True

    # ITEM LEVEL OPERATIONS
    async def create_report_item(self, report_id: int, current_user: User, item_in: ReportItemCreate) -> ActivityReportResponse:
        report = await self.report_repo.get(report_id)
        if not report:
            raise NotFoundException("Rapor bulunamadı.")
        if report.user_id != current_user.manager_id and report.user_id != current_user.id:
             raise ForbiddenException("Sadece yöneticinizin veya kendinizin açtığı rapora satır girebilirsiniz.")
        
        # Eğer raporu açan kişi (yönetici) kendisiyse ve satır girmeye çalışıyorsa engelle!
        if report.user_id == current_user.id:
            raise ForbiddenException("Kendi açtığınız rapora satır giremezsiniz. Yalnızca üst yöneticinizin açtığı rapora veri girebilirsiniz.")

        if report.status == ReportStatus.APPROVED:
             raise BadRequestException("Bu rapor tamamen onaylandığı için yeni satır eklenemez.")

        new_item = ReportItem(
            report_id=report_id,
            creator_id=current_user.id,
            status=ReportStatus.PENDING,
            **item_in.model_dump()
        )
        self.db.add(new_item)
        await self.db.flush()
        
        if item_in.category == ItemCategory.YAPILAN_ISLER:
            report.yapilan_is_ids = (report.yapilan_is_ids or []) + [new_item.id]
        elif item_in.category == ItemCategory.YAPILACAK_ISLER:
            report.yapilacak_is_ids = (report.yapilacak_is_ids or []) + [new_item.id]
        elif item_in.category == ItemCategory.KORDINASYON_GEREKTIREN_ISLER:
            report.koordinasyon_is_ids = (report.koordinasyon_is_ids or []) + [new_item.id]
            
        self.db.add(report)
        
        await LogService.create_log(
            db=self.db,
            action="CREATE_REPORT_ITEM",
            user_id=current_user.id,
            entity_type="REPORT_ITEM",
            entity_id=None,
            details={"report_id": report_id, "activity": item_in.content[:100] if item_in.content else None}
        )
        
        await self.db.commit()
        return await self.get_report_by_id(report_id, current_user)

    async def update_report_item(self, report_id: int, item_id: int, current_user: User, item_in: ReportItemUpdate) -> ActivityReportResponse:
        query = select(ReportItem).where(ReportItem.id == item_id, ReportItem.report_id == report_id)
        res = await self.db.execute(query)
        item = res.scalars().first()
        if not item:
            raise NotFoundException("Satır bulunamadı.")

        if item.creator_id != current_user.id:
            raise ForbiddenException("Sadece kendi eklediğiniz satırları güncelleyebilirsiniz.")
        
        if item.status == ReportStatus.APPROVED:
            raise BadRequestException("Onaylanmış satırlar güncellenemez.")

        for k, v in item_in.model_dump(exclude_unset=True).items():
            if k != 'id':
                setattr(item, k, v)
        
        # Güncellenen satır yeniden onaya düşer
        item.status = ReportStatus.PENDING
        item.rejection_note = None

        await LogService.create_log(
            db=self.db,
            action="UPDATE_REPORT_ITEM",
            user_id=current_user.id,
            entity_type="REPORT_ITEM",
            entity_id=item_id,
            details=item_in.model_dump(exclude_unset=True)
        )

        await self.db.commit()
        return await self.get_report_by_id(report_id, current_user)

    async def delete_report_item(self, report_id: int, item_id: int, current_user: User) -> ActivityReportResponse:
        report = await self.report_repo.get(report_id)
        if not report:
            raise NotFoundException("Rapor bulunamadı.")
            
        is_merged_item = False
        yapilan = report.yapilan_is_ids or []
        yapilacak = report.yapilacak_is_ids or []
        koordinasyon = report.koordinasyon_is_ids or []
        
        if item_id in yapilan:
            is_merged_item = True
            if report.user_id != current_user.id and not current_user.is_superuser:
                raise ForbiddenException("Sadece kendi raporunuzdan satır çıkarabilirsiniz.")
            yapilan.remove(item_id)
            report.yapilan_is_ids = list(yapilan)
        elif item_id in yapilacak:
            is_merged_item = True
            if report.user_id != current_user.id and not current_user.is_superuser:
                raise ForbiddenException("Sadece kendi raporunuzdan satır çıkarabilirsiniz.")
            yapilacak.remove(item_id)
            report.yapilacak_is_ids = list(yapilacak)
        elif item_id in koordinasyon:
            is_merged_item = True
            if report.user_id != current_user.id and not current_user.is_superuser:
                raise ForbiddenException("Sadece kendi raporunuzdan satır çıkarabilirsiniz.")
            koordinasyon.remove(item_id)
            report.koordinasyon_is_ids = list(koordinasyon)

        if not is_merged_item:
            raise NotFoundException("Satır bu raporda bulunamadı.")

        # Gerçek kaydı kontrol et
        query = select(ReportItem).where(ReportItem.id == item_id)
        res = await self.db.execute(query)
        item = res.scalars().first()
        
        if item and item.report_id == report_id:
            # Satır bu rapora aitse tamamen sil
            if item.creator_id != current_user.id and not current_user.is_superuser:
                raise ForbiddenException("Sadece kendi eklediğiniz satırları silebilirsiniz.")
            await self.db.delete(item)
            
            await LogService.create_log(
                db=self.db,
                action="DELETE_REPORT_ITEM",
                user_id=current_user.id,
                entity_type="REPORT_ITEM",
                entity_id=item_id,
                details={"report_id": report_id, "activity": item.content[:100] if item.content else None}
            )
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(report, "yapilan_is_ids")
        flag_modified(report, "yapilacak_is_ids")
        flag_modified(report, "koordinasyon_is_ids")
        
        await self.db.commit()
        return await self.get_report_by_id(report_id, current_user)

    async def review_report_item(self, report_id: int, item_id: int, current_user: User, review_in: ReportItemReview) -> ActivityReportResponse:
        report = await self.report_repo.get(report_id)
        if not report:
            raise NotFoundException("Rapor bulunamadı.")
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise ForbiddenException("Sadece kendi oluşturduğunuz rapordaki satırları onaylayabilir/reddedebilirsiniz.")
            
        query = select(ReportItem).where(ReportItem.id == item_id, ReportItem.report_id == report_id)
        res = await self.db.execute(query)
        item = res.scalars().first()
        if not item:
            raise NotFoundException("Satır bulunamadı.")

        item.status = review_in.status
        item.rejection_note = review_in.rejection_note if review_in.status == ReportStatus.REJECTED else None

        if review_in.status == ReportStatus.REJECTED and item.creator_id:
            # Bildirim gönder
            notif_service = NotificationService(self.db)
            await notif_service.create_notification(NotificationCreate(
                user_id=item.creator_id,
                message=f"'{report.title or report.id}' raporundaki bir faaliyet satırınız reddedildi. Neden: {review_in.rejection_note}",
                type="REJECTED_ITEM",
                reference_id=item.id
            ))
            
        await LogService.create_log(
            db=self.db,
            action="REVIEW_REPORT_ITEM",
            user_id=current_user.id,
            entity_type="REPORT_ITEM",
            entity_id=item_id,
            details={"status": review_in.status, "rejection_note": review_in.rejection_note}
        )

        await self.db.commit()
        return await self.get_report_by_id(report_id, current_user)

    async def approve_full_report(self, report_id: int, current_user: User, force: bool = False) -> Tuple[bool, ActivityReportResponse, List[str]]:
        report = await self.report_repo.get_with_items(report_id)
        if not report:
            raise NotFoundException("Rapor bulunamadı.")
        if report.user_id != current_user.id and not current_user.is_superuser:
            raise ForbiddenException("Sadece kendi oluşturduğunuz raporu onaylayabilirsiniz.")

        if report.status == ReportStatus.APPROVED:
            return True, ActivityReportResponse.model_validate(report), []
        # If not forced, ensure all items are approved before approving the report
        if not force:
            for item in report.items:
                if item.status != ReportStatus.APPROVED:
                    raise BadRequestException(f"Tüm satırlar onaylanmadan raporu onaylayamazsınız.")
        # When force=True, we skip the above check and approve the report regardless of item statuses

        # Eksik ast kontrolü
        query_subs = select(User).where(User.manager_id == current_user.id, User.is_active == True)
        res_subs = await self.db.execute(query_subs)
        subordinates = res_subs.scalars().all()
        
        creators = {item.creator_id for item in report.items}
        missing_names = []
        for sub in subordinates:
            if sub.id not in creators:
                missing_names.append(sub.full_name)

        # Even if some subordinate users have not submitted items, we still approve the report.
        # missing_names is retained for informational purposes.

        report.status = ReportStatus.APPROVED
        
        await LogService.create_log(
            db=self.db,
            action="APPROVE_REPORT",
            user_id=current_user.id,
            entity_type="REPORT",
            entity_id=report_id,
            details={"status": "APPROVED"}
        )
        
        await self.db.commit()
        # Retrieve the report with all relationships eagerly loaded to avoid lazy‑loading errors
        report_data = await self.get_report_by_id(report_id, current_user)
        return True, report_data, missing_names

    

    
    async def merge_items(self, item_ids: list[int], current_user_id: int, title: str | None = None) -> ActivityReportResponse:
        result = await self.db.execute(
            select(ReportItem).options(selectinload(ReportItem.report)).where(ReportItem.id.in_(item_ids))
        )
        items = result.scalars().all()
        
        if not items:
            raise NotFoundException("Seçilen satırlar bulunamadı.")
            
        first_item = items[0]
        report_year = first_item.report.year if first_item.report else 2026
        report_month = first_item.report.month if first_item.report else 1
        
        unit_id = None
        if first_item.report:
            from app.models.user import User
            user_res = await self.db.execute(
                select(User).where(User.id == first_item.report.user_id)
            )
            report_user = user_res.scalars().first()
            if report_user:
                unit_id = report_user.unit_id


        if not title:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            unit_name = "Birim"
            if unit_id:
                from app.models.unit import Unit
                unit_result = await self.db.execute(select(Unit).where(Unit.id == unit_id))
                unit = unit_result.scalar_one_or_none()
                if unit:
                    unit_name = unit.name
            title = f"{unit_name}_{date_str}"

        yapilan = [i.id for i in items if i.category == ItemCategory.YAPILAN_ISLER]
        yapilacak = [i.id for i in items if i.category == ItemCategory.YAPILACAK_ISLER]
        koordinasyon = [i.id for i in items if i.category == ItemCategory.KORDINASYON_GEREKTIREN_ISLER]

        new_report = ActivityReport(
            title=title,
            year=report_year,
            month=report_month,
            status=ReportStatus.PENDING,
            user_id=current_user_id,
            yapilan_is_ids=yapilan,
            yapilacak_is_ids=yapilacak,
            koordinasyon_is_ids=koordinasyon
        )
        self.db.add(new_report)
        await self.db.commit()
        await self.db.refresh(new_report)
        return await self._attach_items_to_report(new_report)

    
    async def merge_reports(self, report_ids: list[int], current_user_id: int, title: str | None = None) -> ActivityReportResponse:
        result = await self.db.execute(
            select(ActivityReport).where(ActivityReport.id.in_(report_ids))
        )
        reports = result.scalars().all()
        
        if not reports:
            raise NotFoundException("Seçilen raporlar bulunamadı.")
            
        first_report = reports[0]
        report_year = first_report.year
        report_month = first_report.month
        
        unit_id = None
        from app.models.user import User
        user_res = await self.db.execute(
            select(User).where(User.id == first_report.user_id)
        )
        report_user = user_res.scalars().first()
        if report_user:
            unit_id = report_user.unit_id


        if not title:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            unit_name = "Birim"
            if unit_id:
                from app.models.unit import Unit
                unit_result = await self.db.execute(select(Unit).where(Unit.id == unit_id))
                unit = unit_result.scalar_one_or_none()
                if unit:
                    unit_name = unit.name
            title = f"{unit_name}_{date_str}"
            
        yapilan = []
        yapilacak = []
        koordinasyon = []
        
        for r in reports:
            yapilan.extend(r.yapilan_is_ids or [])
            yapilacak.extend(r.yapilacak_is_ids or [])
            koordinasyon.extend(r.koordinasyon_is_ids or [])
            
        # Optional: remove duplicates but keep order
        yapilan = list(dict.fromkeys(yapilan))
        yapilacak = list(dict.fromkeys(yapilacak))
        koordinasyon = list(dict.fromkeys(koordinasyon))

        new_report = ActivityReport(
            title=title,
            year=report_year,
            month=report_month,
            status=ReportStatus.PENDING,
            user_id=current_user_id,
            yapilan_is_ids=yapilan,
            yapilacak_is_ids=yapilacak,
            koordinasyon_is_ids=koordinasyon
        )
        self.db.add(new_report)
        await self.db.commit()
        await self.db.refresh(new_report)
        return await self._attach_items_to_report(new_report)

    async def transfer_report(self, report_id: int, current_user: User) -> ActivityReportResponse:
        report = await self.report_repo.get_with_items(report_id)
        if not report:
            raise NotFoundException("Rapor bulunamadı.")
        if report.user_id != current_user.id:
            raise ForbiddenException("Sadece kendi oluşturduğunuz raporu aktarabilirsiniz.")
        if report.status != ReportStatus.APPROVED:
            raise BadRequestException("Sadece tamamen onaylanmış raporlar aktarılabilir.")
        if not current_user.manager_id:
            raise BadRequestException("Üst yöneticiniz bulunamadığı için aktarım yapılamaz.")

        # Üst yöneticinin bu yıl/ay için açtığı raporu bul
        query = select(ActivityReport).where(
            ActivityReport.user_id == current_user.manager_id,
            ActivityReport.year == report.year,
            ActivityReport.month == report.month,
        )
        res = await self.db.execute(query)
        manager_report = res.scalars().first()
        if not manager_report:
            # If manager report does not exist, create it automatically
            manager_report = ActivityReport(
                user_id=current_user.manager_id,
                year=report.year,
                month=report.month,
                status=ReportStatus.DRAFT,
            )
            self.db.add(manager_report)
            await self.db.flush()
            # Notify manager about the created report
            notif_service = NotificationService(self.db)
            await notif_service.create_notification(NotificationCreate(
                user_id=current_user.manager_id,
                message=f"{current_user.full_name}, bir rapor aktarmak istedi ancak sizin için yeni bir {report.year}/{report.month} raporu oluşturuldu.",
                type="INFO"
            ))

        # Kendi raporundaki onaylı satırları manager raporuna aktar (Senkronizasyon)
        query_items = select(ReportItem).where(
            ReportItem.report_id == manager_report.id,
            ReportItem.creator_id == current_user.id
        )
        res_items = await self.db.execute(query_items)
        existing_transferred_items = res_items.scalars().all()
        
        existing_by_source = {item.source_item_id: item for item in existing_transferred_items if item.source_item_id}
        legacy_items = [item for item in existing_transferred_items if not item.source_item_id]
        existing_by_content = {item.content: item for item in legacy_items}
        
        approved_items = [item for item in report.items if item.status == ReportStatus.APPROVED]
        matched_existing_ids = set()
        
        for item in approved_items:
            content_prefix = f"[{item.creator.full_name}] " if item.creator else ""
            new_content = content_prefix + item.content
            
            existing = existing_by_source.get(item.id)
            if not existing and new_content in existing_by_content:
                existing = existing_by_content[new_content]
                
            if existing:
                content_changed = (
                    existing.content != new_content or
                    existing.category != item.category or
                    existing.related_institutions != item.related_institutions or
                    existing.solution_proposals != item.solution_proposals
                )
                
                existing.category = item.category
                existing.content = new_content
                existing.related_institutions = item.related_institutions
                existing.solution_proposals = item.solution_proposals
                existing.display_order = item.display_order
                existing.source_item_id = item.id
                
                if content_changed:
                    existing.status = ReportStatus.PENDING
                    existing.rejection_note = None
                    
                matched_existing_ids.add(existing.id)
            else:
                new_item = ReportItem(
                    report_id=manager_report.id,
                    transfer_manager_id=current_user.id,
                    source_item_id=item.id,
                    creator_id=item.creator_id,
                    category=item.category,
                    content=item.content,
                    related_institutions=item.related_institutions,
                    solution_proposals=item.solution_proposals,
                    display_order=item.display_order,
                    status=item.status,
                    rejection_note=item.rejection_note,
                )
                self.db.add(new_item)
                await self.db.flush()

                # Update manager_report category lists based on original item's category
                if item.category == ItemCategory.YAPILAN_ISLER:
                    manager_report.yapilan_is_ids = (manager_report.yapilan_is_ids or []) + [new_item.id]
                elif item.category == ItemCategory.YAPILACAK_ISLER:
                    manager_report.yapilacak_is_ids = (manager_report.yapilacak_is_ids or []) + [new_item.id]
                elif item.category == ItemCategory.KORDINASYON_GEREKTIREN_ISLER:
                    manager_report.koordinasyon_is_ids = (manager_report.koordinasyon_is_ids or []) + [new_item.id]

            
        self.db.add(manager_report)

        # Çıkarılan veya onayı kaldırılan satırları sil
        for item in existing_transferred_items:
            if item.id not in matched_existing_ids:
                await self.db.delete(item)

        # ---- Deduplicate items in the manager report ----
        # Remove any duplicate items that may have been created during transfer.
        # We consider items duplicate if they have the same source_item_id (when present) or
        # the same content and creator_id combination.
        dedup_query = select(ReportItem).where(ReportItem.report_id == manager_report.id)
        dedup_res = await self.db.execute(dedup_query)
        all_items = dedup_res.scalars().all()
        seen_by_source = {}
        seen_by_content = {}
        for itm in all_items:
            # Prefer source_item_id as the unique identifier
            if itm.source_item_id:
                if itm.source_item_id in seen_by_source:
                    await self.db.delete(itm)
                else:
                    seen_by_source[itm.source_item_id] = itm.id
            else:
                key = (itm.content, itm.creator_id)
                if key in seen_by_content:
                    await self.db.delete(itm)
                else:
                    seen_by_content[key] = itm.id
        # -------------------------------------------------

        await LogService.create_log(
            db=self.db,
            action="TRANSFER_REPORT",
            user_id=current_user.id,
            entity_type="REPORT",
            entity_id=manager_report.id,
            details={"source_report_id": report_id}
        )
        
        await self.db.commit()
        return await self.get_report_by_id(manager_report.id, current_user)

    async def pass_down_rejection(self, item_id: int, current_user: User, extra_note: str) -> ActivityReportResponse:
        query = select(ReportItem).where(ReportItem.id == item_id, ReportItem.creator_id == current_user.id)
        res = await self.db.execute(query)
        item = res.scalars().first()
        
        if not item:
            raise NotFoundException("Satır bulunamadı veya yetkiniz yok.")
        
        if item.status != ReportStatus.REJECTED:
            raise BadRequestException("Sadece reddedilmiş satırları alta iletebilirsiniz.")
            
        if not item.source_item_id:
            raise BadRequestException("Bu satır bir alt kaynaktan kopyalanmamış (Orijinal satır bulunamadı).")

        # Asıl satırı bul
        source_query = select(ReportItem).where(ReportItem.id == item.source_item_id)
        source_res = await self.db.execute(source_query)
        source_item = source_res.scalars().first()
        
        if not source_item:
            raise NotFoundException("Orijinal satır veritabanında bulunamadı.")
            
        # Asıl satırı reddet ve notu birleştir
        source_item.status = ReportStatus.REJECTED
        
        # Asıl raporu da reddedilmiş duruma çek
        source_report_query = select(ActivityReport).where(ActivityReport.id == source_item.report_id)
        source_report_res = await self.db.execute(source_report_query)
        source_report = source_report_res.scalars().first()
        if source_report:
            source_report.status = ReportStatus.REJECTED
        
        combined_note = f"[Üst Yönetici]: {item.rejection_note or 'Belirtilmedi'}\n"
        if extra_note:
            combined_note += f"[Yönetici ({current_user.full_name})]: {extra_note}"
            
        source_item.rejection_note = combined_note
        
        # Orijinal oluşturana bildirim gönder
        if source_item.creator_id:
            notif_service = NotificationService(self.db)
            await notif_service.create_notification(NotificationCreate(
                user_id=source_item.creator_id,
                message=f"Bir faaliyet satırınız alta iletilerek reddedildi. Neden: {combined_note}",
                type="REJECTED_ITEM",
                reference_id=source_item.id
            ))
            
        await LogService.create_log(
            db=self.db,
            action="PASS_DOWN_REJECTION",
            user_id=current_user.id,
            entity_type="REPORT_ITEM",
            entity_id=source_item.id,
            details={"rejection_note": combined_note, "source_item_id": item_id}
        )
            
        await self.db.commit()
        return await self.get_report_by_id(item.report_id, current_user)

    async def get_unit_report_items(
        self,
        current_user: User,
        year: Optional[int] = None,
        month: Optional[int] = None,
        status: Optional[str] = None,
        search_text: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        creator_ids: Optional[List[int]] = None,
        institutions: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[dict], int]:
        """
        Yöneticinin kendi oluşturduğu raporların içerisindeki (astlar tarafından eklenmiş)
        satırları (ReportItem) detaylarıyla birlikte getirir.
        """
        from sqlalchemy import and_, or_, select
        from app.models.report import ActivityReport as Report, ReportItem
        from app.models.user import User as UserModel

        # Yöneticinin kendi raporlarına eklenen öğeler (kendisi hariç)
        # Note: If the manager wants to see all items including theirs, we remove `ReportItem.creator_id != current_user.id`
        # User requested: "astları hangi rapora hangi satırları eklemiş" -> so `ReportItem.creator_id != current_user.id`
        
        query = select(ReportItem, Report, UserModel).join(
            Report, Report.id == ReportItem.report_id
        ).outerjoin(
            UserModel, UserModel.id == ReportItem.creator_id
        ).where(
            and_(
                Report.user_id == current_user.id,
                ReportItem.creator_id != current_user.id,
                ReportItem.creator_id.isnot(None)
            )
        )

        if year:
            query = query.where(Report.year == year)
        if month:
            query = query.where(Report.month == month)
        if status:
            query = query.where(ReportItem.status == status)
        if creator_ids:
            query = query.where(ReportItem.creator_id.in_(creator_ids))
            
        if start_date:
            try:
                start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                query = query.where(ReportItem.created_at >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.where(ReportItem.created_at <= end_dt)
            except ValueError:
                pass

        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.where(
                or_(
                    ReportItem.content.ilike(search_pattern),
                    ReportItem.related_institutions.ilike(search_pattern),
                    ReportItem.solution_proposals.ilike(search_pattern),
                    UserModel.full_name.ilike(search_pattern)
                )
            )

        if institutions:
            inst_list = [i.strip() for i in institutions.split(",") if i.strip()]
            if inst_list:
                inst_conditions = [ReportItem.related_institutions.ilike(f"%{inst}%") for inst in inst_list]
                query = query.where(
                    and_(
                        ReportItem.category == "KORDINASYON_GEREKTIREN_ISLER",
                        or_(*inst_conditions)
                    )
                )

        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.order_by(ReportItem.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        response_items = []
        for item, report, user in rows:
            response_items.append({
                "id": item.id,
                "report_id": item.report_id,
                "report_year": report.year,
                "report_month": report.month,
                "content": item.content,
                "category": item.category,
                "status": item.status,
                "created_at": item.created_at,
                "creator_id": user.id if user else None,
                "creator_name": user.full_name if user else None,
                "creator": {"id": user.id, "full_name": user.full_name, "email": user.email, "title": user.title, "role": user.role, "created_at": user.created_at, "updated_at": user.updated_at} if user else None,
                "updated_at": item.updated_at if hasattr(item, "updated_at") else item.created_at,
                "related_institutions": item.related_institutions,
                "solution_proposals": item.solution_proposals
            })
            
        return response_items, total_count