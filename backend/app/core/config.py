import os
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==============================================================================
# VERÄ°TABANI BAÄLANTI AYARLARI
# ==============================================================================
# BaÅŸka bir veritabanÄ±na baÄŸlanmak iÃ§in aÅŸaÄŸÄ±daki deÄŸerleri deÄŸiÅŸtirmeniz yeterlidir.
# Ã–NEMLÄ°: EÄŸer projenin ana dizininde bir ".env" dosyasÄ± oluÅŸturursanÄ±z, 
# oradaki deÄŸerler buradaki varsayÄ±lan deÄŸerleri ezecektir. (Ã–nerilen yÃ¶ntem)

DB_SERVER = "localhost"       # VeritabanÄ± sunucu adresi (Ã¶rn: localhost, 192.168.1.50)
DB_PORT = 5432                # VeritabanÄ± port numarasÄ± (PostgreSQL varsayÄ±lan: 5432)
DB_USER = "postgres"          # VeritabanÄ± kullanÄ±cÄ± adÄ±
DB_PASSWORD = "postgres"      # VeritabanÄ± ÅŸifresi
DB_NAME = "postgres"          # BaÄŸlanÄ±lacak veritabanÄ±nÄ±n adÄ±
# ==============================================================================


class Settings(BaseSettings):
    """
    Uygulama genelindeki tÃ¼m yapÄ±landÄ±rma (config) ayarlarÄ±nÄ±n tutulduÄŸu sÄ±nÄ±f.
    Pydantic BaseSettings kullanÄ±ldÄ±ÄŸÄ± iÃ§in ortam deÄŸiÅŸkenlerinden (Environment Variables)
    veya .env dosyasÄ±ndan otomatik olarak deÄŸerleri okuyabilir.
    """
    PROJECT_NAME: str = "Bursa BÃ¼yÃ¼kÅŸehir Belediyesi Faaliyet Raporu Sistemi"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # GÃ¼venlik ve Kimlik DoÄŸrulama (JWT)
    # Token ÅŸifrelemesi iÃ§in kullanÄ±lan gizli anahtar. CanlÄ± ortamda rastgele ve gÃ¼venli bir string olmalÄ±dÄ±r.
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1  # Token geÃ§erlilik sÃ¼resi (Ã–rn: 1 gÃ¼n)

    # CORS (Cross-Origin Resource Sharing) AyarlarÄ±
    # Frontend'in Backend'e API istekleri atabilmesi iÃ§in izin verilen URL adresleri.
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # VeritabanÄ± AyarlarÄ± (DeÄŸerler sayfanÄ±n en Ã¼stÃ¼ndeki sabitlerden gelir)
    POSTGRES_SERVER: str = DB_SERVER
    POSTGRES_PORT: int = DB_PORT
    POSTGRES_USER: str = DB_USER
    POSTGRES_PASSWORD: str = DB_PASSWORD
    POSTGRES_DB: str = DB_NAME
    ASYNC_SQLALCHEMY_DATABASE_URI: Union[Optional[str], PostgresDsn] = None

    @field_validator("ASYNC_SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """
        YukarÄ±daki DB bilgilerini kullanarak asenkron (asyncpg) PostgreSQL baÄŸlantÄ± cÃ¼mlesini oluÅŸturur.
        """
        if isinstance(v, str) and v:
            return v
        
        user = values.data.get("POSTGRES_USER")
        password = values.data.get("POSTGRES_PASSWORD")
        server = values.data.get("POSTGRES_SERVER")
        port = values.data.get("POSTGRES_PORT")
        db = values.data.get("POSTGRES_DB")
        
        return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"

    # Dosya Depolama (YÃ¼klenen rapor vb. belgelerin diske kaydedileceÄŸi klasÃ¶r)
    STORAGE_DIR: str = "storage/reports"

    # Ä°lk SÃ¼per KullanÄ±cÄ± (Sistem ilk kurulduÄŸunda oluÅŸturulacak varsayÄ±lan admin hesabÄ±)
    FIRST_SUPERUSER_EMAIL: str = "admin@bursa.bel.tr"
    FIRST_SUPERUSER_PASSWORD: str = "admin123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Sistemin diÄŸer kÄ±sÄ±mlarÄ±ndan eriÅŸilecek olan config objesi (singleton)
settings = Settings()