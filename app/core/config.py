import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import ClassVar

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # ✅ These are now ClassVar so Pydantic does not treat them as fields
    UPLOAD_USER_DIR: ClassVar[str] = os.getenv(
        "UPLOAD_USER_DIR",
        "app/upload/users/",
    )
    UPLOAD_PROVIDER_DIR: ClassVar[str] = os.getenv(
        "UPLOAD_PROVIDER_DIR",
        "app/upload/providers/",
    )
    UPLOAD_STAYS_DIR: ClassVar[str] = os.getenv(
        "UPLOAD_STAYS_DIR",
        "app/upload/stays/",
    )

    class Config:
        case_sensitive = True


settings = Settings()
