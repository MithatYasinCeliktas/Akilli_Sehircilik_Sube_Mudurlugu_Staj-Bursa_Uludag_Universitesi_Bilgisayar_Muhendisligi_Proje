from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    general_exception_handler,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware Yapılandırması
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"]
    )

# Özel Hata Yakalayıcılar (Exception Handlers)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# API v1 Router Entegrasyonu
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Sistem"])
async def health_check():
    """
    Sistem sağlık ve çalışma durumu kontrolü.
    """
    return {
        "status": "ok",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION
    }