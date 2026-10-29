import os
from datetime import datetime, timezone
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, csrf
from app.exceptions import VillaVerseError

def create_app(config_name: str | None = None) -> Flask:
    """
    Application factory for VillaVerse.
    Initializes Flask, binds database and CSRF extensions, registers blueprints,
    and sets up custom template filters and context processors.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.routes import (
        dashboard_bp,
        villas_bp,
        residents_bp,
        maintenance_bp,
        finance_bp,
        reports_bp
    )
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(villas_bp)
    app.register_blueprint(residents_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(reports_bp)

    # Template filters and context processors
    @app.template_filter("currency")
    def currency_filter(value):
        """Formats a float as currency e.g. $1,250.00"""
        symbol = app.config.get("CURRENCY_SYMBOL", "$")
        try:
            return f"{symbol}{float(value):,.2f}"
        except (ValueError, TypeError):
            return f"{symbol}0.00"

    @app.context_processor
    def inject_global_template_vars():
        return {
            "community_name": app.config.get("COMMUNITY_NAME", "Emerald Palms Luxury Community"),
            "community_tagline": app.config.get("COMMUNITY_TAGLINE", "Exclusive Private Villa Living"),
            "currency_symbol": app.config.get("CURRENCY_SYMBOL", "$"),
            "current_year": datetime.now(timezone.utc).year
        }

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html", message="The requested page or record could not be found."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html", message="An unexpected server error occurred."), 500

    @app.errorhandler(VillaVerseError)
    def handle_domain_error(error):
        return render_template("errors/domain_error.html", error=error), error.status_code

    # CLI Commands
    @app.cli.command("seed-db")
    def seed_db_command():
        """Command to populate database with 100+ fictional sample records."""
        from seed import seed_database
        seed_database()
        print("Community database successfully populated with realistic demonstration data!")

    return app
