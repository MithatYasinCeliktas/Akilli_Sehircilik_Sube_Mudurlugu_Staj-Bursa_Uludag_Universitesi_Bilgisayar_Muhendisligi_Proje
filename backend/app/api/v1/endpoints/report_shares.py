from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import deps
from app.models.user import User, UserRole
from app.models.report import ActivityReport
from app.models.report_share import ReportShare, ShareStatus
from app.schemas.report_share import ReportShareCreate, ReportShareResponse, ReportShareAction
from app.services.log_service import LogService

router = APIRouter()

@router.post("/request", response_model=ReportShareResponse)
async def create_share_request(
    *,
    db: AsyncSession = Depends(deps.get_db),
    share_in: ReportShareCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Rapor paylaşım talebi oluşturur.
    """
    if not share_in.target_user_id and not share_in.target_unit_id:
        raise HTTPException(
            status_code=400,
            detail="Hedef kullanıcı veya hedef birim belirtilmelidir.",
        )

    # Raporun kime ait olduğunu kontrol et
    report_result = await db.execute(
        select(ActivityReport).where(ActivityReport.id == share_in.report_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")
        
    can_share = False
    if report.user_id == current_user.id:
        can_share = True
    elif hasattr(report, 'creator_id') and report.creator_id == current_user.id:
        can_share = True
    elif current_user.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.USER_MANAGER]:
        can_share = True

    if not can_share:
        raise HTTPException(
            status_code=403, detail="Bu raporu paylaşma yetkiniz yok"
        )
        
    # Yöneticisi var mı kontrol et
    if not current_user.manager_id:
        # Eğer yöneticisi yoksa, doğrudan onaylı olarak da oluşturulabilir veya 
        # Hata dönebiliriz. Şimdilik doğrudan onaylı (APPROVED) yapalım.
        initial_status = ShareStatus.APPROVED
    else:
        initial_status = ShareStatus.PENDING

    # Daha önce aynı hedefe bekleyen veya onaylı talep var mı?
    query = select(ReportShare).where(
        ReportShare.report_id == share_in.report_id,
        ReportShare.requester_id == current_user.id,
        ReportShare.status.in_([ShareStatus.PENDING, ShareStatus.APPROVED])
    )
    if share_in.target_user_id:
        query = query.where(ReportShare.target_user_id == share_in.target_user_id)
    if share_in.target_unit_id:
        query = query.where(ReportShare.target_unit_id == share_in.target_unit_id)
        
    existing_result = await db.execute(query)
    if existing_result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="Bu rapor için belirtilen hedefe zaten bekleyen veya onaylanmış bir paylaşım var."
        )

    share_obj = ReportShare(
        report_id=share_in.report_id,
        requester_id=current_user.id,
        manager_id=current_user.manager_id,
        target_user_id=share_in.target_user_id,
        target_unit_id=share_in.target_unit_id,
        status=initial_status
    )
    db.add(share_obj)
    await db.commit()
    await db.refresh(share_obj)
    
    # Tüm ilişkileriyle birlikte döndür
    result = await db.execute(
        select(ReportShare)
        .options(
            selectinload(ReportShare.report),
            selectinload(ReportShare.requester),
            selectinload(ReportShare.manager),
            selectinload(ReportShare.target_user),
            selectinload(ReportShare.target_unit)
        )
        .where(ReportShare.id == share_obj.id)
    )
    
    await LogService.create_log(
        db=db,
        action="SHARE_REQUEST",
        user_id=current_user.id,
        entity_type="REPORT_SHARE",
        entity_id=share_obj.id,
        details={"report_id": share_in.report_id, "target_user_id": share_in.target_user_id, "target_unit_id": share_in.target_unit_id, "status": initial_status}
    )
    await db.commit()
    
    return result.scalar_one()


@router.get("/pending", response_model=List[ReportShareResponse])
async def get_pending_shares_for_manager(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Yöneticinin onaylaması beklenen paylaşım taleplerini listeler.
    """
    result = await db.execute(
        select(ReportShare)
        .options(
            selectinload(ReportShare.report),
            selectinload(ReportShare.requester),
            selectinload(ReportShare.target_user),
            selectinload(ReportShare.target_unit)
        )
        .where(
            ReportShare.manager_id == current_user.id,
            ReportShare.status == ShareStatus.PENDING
        )
        .order_by(ReportShare.created_at.desc())
    )
    return result.scalars().all()


@router.get("/approved", response_model=List[ReportShareResponse])
async def get_approved_shares_by_manager(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Yöneticinin daha önce onayladığı paylaşımları listeler (Geri alabilmesi için).
    """
    result = await db.execute(
        select(ReportShare)
        .options(
            selectinload(ReportShare.report),
            selectinload(ReportShare.requester),
            selectinload(ReportShare.target_user),
            selectinload(ReportShare.target_unit)
        )
        .where(
            ReportShare.manager_id == current_user.id,
            ReportShare.status == ShareStatus.APPROVED
        )
        .order_by(ReportShare.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/my-shares", response_model=List[ReportShareResponse])
async def get_my_shares(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Kullanıcının kendi paylaştığı veya paylaşmak istediği raporları listeler.
    """
    result = await db.execute(
        select(ReportShare)
        .options(
            selectinload(ReportShare.report),
            selectinload(ReportShare.manager),
            selectinload(ReportShare.target_user),
            selectinload(ReportShare.target_unit)
        )
        .where(ReportShare.requester_id == current_user.id)
        .order_by(ReportShare.created_at.desc())
    )
    return result.scalars().all()


@router.get("/shared-with-me", response_model=List[ReportShareResponse])
async def get_shared_with_me(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Kullanıcının kendisiyle (veya birimiyle) paylaşılan ve onaylanmış raporları listeler.
    """
    # Kullanıcının dahil olduğu birimler
    user_unit_ids = []
    if current_user.unit_id:
        user_unit_ids.append(current_user.unit_id)

    # Kriter: Onaylanmış olacak (APPROVED) 
    # ve target_user_id == current_user.id 
    # veya target_unit_id in [kullanıcının birimleri]
    
    query = (
        select(ReportShare)
        .options(
            selectinload(ReportShare.report),
            selectinload(ReportShare.requester),
            selectinload(ReportShare.target_user),
            selectinload(ReportShare.target_unit)
        )
        .where(ReportShare.status == ShareStatus.APPROVED)
    )
    
    conditions = []
    conditions.append(ReportShare.target_user_id == current_user.id)
    if user_unit_ids:
        conditions.append(ReportShare.target_unit_id.in_(user_unit_ids))
        
    from sqlalchemy import or_
    query = query.where(or_(*conditions))
    
    result = await db.execute(query.order_by(ReportShare.updated_at.desc()))
    return result.scalars().all()


@router.put("/{share_id}/approve", response_model=ReportShareResponse)
async def approve_share(
    share_id: int,
    action: ReportShareAction,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Yönetici tarafından paylaşımı onaylar.
    """
    result = await db.execute(select(ReportShare).where(ReportShare.id == share_id))
    share_obj = result.scalar_one_or_none()
    if not share_obj:
        raise HTTPException(status_code=404, detail="Paylaşım talebi bulunamadı")
        
    if share_obj.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu talebi onaylama yetkiniz yok")
        
    if share_obj.status != ShareStatus.PENDING:
        raise HTTPException(status_code=400, detail="Sadece bekleyen talepler onaylanabilir")

    share_obj.status = ShareStatus.APPROVED
    if action.note:
        share_obj.manager_note = action.note

    await LogService.create_log(
        db=db,
        action="SHARE_APPROVE",
        user_id=current_user.id,
        entity_type="REPORT_SHARE",
        entity_id=share_id,
        details={"note": action.note}
    )
    
    await db.commit()
    await db.refresh(share_obj)
    return share_obj


@router.put("/{share_id}/reject", response_model=ReportShareResponse)
async def reject_share(
    share_id: int,
    action: ReportShareAction,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Yönetici tarafından paylaşımı reddeder.
    """
    result = await db.execute(select(ReportShare).where(ReportShare.id == share_id))
    share_obj = result.scalar_one_or_none()
    if not share_obj:
        raise HTTPException(status_code=404, detail="Paylaşım talebi bulunamadı")
        
    if share_obj.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu talebi reddetme yetkiniz yok")
        
    if share_obj.status != ShareStatus.PENDING:
        raise HTTPException(status_code=400, detail="Sadece bekleyen talepler reddedilebilir")

    share_obj.status = ShareStatus.REJECTED
    if action.note:
        share_obj.manager_note = action.note

    await LogService.create_log(
        db=db,
        action="SHARE_REJECT",
        user_id=current_user.id,
        entity_type="REPORT_SHARE",
        entity_id=share_id,
        details={"note": action.note}
    )
    
    await db.commit()
    await db.refresh(share_obj)
    return share_obj


@router.put("/{share_id}/revoke", response_model=ReportShareResponse)
async def revoke_share(
    share_id: int,
    action: ReportShareAction,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Yönetici tarafından önceden onaylanmış bir paylaşımı iptal eder (Geri alır).
    """
    result = await db.execute(select(ReportShare).where(ReportShare.id == share_id))
    share_obj = result.scalar_one_or_none()
    if not share_obj:
        raise HTTPException(status_code=404, detail="Paylaşım talebi bulunamadı")
        
    if share_obj.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu paylaşımı geri alma yetkiniz yok")
        
    if share_obj.status != ShareStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Sadece onaylanmış paylaşımlar iptal edilebilir")

    share_obj.status = ShareStatus.REVOKED
    if action.note:
        share_obj.manager_note = action.note

    await LogService.create_log(
        db=db,
        action="SHARE_REVOKE",
        user_id=current_user.id,
        entity_type="REPORT_SHARE",
        entity_id=share_id,
        details={"note": action.note}
    )

    await db.commit()
    await db.refresh(share_obj)
    return share_obj
