from flask import Blueprint, render_template, Response
from app.services import report_service

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/")
def index():
    """Reports overview dashboard with analytics, graphs, and export actions."""
    data = report_service.get_dashboard_data()
    return render_template("reports/index.html", data=data)

@reports_bp.route("/export/villas.csv")
def export_villas():
    """Export complete villa registry as CSV file."""
    csv_data = report_service.export_villas_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=villaverse_villas.csv"}
    )

@reports_bp.route("/export/maintenance.csv")
def export_maintenance():
    """Export complete maintenance history as CSV file."""
    csv_data = report_service.export_maintenance_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=villaverse_maintenance.csv"}
    )

@reports_bp.route("/export/finance.csv")
def export_finance():
    """Export community fee billing and collection ledger as CSV file."""
    csv_data = report_service.export_finance_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=villaverse_financial_ledger.csv"}
    )
