from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-me-in-production", validation_alias="ADMIN_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="ADMIN_JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24, validation_alias="ADMIN_JWT_EXPIRE_MINUTES")
    admin_username: str = Field(default="admin", validation_alias="ADMIN_USERNAME")
    admin_password: str = Field(default="", validation_alias="ADMIN_PASSWORD")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
