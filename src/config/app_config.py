from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
USER_CACHE_TTL = 900  # 15 minutes in seconds
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = 30

origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    ]

class Settings(BaseSettings):
    DATABASE_CONNECT_URL: str = "postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "contact_book"

    MAIL_USERNAME: EmailStr = "your_email@example.com"
    MAIL_PASSWORD: str = "your_email_password"
    MAIL_FROM: EmailStr = "your_email@example.com"
    MAIL_PORT: int = 587 
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Contact Book"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str = "your_cloudinary_name"
    CLD_API_KEY: int = 1234567890
    CLD_API_SECRET: str = "your_cloudinary_api_secret"

    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


