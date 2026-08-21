from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from app.core.response import error_response


class AppException(Exception):
    """
    Sistem genelinde özel iş mantığı hataları için kullanılacak temel exception sınıfı.
    """
    def __init__(
        self,
        message: str = "Bir uygulama hatası oluştu.",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Optional[Any] = None,
        detail: Optional[str] = None
    ):
        # 'detail' parametresini 'message' olarak da kabul et (geriye dönük uyumluluk)
        self.message = detail if detail is not None else message
        self.status_code = status_code
        self.errors = errors
        super().__init__(self.message)


class NotFoundException(AppException):
    """
    Aranan kaynak bulunamadığında fırlatılır (HTTP 404).
    """
    def __init__(self, message: str = "İstenen kaynak bulunamadı.", errors: Optional[Any] = None, detail: Optional[str] = None):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND, errors=errors, detail=detail)


class UnauthorizedException(AppException):
    """
    Kimlik doğrulama başarısız olduğunda fırlatılır (HTTP 401).
    """
    def __init__(self, message: str = "Kimlik doğrulaması başarısız.", errors: Optional[Any] = None, detail: Optional[str] = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, errors=errors, detail=detail)


class ForbiddenException(AppException):
    """
    Kullanıcının bu işlemi yapmaya yetkisi olmadığında fırlatılır (HTTP 403).
    """
    def __init__(self, message: str = "Bu işlem için yetkiniz bulunmamaktadır.", errors: Optional[Any] = None, detail: Optional[str] = None):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN, errors=errors, detail=detail)


class BadRequestException(AppException):
    """
    Geçersiz istek veya iş kuralı ihlalinde fırlatılır (HTTP 400).
    """
    def __init__(self, message: str = "Geçersiz istek.", errors: Optional[Any] = None, detail: Optional[str] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, errors=errors, detail=detail)


class ValidationException(AppException):
    """
    İş kuralları veya veri doğrulama hatalarında fırlatılır (HTTP 422).
    """
    def __init__(self, message: str = "Geçersiz veri girişi.", errors: Optional[Any] = None, detail: Optional[str] = None):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, errors=errors, detail=detail)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    AppException ve alt sınıfları için global hata işleyici.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=exc.message, errors=exc.errors)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Yakalanmamış tüm Exception'lar için fallback hata işleyici.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="Sunucu tarafında beklenmeyen bir hata oluştu.",
            errors={"detail": str(exc)}
        )
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    FastAPI uygulamasına global exception handler'ları kaydeder.
    Tüm hataları standart zarf yanıtı (APIResponse / error_response) formatında döndürür.
    """

    @app.exception_handler(AppException)
    async def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return await app_exception_handler(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message=str(exc.detail), errors=None)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        formatted_errors = []
        for err in exc.errors():
            field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
            formatted_errors.append({
                "field": field,
                "message": err.get("msg", "Geçersiz değer"),
                "type": err.get("type", "validation_error")
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(
                message="Gönderilen parametreler doğrulanamadı.",
                errors=formatted_errors
            )
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return await general_exception_handler(request, exc)