from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api import deps
from app.core.response import DataResponse
from app.models.report import ItemCategory, ReportStatus
from app.models.user import User
from app.schemas.common import PaginatedData
from app.schemas.report import (
    MergeReportsRequest,
    MergeItemsRequest,
    ActivityReportCreate,
    ActivityReportUpdate,
    ActivityReportResponse,
    ReportItemCreate,
    ReportItemUpdate,
    ReportItemReview,
    ReportFilter,
    ReportItemProposalResponse,
    ProposalRespondRequest,
    UnitReportItemResponse
)
from app.services.report_service import ReportService
from app.services.report_import_service import ReportImportService
from app.models.report import ReportItemProposal, ProposalStatus
from app.services.log_service import LogService

router = APIRouter()

@router.get(
    "/import/template",
    summary="Boş Excel Şablonu İndir",
    description="Sistemin kabul ettiği boş bir excel taslağı döndürür."
)
async def download_import_template(db: AsyncSession = Depends(deps.get_db)):
    from app.services.export_service import ExportService
    from fastapi.responses import StreamingResponse
    
    stream = await ExportService.export_reports_to_excel([], db)
    
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=faaliyet_raporu_taslagi.xlsx",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@router.post(
    "/import/preview",
    response_model=DataResponse[Dict[str, Any]],
    summary="Excel'den İçeri Aktarma Önizlemesi",
    description="Yüklenen Excel dosyasını işler, eksikleri/hataları bulur ve doğrulanacak bir önizleme listesi döner."
)
async def preview_import(
    file: UploadFile = File(...),
    target: str = Form("OWN_REPORT"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    import_service = ReportImportService(db, report_service)
    file_bytes = await file.read()
    result = await import_service.preview_import(file_bytes, current_user, target)
    return DataResponse(
        data=result,
        message="Önizleme oluşturuldu."
    )

@router.post(
    "/import/revalidate",
    response_model=DataResponse[Dict[str, Any]],
    summary="Düzenlenmiş Veriyi Yeniden Doğrular",
    description="Önizleme tablosunda yapılan değişiklikleri (personel adı vb.) tekrar doğrular."
)
async def revalidate_import(
    data: Dict[str, Any] = Body(...),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    import_service = ReportImportService(db, report_service)
    result = await import_service.revalidate_import(data, current_user)
    return DataResponse(
        data=result,
        message="Yeniden doğrulama tamamlandı."
    )

@router.post(
    "/import/execute",
    response_model=DataResponse[Dict[str, Any]],
    summary="Excel'den İçeri Aktarma İşlemini Gerçekleştirir",
    description="Önizleme sonrasında kesinleştirilen (çatışmaları çözülmüş) veriyi veritabanına kaydeder."
)
async def execute_import(
    data: Dict[str, Any] = Body(...),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    import_service = ReportImportService(db, report_service)
    result = await import_service.execute_import(data, current_user)
    
    await LogService.create_log(
        db=db,
        action="IMPORT_EXCEL",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=None,
        details={"target": "execute_import"}
    )
    await db.commit()
    
    return DataResponse(
        data=result,
        message="İçeri aktarma işlemi tamamlandı."
    )



@router.get(
    "",
    response_model=DataResponse[PaginatedData[ActivityReportResponse]],
    summary="Faaliyet Raporları Listesi ve Gelişmiş Filtreleme",
    description="Yıl, ay, durum, kullanıcı, birim, kategori ve metin içi kelime aramasına göre faaliyet raporlarını filtreler ve sayfalı getirir."
)
async def read_reports(
    year: Optional[int] = Query(None, description="Yıl filtresi (ör. 2026)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Ay filtresi (1-12)"),
    status: Optional[ReportStatus] = Query(None, description="Rapor durumu (DRAFT / SAVED)"),
    user_ids: Optional[list[int]] = Query(None, description="Kullanıcı ID listesi filtresi"),
    unit_id: Optional[int] = Query(None, description="Birim (Daire / Şube) ID filtresi"),
    category: Optional[ItemCategory] = Query(None, description="Faaliyet kategori filtresi"),
    search_text: Optional[str] = Query(None, description="Rapor başlığı veya içeriğinde metin arama"),
    start_date: Optional[str] = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(10, ge=1, le=1000, description="Sayfa başına kayıt sayısı"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    filters = ReportFilter(
        year=year,
        month=month,
        status=status,
        user_ids=user_ids,
        unit_id=unit_id,
        category=category,
        search_text=search_text,
        start_date=start_date,
        end_date=end_date
    )

    report_service = ReportService(db)
    paginated_reports = await report_service.get_reports_paginated(
        filters=filters,
        page=page,
        page_size=page_size,
        current_user=current_user
    )
    return DataResponse(
        data=paginated_reports,
        message="Faaliyet raporları başarıyla getirildi."
    )

@router.get(
    "/unit-items",
    response_model=DataResponse[PaginatedData[UnitReportItemResponse]],
    summary="Birim Raporu Satırları",
    description="Yöneticilerin kendi oluşturduğu raporların içerisindeki (astlar tarafından eklenmiş) satırları detaylarıyla birlikte getirir."
)
async def read_unit_report_items(
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[str] = None,
    search_text: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    creator_ids: Optional[str] = None,  # comma-separated list of IDs
    institutions: Optional[str] = None,
    page: int = Query(1, ge=1, description="Sayfa numarası (1'den başlar)"),
    page_size: int = Query(10, ge=1, le=100, description="Sayfa başına kayıt sayısı"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    
    parsed_creator_ids = None
    if creator_ids:
        try:
            parsed_creator_ids = [int(cid.strip()) for cid in creator_ids.split(",") if cid.strip()]
        except ValueError:
            pass

    skip = (page - 1) * page_size
    items, total = await report_service.get_unit_report_items(
        current_user=current_user,
        year=year,
        month=month,
        status=status,
        search_text=search_text,
        start_date=start_date,
        end_date=end_date,
        creator_ids=parsed_creator_ids,
        institutions=institutions,
        skip=skip,
        limit=page_size
    )
    
    paginated_data = PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if page_size > 0 else 0
    )

    return DataResponse(
        data=paginated_data,
        message="Birim raporu satırları başarıyla getirildi."
    )



@router.get(
    "/{report_id}",
    response_model=DataResponse[ActivityReportResponse],
    summary="Faaliyet Raporu Detayı",
    description="ID değerine göre faaliyet raporunu tüm detay satırlarıyla birlikte getirir."
)
async def read_report_by_id(
    report_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    report_data = await report_service.get_report_by_id(report_id, current_user=current_user)
    return DataResponse(
        data=report_data,
        message="Faaliyet raporu detayı başarıyla getirildi."
    )


@router.post(
    "",
    response_model=DataResponse[ActivityReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Faaliyet Raporu Oluşturma",
    description="Yöneticiler için yeni dönem faaliyet raporu dosyasını açar."
)
async def create_report(
    report_in: ActivityReportCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    created_report = await report_service.create_report(
        user_id=current_user.id,
        report_in=report_in
    )
    return DataResponse(
        data=created_report,
        message="Faaliyet raporu başarıyla oluşturuldu."
    )


@router.put(
    "/{report_id}",
    response_model=DataResponse[ActivityReportResponse],
    summary="Faaliyet Raporu Güncelleme",
    description="Mevcut faaliyet raporu ana bilgilerini günceller."
)
async def update_report(
    report_id: int,
    report_in: ActivityReportUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.update_report(
        report_id=report_id,
        user_id=current_user.id,
        report_in=report_in,
        is_admin=current_user.is_superuser
    )
    return DataResponse(
        data=updated_report,
        message="Faaliyet raporu başarıyla güncellendi."
    )


@router.delete(
    "/{report_id}",
    response_model=DataResponse[bool],
    summary="Faaliyet Raporu Silme",
    description="Faaliyet raporunu veritabanından siler."
)
async def delete_report(
    report_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    result = await report_service.delete_report(
        report_id=report_id,
        user_id=current_user.id,
        is_admin=current_user.is_superuser
    )
    return DataResponse(
        data=result,
        message="Faaliyet raporu başarıyla silindi."
    )

# --- YENİ EKLENEN SATIR (ITEM) BAZLI API'LER ---

@router.post(
    "/{report_id}/items",
    response_model=DataResponse[ActivityReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Rapora Satır Ekle",
    description="Bir astın kendi yöneticisinin raporuna yeni faaliyet satırı eklemesini sağlar."
)
async def add_report_item(
    report_id: int,
    item_in: ReportItemCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.create_report_item(
        report_id=report_id,
        current_user=current_user,
        item_in=item_in
    )
    return DataResponse(
        data=updated_report,
        message="Satır başarıyla eklendi."
    )


@router.put(
    "/{report_id}/items/{item_id}",
    response_model=DataResponse[ActivityReportResponse],
    summary="Rapordaki Satırı Güncelle",
    description="Astın sadece kendi eklediği satırı (onaylanmamışsa) güncellemesini sağlar."
)
async def update_report_item(
    report_id: int,
    item_id: int,
    item_in: ReportItemUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.update_report_item(
        report_id=report_id,
        item_id=item_id,
        current_user=current_user,
        item_in=item_in
    )
    return DataResponse(
        data=updated_report,
        message="Satır başarıyla güncellendi."
    )


@router.delete(
    "/{report_id}/items/{item_id}",
    response_model=DataResponse[ActivityReportResponse],
    summary="Rapordaki Satırı Sil",
    description="Astın sadece kendi eklediği satırı silmesini sağlar."
)
async def delete_report_item(
    report_id: int,
    item_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.delete_report_item(
        report_id=report_id,
        item_id=item_id,
        current_user=current_user
    )
    return DataResponse(
        data=updated_report,
        message="Satır başarıyla silindi."
    )

@router.get(
    "/items/{item_id}/report-id",
    response_model=DataResponse[int],
    summary="Satırın Bağlı Olduğu Raporun ID'sini Getir",
    description="Bildirim yönlendirmeleri için kullanılır."
)
async def get_report_id_by_item(
    item_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    from sqlalchemy import select
    from app.models.report import ReportItem
    from fastapi import HTTPException
    
    query = select(ReportItem.report_id).where(ReportItem.id == item_id)
    res = await db.execute(query)
    report_id = res.scalar()
    
    if not report_id:
        raise HTTPException(status_code=404, detail="Satır bulunamadı.")
        
    return DataResponse(
        data=report_id,
        message="Rapor ID getirildi."
    )


@router.put(
    "/{report_id}/items/{item_id}/review",
    response_model=DataResponse[ActivityReportResponse],
    summary="Satırı Onayla veya Reddet",
    description="Yöneticinin rapordaki bir satırı onaylamasını veya red notu ile reddetmesini sağlar."
)
async def review_report_item(
    report_id: int,
    item_id: int,
    review_in: ReportItemReview,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.review_report_item(
        report_id=report_id,
        item_id=item_id,
        current_user=current_user,
        review_in=review_in
    )
    return DataResponse(
        data=updated_report,
        message="Satır değerlendirmesi kaydedildi."
    )


@router.post(
    "/{report_id}/approve",
    response_model=DataResponse[ActivityReportResponse],
    summary="Tüm Raporu Onayla",
    description="Yöneticinin tüm satırları onayladıktan sonra dosyayı tamamen kapatmasını sağlar."
)
async def approve_report(
    report_id: int,
    force: bool = Query(False, description="Eksik kullanıcılara rağmen zorla onaylama"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    from fastapi import HTTPException
    from app.models.report import ReportStatus
    report_service = ReportService(db)
    # Fetch report data to check status
    report_data = await report_service.get_report_by_id(report_id, current_user=current_user)
    if not report_data:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    # If already approved, treat as success (force flag irrelevant)
    if report_data.status == ReportStatus.APPROVED:
        return DataResponse(
            data=report_data,
            message="Rapor zaten onaylandı."
        )
    # Proceed with approval; missing users are informational only
    success, report_data, missing = await report_service.approve_full_report(
        report_id=report_id,
        current_user=current_user,
        force=force,
    )
    # approve_full_report always returns success=True, so we directly return the response
    return DataResponse(
        data=report_data,
        message="Rapor başarıyla onaylandı.",
        # optional: missing=missing
    )


@router.post(
    "/{report_id}/transfer",
    response_model=DataResponse[ActivityReportResponse],
    summary="Raporu Üst Yöneticiye Aktar",
    description="Onaylanmış rapordaki tüm satırları üst yöneticinin ilgili ay/yıl raporuna ekler."
)
async def transfer_report(
    report_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    transferred_report = await report_service.transfer_report(
        report_id=report_id,
        current_user=current_user
    )
    return DataResponse(
        data=transferred_report,
        message="Rapor başarıyla üst yöneticiye aktarıldı."
    )

class PassDownRequest(BaseModel):
    extra_note: str = ""

@router.post(
    "/{report_id}/items/{item_id}/pass-down",
    response_model=DataResponse[ActivityReportResponse],
    summary="Reddi Alta İlet",
    description="Üst yönetici tarafından reddedilen bir satırı, kendi personeline reddedilmiş olarak iletir."
)
async def pass_down_rejection_endpoint(
    report_id: int,
    item_id: int,
    request: PassDownRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    updated_report = await report_service.pass_down_rejection(
        item_id=item_id,
        current_user=current_user,
        extra_note=request.extra_note
    )
    return DataResponse(
        data=updated_report,
        message="Red durumu alt çalışana başarıyla iletildi."
    )

@router.get(
    "/proposals/me",
    response_model=DataResponse[List[ReportItemProposalResponse]],
    summary="Bana Gelen Faaliyet Teklifleri",
    description="Yöneticinin benim adıma eklediği ve onayımı bekleyen faaliyet satırlarını getirir."
)
async def get_my_proposals(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    query = select(ReportItemProposal).options(
        selectinload(ReportItemProposal.creator)
    ).where(
        ReportItemProposal.target_user_id == current_user.id,
        ReportItemProposal.status == ProposalStatus.PENDING
    ).order_by(ReportItemProposal.created_at.desc())
    
    result = await db.execute(query)
    proposals = result.scalars().all()
    
    return DataResponse(
        data=[ReportItemProposalResponse.model_validate(p) for p in proposals],
        message="Bekleyen teklifler getirildi."
    )

@router.post(
    "/proposals/{proposal_id}/respond",
    response_model=DataResponse[bool],
    summary="Teklife Yanıt Ver (Onayla/Reddet)",
    description="Gelen teklife onay veya red yanıtı verir."
)
async def respond_to_proposal(
    proposal_id: int,
    request: ProposalRespondRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    from sqlalchemy.future import select
    from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
    from app.models.report import ReportItem, ReportStatus

    query = select(ReportItemProposal).where(ReportItemProposal.id == proposal_id)
    result = await db.execute(query)
    proposal = result.scalars().first()
    
    if not proposal:
        raise NotFoundException("Teklif bulunamadı.")
        
    if proposal.target_user_id != current_user.id:
        raise ForbiddenException("Bu teklife yanıt verme yetkiniz yok.")
        
    if proposal.status != ProposalStatus.PENDING:
        raise BadRequestException("Bu teklif zaten yanıtlanmış.")
        
    proposal.status = ProposalStatus.APPROVED if request.is_approved else ProposalStatus.REJECTED
    
    from app.models.notification import Notification

    if request.is_approved:
        # Check if changed
        is_changed = False
        if request.content is not None and request.content != proposal.content:
            is_changed = True
        if request.related_institutions is not None and request.related_institutions != proposal.related_institutions:
            is_changed = True
        if request.solution_proposals is not None and request.solution_proposals != proposal.solution_proposals:
            is_changed = True
            
        content = request.content if request.content is not None else proposal.content
        related_institutions = request.related_institutions if request.related_institutions is not None else proposal.related_institutions
        solution_proposals = request.solution_proposals if request.solution_proposals is not None else proposal.solution_proposals
        
        # Onaylarsa başına adını ekle
        content = f"[{current_user.full_name or current_user.email}] {content}"
        
        from app.models.report import ActivityReport
        manager_report = await db.get(ActivityReport, proposal.manager_report_id)
        
        new_item = ReportItem(
            report_id=proposal.manager_report_id,
            category=proposal.category,
            content=content,
            related_institutions=related_institutions,
            solution_proposals=solution_proposals,
            creator_id=proposal.target_user_id, # Astın ID'si ile kaydedilir
            status=ReportStatus.PENDING if is_changed else ReportStatus.APPROVED
        )
        db.add(new_item)
        await db.flush()
        
        if manager_report:
            from sqlalchemy.orm.attributes import flag_modified
            if new_item.category == ItemCategory.YAPILAN_ISLER:
                manager_report.yapilan_is_ids = (manager_report.yapilan_is_ids or []) + [new_item.id]
                flag_modified(manager_report, "yapilan_is_ids")
            elif new_item.category == ItemCategory.YAPILACAK_ISLER:
                manager_report.yapilacak_is_ids = (manager_report.yapilacak_is_ids or []) + [new_item.id]
                flag_modified(manager_report, "yapilacak_is_ids")
            elif new_item.category == ItemCategory.KORDINASYON_GEREKTIREN_ISLER:
                manager_report.koordinasyon_is_ids = (manager_report.koordinasyon_is_ids or []) + [new_item.id]
                flag_modified(manager_report, "koordinasyon_is_ids")
        
        # Düzenleme yapıldıysa yöneticiye bildirim gönder
        if is_changed:
            notif_msg = f"{current_user.full_name or current_user.email} sizin eklediğiniz faaliyeti düzenleyerek onayladı."
            mgr_notif = Notification(
                user_id=proposal.creator_id,
                message=notif_msg,
                is_read=False,
                type="PROPOSAL_EDITED",
                reference_id=proposal.id
            )
            db.add(mgr_notif)
    
    # İlgili bildirimi okundu yap (Alt çalışana gelen bildirim)
    notif_query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.reference_id == proposal_id,
        Notification.type == "PROPOSAL_PENDING"
    )
    notif_res = await db.execute(notif_query)
    notif = notif_res.scalars().first()
    if notif:
        notif.is_read = True
    
    await db.commit()
    
    return DataResponse(
        data=True,
        message="Teklif başarıyla yanıtlandı."
    )


@router.post("/merge-items", response_model=DataResponse[ActivityReportResponse], summary="Secilen Satirlari Birlestir")
async def merge_items(
    request_data: MergeItemsRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if current_user.role not in ["ADMIN", "MANAGER", "USER_MANAGER"] and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    report_service = ReportService(db)
    merged_report = await report_service.merge_items(
        item_ids=request_data.item_ids,
        current_user_id=current_user.id,
        title=request_data.title
    )
    
    return DataResponse(
        success=True,
        message="Secili satirlar basariyla yeni bir rapora donusturuldu.",
        data=merged_report
    )

@router.post("/merge", response_model=DataResponse[ActivityReportResponse])
async def merge_selected_reports(
    *,
    db: AsyncSession = Depends(deps.get_db),
    merge_in: MergeReportsRequest,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Seçilen birden fazla raporu tek bir rapor halinde birleştirir.
    """
    report_service = ReportService(db)
    try:
        merged_report = await report_service.merge_reports(
            report_ids=merge_in.report_ids,
            current_user_id=current_user.id,
            title=merge_in.title
        )
        return DataResponse(
            data=merged_report,
            message="Raporlar başarıyla birleştirildi."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
