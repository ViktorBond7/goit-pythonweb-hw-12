from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
USER_CACHE_TTL = 900  # 15 minutes in seconds

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    ]

class Settings(BaseSettings):
    DATABASE_CONNECT_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Contact Book"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str
    CLD_API_KEY: int 
    CLD_API_SECRET: str

    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


