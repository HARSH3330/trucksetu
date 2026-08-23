from app.core.config import Settings


def test_neon_urls_are_normalized_for_psycopg3() -> None:
    settings = Settings(
        DATABASE_URL="postgresql://user:secret@ep-test-pooler.neon.tech/neondb?sslmode=require",
        MIGRATION_DATABASE_URL="postgresql://user:secret@ep-test.neon.tech/neondb?sslmode=require",
    )
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")
    assert settings.migration_database_url.startswith("postgresql+psycopg://")
    assert "-pooler" not in settings.migration_database_url


def test_migrations_fall_back_to_runtime_url_for_local_development() -> None:
    settings = Settings(DATABASE_URL="postgresql://user:secret@localhost/trucksetu", MIGRATION_DATABASE_URL="")
    assert settings.migration_database_url == settings.DATABASE_URL
