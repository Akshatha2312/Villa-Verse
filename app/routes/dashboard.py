from flask import Blueprint, render_template, jsonify
from app.services import report_service, villa_service, maintenance_service, finance_service

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def index():
    """Render executive management dashboard with live metrics."""
    data = report_service.get_dashboard_data()
    return render_template("dashboard/index.html", data=data)

@dashboard_bp.route("/api/chart-data")
def chart_data():
    """API endpoint providing real-time data for Chart.js dashboards."""
    charts = report_service.get_chart_data()
    return jsonify(charts)
