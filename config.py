import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def normalize_database_url(database_url: str | None) -> str | None:
    if database_url and database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url and database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    ENVIRONMENT = "development"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    COMMUNITY_NAME = os.environ.get("COMMUNITY_NAME", "Emerald Palms Luxury Community")
    COMMUNITY_TAGLINE = "Exclusive Private Villa Living & Community Services"
    CURRENCY_SYMBOL = "₹"
    BASE_FEE_RATE_PER_SQFT = float(os.environ.get("MONTHLY_BASE_FEE_RATE_PER_SQFT", 0.15))
    ITEMS_PER_PAGE = 12

class DevelopmentConfig(Config):
    """Development configuration with SQLite file database."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{BASE_DIR / 'instance' / 'villaverse.db'}"
    )

class TestingConfig(Config):
    """Testing configuration with in-memory SQLite database."""
    ENVIRONMENT = "testing"
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

class ProductionConfig(Config):
    """Production configuration."""
    ENVIRONMENT = "production"
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.environ.get("DATABASE_URL"))

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
