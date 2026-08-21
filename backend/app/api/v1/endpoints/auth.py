from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.response import DataResponse
from app.models.user import User
from app.schemas.user import UserLogin, Token, UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.log_service import LogService

router = APIRouter()


@router.post(
    "/login",
    response_model=DataResponse[Token],
    summary="Kullanıcı Girişi ve JWT Token Üretimi",
    description="E-posta ve şifre ile kimlik doğrular, başarılı girişte Bearer Access Token döndürür."
)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(deps.get_db)
):
    auth_service = AuthService(db)
    token_data = await auth_service.authenticate_user(login_data)
    return DataResponse(
        data=token_data,
        message="Giriş başarılı."
    )


@router.post(
    "/login/access-token",
    response_model=Token,
    summary="OAuth2 Uyumlu Form Girişi",
    description="Swagger UI / OAuth2 standart form yapısına uygun token alma endpoint'i."
)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db)
):
    auth_service = AuthService(db)
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    token_data = await auth_service.authenticate_user(login_data)
    return token_data


@router.post(
    "/register",
    response_model=DataResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Yeni Kullanıcı Kaydı",
    description="Sisteme yeni kullanıcı kaydı gerçekleştirir."
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    auth_service = AuthService(db)
    user_response = await auth_service.register_user(user_in)
    return DataResponse(
        data=user_response,
        message="Kullanıcı kaydı başarıyla oluşturuldu."
    )


@router.get(
    "/me",
    response_model=DataResponse[UserResponse],
    summary="Mevcut Kullanıcı Profil Detayları",
    description="Oturum açmış olan kullanıcının detaylı profil bilgilerini döndürür."
)
async def read_current_user_me(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    auth_service = AuthService(db)
    user_response = await auth_service.get_current_user_profile(current_user.id)
    return DataResponse(
        data=user_response,
        message="Profil bilgileri başarıyla getirildi."
    )

@router.post(
    "/logout",
    response_model=DataResponse[bool],
    summary="Kullanıcı Çıkışı",
    description="Oturum açmış olan kullanıcının tokenını geçersiz kılar ve çıkış işlemini loglar."
)
async def logout(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    # active_token_jti null yapılarak mevcut token iptal ediliyor
    current_user.active_token_jti = None
    
    await LogService.create_log(
        db=db,
        action="LOGOUT",
        user_id=current_user.id,
        entity_type="USER",
        entity_id=current_user.id,
        details={"email": current_user.email}
    )
    
    await db.commit()
    
    return DataResponse(
        data=True,
        message="Çıkış başarılı."
    )