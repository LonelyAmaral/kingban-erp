"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (SQLite para dev local, PostgreSQL para Docker/prod)
    DATABASE_URL: str = "sqlite+aiosqlite:///./kingban_dev.db"
    DATABASE_URL_SYNC: str = "sqlite:///./kingban_dev.db"

    # Auth
    SECRET_KEY: str = "kingban"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    ALGORITHM: str = "HS256"

    # App
    APP_NAME: str = "KING BAN ERP"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
