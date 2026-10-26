from __future__ import annotations

from functools import lru_cache
from typing import Annotated, List, Literal
from decimal import Decimal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "TransivoX"
    APP_VERSION: str = "1.0.0"
    BUILD_SHA: str = "unknown"
    VERCEL_GIT_COMMIT_SHA: str = ""
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: Annotated[List[str], NoDecode] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg://trucksetu:password@localhost:5432/trucksetu_db"
    MIGRATION_DATABASE_URL: str = ""
    DB_POOL_SIZE: int = 2
    DB_MAX_OVERFLOW: int = 1
    DB_POOL_TIMEOUT_SECONDS: int = 10
    DB_POOL_RECYCLE_SECONDS: int = 300
    DB_CONNECT_TIMEOUT_SECONDS: int = 10
    DB_STATEMENT_TIMEOUT_MS: int = 15000
    DB_IDLE_TRANSACTION_TIMEOUT_MS: int = 15000

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_REQUIRED: bool = False

    # ── JWT ──────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    AUTH_COOKIE_SAMESITE: Literal['none','lax','strict'] = 'none'
    JWT_ISSUER: str = "transivox-api"
    JWT_AUDIENCE: str = "transivox-web"

    # ── Google OAuth ──────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # ── AWS S3 ────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "ap-south-1"
    KYC_SCAN_PROVIDER: Literal['guardduty', 'clamav', 'disabled', 'test'] = 'guardduty'
    KYC_SCAN_RESULTS_BUCKET: str = ""
    KYC_SCAN_MAX_DEFINITION_AGE_HOURS: int = 48
    CUSTOMER_KYC_REQUIRED_DOCUMENTS: str = ""
    CUSTOMER_KYC_POLICY_VERSION: str = ""
    CUSTOMER_KYC_CONSENT_TEXT: str = ""
    CUSTOMER_KYC_TEST_SIMULATION: bool = False

    # ── Razorpay ──────────────────────────────────────────
    ENABLE_RAZORPAY_SANDBOX: bool = False
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── MSG91 ─────────────────────────────────────────────
    MSG91_AUTH_KEY: str = ""
    MSG91_WIDGET_ENABLED: bool = False
    MSG91_TEMPLATE_ID: str = ""
    MSG91_OTP_VARIABLE: str = "OTP"

    # ── WATI WhatsApp ─────────────────────────────────────
    WATI_API_KEY: str = ""
    WATI_BASE_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_REPLY_TO: str = ""
    PUBLIC_FRONTEND_URL: str = ""
    ACCOUNT_EMAIL_COOLDOWN_SECONDS: int = 60

    @field_validator('PUBLIC_FRONTEND_URL')
    @classmethod
    def validate_public_frontend_url(cls, value: str) -> str:
        from urllib.parse import urlsplit
        if not value:
            return value
        parsed = urlsplit(value)
        local = parsed.hostname in {'localhost', '127.0.0.1', '::1'}
        if (parsed.scheme not in {'http', 'https'} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {'', '/'} or (parsed.scheme != 'https' and not local)):
            raise ValueError('PUBLIC_FRONTEND_URL must be an HTTPS origin (HTTP loopback is allowed locally)')
        return value.rstrip('/')

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
    MAX_REQUEST_BODY_BYTES: int = 2_000_000
    LOGIN_RATE_LIMIT: int = 10
    SIGNUP_RATE_LIMIT: int = 5
    VERIFICATION_RATE_LIMIT: int = 10
    REFRESH_RATE_LIMIT: int = 30
    OTP_RATE_LIMIT: int = 5
    PRICING_RATE_LIMIT: int = 20
    AI_RATE_LIMIT: int = 20
    SCHEDULE_MIN_LEAD_MINUTES: int = 30
    NOW_PICKUP_LEAD_MINUTES: int = 15
    NOW_PICKUP_WINDOW_MINUTES: int = 90
    NOW_DELIVERY_WINDOW_HOURS: int = 24
    TRUSTED_HOSTS: Annotated[List[str], NoDecode] = ["localhost", "127.0.0.1"]

    # ── Controlled pilot feature flags ────────────────────
    # New commercial policies have no implicit production defaults.
    ENABLE_CUSTOMER_DEMAND_MARKETPLACE: bool = True
    ENABLE_LEGACY_PROVIDER_MARKETPLACE: bool = False
    ENABLE_PROVIDER_FIRST_PUBLICATION: bool = False
    DEMAND_MARKETPLACE_POLICY: str = ""
    CONNECTION_FEE_POLICY: str = ""
    ENABLE_REAL_CONNECTION_CHECKOUT: bool = False
    ENABLE_TRANSPORT_PAYMENT_COLLECTION: bool = False
    CONNECTION_FEE_AMOUNT: Decimal = Decimal("1000.00")
    CONNECTION_FEE_TAX_RATE: Decimal = Decimal('0.20')
    CONNECTION_FEE_TAX_CONFIRMED: bool = False
    # Retained for compatibility with old local settings; checkout ignores it.
    CONNECTION_FEE_WAIVER_TEST_TAX_AMOUNT: Decimal | None = None
    CONNECTION_FEE_CURRENCY: str = "INR"
    ENABLE_SHARED_CAPACITY: bool = True
    ENABLE_IMMEDIATE_BOOKING: bool = True
    ENABLE_LIVE_GPS: bool = False
    ENABLE_AUTOMATED_PAYOUTS: bool = False
    ENABLE_AUTOMATED_KYC: bool = False
    ENABLE_INTERSTATE: bool = False
    ENABLE_PROMOTIONS: bool = False
    ENABLE_HAZARDOUS_CARGO: bool = False
    PILOT_ORIGIN_CITIES: Annotated[List[str], NoDecode] = ["Delhi"]
    PILOT_DESTINATION_CITIES: Annotated[List[str], NoDecode] = ["Delhi", "Gurugram", "Noida"]

    # ── Celery ────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Sentry ────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── One-time admin bootstrap ──────────────────────────
    # Configure temporarily, create the first admin, then remove and redeploy.
    ADMIN_BOOTSTRAP_TOKEN: str = ""

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("DATABASE_URL", "MIGRATION_DATABASE_URL", mode="before")
    @classmethod
    def use_psycopg3_sqlalchemy_driver(cls, value: str) -> str:
        if value and value.startswith(("postgresql://", "postgres://")):
            return value.replace(value.split("://", 1)[0] + "://", "postgresql+psycopg://", 1)
        return value

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_hosts(cls, v: str | List[str]) -> List[str]:
        return [item.strip() for item in v.split(",")] if isinstance(v, str) else v

    @field_validator("PILOT_ORIGIN_CITIES", "PILOT_DESTINATION_CITIES", mode="before")
    @classmethod
    def parse_pilot_cities(cls, v: str | List[str]) -> List[str]:
        return [item.strip() for item in v.split(",") if item.strip()] if isinstance(v, str) else v

    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("DB_POOL_SIZE must be between 1 and 5 for serverless deployment")
        return value

    @field_validator("DB_MAX_OVERFLOW")
    @classmethod
    def validate_pool_overflow(cls, value: int) -> int:
        if not 0 <= value <= 3:
            raise ValueError("DB_MAX_OVERFLOW must be between 0 and 3 for serverless deployment")
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        weak_markers = {"dev-secret-key-change-in-production", "replace-with-a-long-random-secret", "changeme"}
        if self.APP_ENV == "production" and (len(self.SECRET_KEY) < 64 or self.SECRET_KEY.lower() in weak_markers):
            raise ValueError("SECRET_KEY must contain at least 64 unpredictable characters in production")
        if self.APP_ENV == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        if self.APP_ENV == "production":
            if self.PUBLIC_FRONTEND_URL and not self.PUBLIC_FRONTEND_URL.startswith("https://"):
                raise ValueError("Production PUBLIC_FRONTEND_URL must use HTTPS")
            if not self.ALLOWED_ORIGINS or any(origin == "*" or not origin.startswith("https://") for origin in self.ALLOWED_ORIGINS):
                raise ValueError("Production ALLOWED_ORIGINS must contain explicit HTTPS origins")
            if not self.TRUSTED_HOSTS or "*" in self.TRUSTED_HOSTS:
                raise ValueError("Production TRUSTED_HOSTS must not allow every host")
        if self.ALGORITHM != "HS256":
            raise ValueError("Only the reviewed HS256 JWT algorithm is supported")
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def admin_bootstrap_enabled(self) -> bool:
        return len(self.ADMIN_BOOTSTRAP_TOKEN) >= 32

    @property
    def migration_database_url(self) -> str:
        return self.MIGRATION_DATABASE_URL or self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
