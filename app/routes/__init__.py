from app.routes.dashboard import dashboard_bp
from app.routes.villas import villas_bp
from app.routes.residents import residents_bp
from app.routes.maintenance import maintenance_bp
from app.routes.finance import finance_bp
from app.routes.reports import reports_bp

__all__ = [
    "dashboard_bp",
    "villas_bp",
    "residents_bp",
    "maintenance_bp",
    "finance_bp",
    "reports_bp",
]
