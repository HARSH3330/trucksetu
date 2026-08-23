from __future__ import annotations

from functools import lru_cache
from typing import List
from decimal import Decimal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "TruckSetu"
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg://trucksetu:password@localhost:5432/trucksetu_db"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Google OAuth ──────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── AWS S3 ────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"

    # ── Razorpay ──────────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # ── MSG91 ─────────────────────────────────────────────
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""

    # ── WATI WhatsApp ─────────────────────────────────────
    WATI_API_KEY: str = ""
    WATI_BASE_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    # ── AI ────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GOOGLE_MAPS_API_KEY: str = ""

    # ── Business Rules ────────────────────────────────────
    # Development fallback only. Production values are stored in application_settings.
    PLATFORM_COMMISSION_PERCENT: Decimal = Decimal("8.00")
    DEFAULT_ADVANCE_PERCENT: Decimal = Decimal("20.00")
    DEFAULT_GST_PERCENT: Decimal = Decimal("18.00")
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    RATE_LIMIT_PER_MINUTE: int = 120
    TRUSTED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # ── Controlled pilot feature flags ────────────────────
    ENABLE_SHARED_CAPACITY: bool = True
    ENABLE_IMMEDIATE_BOOKING: bool = True
    ENABLE_LIVE_GPS: bool = False
    ENABLE_AUTOMATED_PAYOUTS: bool = False
    ENABLE_AUTOMATED_KYC: bool = False
    ENABLE_INTERSTATE: bool = False
    ENABLE_PROMOTIONS: bool = False
    ENABLE_HAZARDOUS_CARGO: bool = False
    PILOT_ORIGIN_CITIES: List[str] = ["Delhi"]
    PILOT_DESTINATION_CITIES: List[str] = ["Delhi", "Gurugram", "Noida"]

    # ── Celery ────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Sentry ────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── Seed Admin ────────────────────────────────────────
    FIRST_SUPERADMIN_EMAIL: str = "admin@trucksetu.in"
    FIRST_SUPERADMIN_PASSWORD: str = "Admin@123"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_hosts(cls, v: str | List[str]) -> List[str]:
        return [item.strip() for item in v.split(",")] if isinstance(v, str) else v

    @field_validator("PILOT_ORIGIN_CITIES", "PILOT_DESTINATION_CITIES", mode="before")
    @classmethod
    def parse_pilot_cities(cls, v: str | List[str]) -> List[str]:
        return [item.strip() for item in v.split(",") if item.strip()] if isinstance(v, str) else v

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.APP_ENV == "production" and self.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be replaced in production")
        if self.APP_ENV == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
