from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import urllib.parse

from app.api import deps
from app.models.report import ItemCategory, ReportStatus
from app.models.user import User
from app.schemas.report import ReportFilter
from app.services.export_service import ExportService
from app.services.report_service import ReportService
from app.services.log_service import LogService

router = APIRouter()


@router.get(
    "/excel",
    summary="Faaliyet Raporlarını Excel Olarak Dışa Aktar",
    description="Filtrelenen tüm faaliyet raporlarını .xlsx Excel formatında dosya akışı olarak indirir."
)
async def export_reports_excel(
    year: Optional[int] = Query(None, description="Yıl filtresi (ör. 2026)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Ay filtresi (1-12)"),
    status: Optional[ReportStatus] = Query(None, description="Rapor durumu (DRAFT / SAVED)"),
    user_ids: Optional[list[int]] = Query(None, description="Kullanıcı ID listesi filtresi"),
    unit_id: Optional[int] = Query(None, description="Birim ID filtresi"),
    category: Optional[ItemCategory] = Query(None, description="Faaliyet kategori filtresi"),
    search_text: Optional[str] = Query(None, description="Rapor başlığı veya içeriğinde metin arama"),
    start_date: Optional[str] = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
    report_ids: Optional[list[int]] = Query(None, description="Spesifik rapor ID'leri"),
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
        end_date=end_date,
        report_ids=report_ids
    )

    report_service = ReportService(db)
    
    items = []
    if report_ids:
        # Eğer özel olarak rapor ID'leri istenmişse, tek tek get_report_by_id ile çekiyoruz
        # Bu sayede check_if_shared_with_user yetkilendirmesinden de faydalanmış oluyoruz.
        for rid in report_ids:
            try:
                report_data = await report_service.get_report_by_id(rid, current_user=current_user)
                items.append(report_data)
            except Exception:
                pass # Yetkisi yoksa veya bulunamadıysa atla
    else:
        # Filtreye uyan tüm raporları çekmek için geniş limit veriyoruz
        paginated = await report_service.get_reports_paginated(
            filters=filters,
            page=1,
            page_size=1000,
            current_user=current_user
        )
        items = paginated.items

    excel_stream = await ExportService.export_reports_to_excel(items, db)

    unit_name = current_user.unit.name if current_user.unit else "Birim"
    safe_unit_name = unit_name.replace(" ", "_")
    filename = f"{safe_unit_name}-birleştirilmiş_faaliyet_raporu.xlsx"
    encoded_filename = urllib.parse.quote(filename)

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    await LogService.create_log(
        db=db,
        action="EXPORT_EXCEL",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=None,
        details={"report_ids": report_ids, "filename": filename}
    )
    await db.commit()
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )


@router.get(
    "/pdf/{report_id}",
    summary="Faaliyet Raporunu PDF Olarak Dışa Aktar",
    description="Tekil bir faaliyet raporunu kurumsal PDF formatında indirir."
)
async def export_report_pdf(
    report_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    report_service = ReportService(db)
    report_data = await report_service.get_report_by_id(report_id, current_user=current_user)

    pdf_stream = await ExportService.export_report_to_pdf(report_data, db)

    unit_name = report_data.user.unit.name if report_data.user and report_data.user.unit else "Birim"
    safe_unit_name = unit_name.replace(" ", "_")
    filename = f"{safe_unit_name}-{report_data.year}_{report_data.month:02d}.pdf"
    encoded_filename = urllib.parse.quote(filename)
    
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    await LogService.create_log(
        db=db,
        action="EXPORT_PDF",
        user_id=current_user.id,
        entity_type="REPORT",
        entity_id=report_id,
        details={"filename": filename}
    )
    await db.commit()
    
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers=headers
    )


@router.get(
    "/excel-template",
    summary="Boş Excel Şablonunu İndir",
    description="Kullanıcıların veri girebilmesi için boş bir faaliyet raporu Excel şablonu indirir."
)
async def download_excel_template():
    excel_stream = ExportService.generate_excel_template()
    filename = "faaliyet_raporu_taslagi.xlsx"
    encoded_filename = urllib.parse.quote(filename)
    
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )