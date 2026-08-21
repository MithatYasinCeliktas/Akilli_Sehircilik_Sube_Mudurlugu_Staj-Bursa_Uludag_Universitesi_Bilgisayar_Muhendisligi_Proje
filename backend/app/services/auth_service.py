from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import UnauthorizedException, NotFoundException, BadRequestException
from app.services.log_service import LogService

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, login_data: UserLogin) -> Token:
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            raise UnauthorizedException(detail="Geçersiz e-posta adresi veya şifre.")

        if not user.is_active:
            raise UnauthorizedException(detail="Kullanıcı hesabı pasif durumdadır.")

        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException(detail="Geçersiz e-posta adresi veya şifre.")

        import uuid
        jti = str(uuid.uuid4())
        user.active_token_jti = jti
        await self.db.commit()
        await self.db.refresh(user)

        access_token = create_access_token(subject=user.id, jti=jti)

        await LogService.create_log(
            db=self.db,
            action="LOGIN",
            user_id=user.id,
            entity_type="USER",
            entity_id=user.id,
            details={"message": f"{user.email} sisteme giriş yaptı."}
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    async def register_user(self, user_in: UserCreate) -> UserResponse:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise BadRequestException(detail="Bu e-posta adresi ile kayıtlı bir kullanıcı zaten mevcut.")

        user_data = user_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = get_password_hash(user_in.password)
        user_data["is_active"] = True
        
        new_user = await self.user_repo.create(user_data)
        
        await LogService.create_log(
            db=self.db,
            action="CREATE",
            user_id=new_user.id,
            entity_type="USER",
            entity_id=new_user.id,
            details={"message": f"Yeni kullanıcı kaydı oluşturuldu: {new_user.email}"}
        )
        
        return UserResponse.model_validate(new_user)