from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_async_db
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User
from app.repositories.user_repository import UserRepository

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI endpoint'leri için asenkron veritabanı oturumu (AsyncSession) sağlayıcısı.
    """
    async for session in get_async_db():
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    JWT Access Token'ı doğrulayarak oturum açmış aktif kullanıcıyı getirir.
    Token süresi dolmuşsa veya kullanıcı bulunamazsa yetkisizlik hatası döndürür.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_jti = payload.get("jti")
        if user_id_str is None:
            raise UnauthorizedException(detail="Geçersiz kimlik doğrulama bilgisi.")
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedException(detail="Geçersiz veya süresi dolmuş oturum jetonu.")

    user_repo = UserRepository(db)
    user = await user_repo.get_with_relations(user_id)
    if not user:
        raise UnauthorizedException(detail="Kullanıcı hesabı bulunamadı.")

    if not user.is_active:
        raise UnauthorizedException(detail="Kullanıcı hesabı pasif durumdadır.")

    if token_jti and user.active_token_jti and token_jti != user.active_token_jti:
        raise UnauthorizedException(detail="Oturumunuz başka bir cihazdan giriş yapıldığı için sonlandırıldı.")

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Yalnızca sistem yöneticisi (is_superuser=True) yetkisine sahip aktif kullanıcıların
    ilgili endpoint'e erişmesine izin verir.
    """
    if not current_user.is_superuser:
        raise ForbiddenException(detail="Bu işlem için sistem yöneticisi yetkisi gereklidir.")
    return current_user