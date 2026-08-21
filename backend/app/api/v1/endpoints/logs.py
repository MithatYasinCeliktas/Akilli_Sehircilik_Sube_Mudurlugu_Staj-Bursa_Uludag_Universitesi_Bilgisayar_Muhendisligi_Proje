from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import Response

from app.api import deps
from app.core.response import DataResponse
from app.models.user import User, UserRole
from app.schemas.common import PaginatedData
from app.schemas.system_log import SystemLogResponse
from app.services.log_service import LogService
import json

router = APIRouter()

@router.get(
    "",
    response_model=DataResponse[PaginatedData[SystemLogResponse]],
    summary="Sistem Loglarını Listele",
    description="Admin için tüm sistem loglarını filtrelenebilir ve sayfalı olarak getirir."
)
async def get_logs(
    user_id: Optional[int] = Query(None, description="Kullanıcı ID filtresi"),
    action: Optional[str] = Query(None, description="Aksiyon filtresi"),
    entity_type: Optional[str] = Query(None, description="Entity Type filtresi"),
    entity_id: Optional[int] = Query(None, description="Entity ID filtresi"),
    start_date: Optional[str] = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(20, ge=1, le=1000, description="Sayfa başına kayıt sayısı"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için Admin yetkisi gereklidir."
        )
        
    logs, total = await LogService.get_logs_paginated(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        skip=(page - 1) * page_size,
        limit=page_size
    )

    items = [SystemLogResponse.model_validate(log) for log in logs]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    paginated_data = PaginatedData[SystemLogResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

    return DataResponse(
        data=paginated_data,
        message="Sistem logları başarıyla getirildi."
    )

@router.get(
    "/export",
    summary="Sistem Loglarını JSON Olarak İndir",
    description="Sistem loglarını JSON dosyası olarak indirir."
)
async def export_logs_json(
    user_id: Optional[int] = Query(None, description="Kullanıcı ID filtresi"),
    action: Optional[str] = Query(None, description="Aksiyon filtresi"),
    entity_type: Optional[str] = Query(None, description="Entity Type filtresi"),
    entity_id: Optional[int] = Query(None, description="Entity ID filtresi"),
    start_date: Optional[str] = Query(None, description="Başlangıç tarihi (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Bitiş tarihi (YYYY-MM-DD)"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için Admin yetkisi gereklidir."
        )

    # Export işlemi için sayfalama yapmadan geniş aralık çekelim (örn: 10,000 kayıt)
    logs, _ = await LogService.get_logs_paginated(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date,
        skip=0,
        limit=10000
    )

    items = [SystemLogResponse.model_validate(log).model_dump(mode="json") for log in logs]
    json_data = json.dumps(items, ensure_ascii=False, indent=2)

    return Response(
        content=json_data,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=system_logs.json"
        }
    )
