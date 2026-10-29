from app.services.base import BaseService
from app.services.villa_service import VillaService
from app.services.resident_service import ResidentService
from app.services.maintenance_service import MaintenanceService
from app.services.finance_service import FinanceService
from app.services.report_service import ReportService

# Singleton service instances for convenient dependency injection
villa_service = VillaService()
resident_service = ResidentService()
maintenance_service = MaintenanceService()
finance_service = FinanceService()
report_service = ReportService()

__all__ = [
    "BaseService",
    "VillaService",
    "ResidentService",
    "MaintenanceService",
    "FinanceService",
    "ReportService",
    "villa_service",
    "resident_service",
    "maintenance_service",
    "finance_service",
    "report_service",
]
