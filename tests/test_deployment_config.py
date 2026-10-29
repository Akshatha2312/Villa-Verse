import pytest

from app import create_app
from app.extensions import db
from config import ProductionConfig, normalize_database_url
from sqlalchemy import inspect


def test_normalize_render_postgresql_urls_for_psycopg():
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+psycopg://user:pass@host/db"
    )
    assert normalize_database_url("sqlite:///local.db") == "sqlite:///local.db"


def test_production_app_requires_secure_secret_and_postgresql(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "s" * 64)
    monkeypatch.setattr(db, "create_all", lambda: None)
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+psycopg://user:pass@localhost/villaverse",
    )

    app = create_app("production")

    assert app.config["DEBUG"] is False
    assert app.config["ENVIRONMENT"] == "production"


def test_init_db_cli_creates_missing_tables():
    app = create_app("testing")

    result = app.test_cli_runner().invoke(args=["init-db"])

    assert result.exit_code == 0
    assert "Existing tables were not migrated." in result.output


def test_app_factory_initializes_models_and_dashboard():
    app = create_app("testing")

    with app.app_context():
        tables = set(inspect(db.engine).get_table_names())

    assert {
        "villas",
        "community_members",
        "villa_occupancies",
        "maintenance_requests",
        "fee_charges",
        "payment_records",
        "expense_records",
    } <= tables

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Operations overview" in response.data


def test_render_defaults_to_production_configuration(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("FLASK_ENV", raising=False)
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "s" * 64)
    monkeypatch.setattr(db, "create_all", lambda: None)
    monkeypatch.setattr(
        ProductionConfig,
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+psycopg://user:password@localhost/villaverse",
    )

    app = create_app()

    assert app.config["ENVIRONMENT"] == "production"
    assert app.config["DEBUG"] is False
    assert app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg://")


@pytest.mark.parametrize(
    ("secret_key", "database_url", "error"),
    [
        (None, "postgresql+psycopg://user:pass@localhost/villaverse", "SECRET_KEY"),
        ("s" * 64, None, "DATABASE_URL"),
        (
            "replace-with-a-random-secret-at-least-32-characters",
            "postgresql+psycopg://user:pass@localhost/villaverse",
            "SECRET_KEY",
        ),
        ("s" * 64, "sqlite:///local.db", "DATABASE_URL"),
    ],
)
def test_production_app_rejects_unsafe_configuration(
    monkeypatch, secret_key, database_url, error
):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", secret_key)
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", database_url)

    with pytest.raises(RuntimeError, match=error):
        create_app("production")
