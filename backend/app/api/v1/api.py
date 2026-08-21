from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, units, reports, export, report_shares, notifications, institutions, logs, chat

api_router = APIRouter()

# Alt router'ların v1 API yoluna eklenmesi
api_router.include_router(auth.router, prefix="/auth", tags=["Kimlik Doğrulama"])
api_router.include_router(users.router, prefix="/users", tags=["Kullanıcı Yönetimi"])
api_router.include_router(units.router, prefix="/units", tags=["Birim Yönetimi"])
api_router.include_router(reports.router, prefix="/reports", tags=["Faaliyet Raporları"])
api_router.include_router(export.router, prefix="/export", tags=["Dışa Aktarım"])
api_router.include_router(report_shares.router, prefix="/report-shares", tags=["Rapor Paylaşımları"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Bildirimler"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["Kurum Yönetimi"])
api_router.include_router(logs.router, prefix="/logs", tags=["Sistem Logları"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Asistan"])