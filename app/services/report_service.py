import csv
import io
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import func
from app.extensions import db
from app.models.villa import Villa
from app.models.member import CommunityMember
from app.models.maintenance import MaintenanceRequest
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord

class ReportService:
    """
    Service responsible for analytical queries, dashboard chart aggregation,
    and CSV report exports.
    Demonstrates OOP Separation of Concerns (Business Analytics).
    """

    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """Calculates live aggregated metrics for the executive overview."""
        # 1. Villa metrics
        total_villas = Villa.query.count()
        occupied_villas = Villa.query.filter_by(status=Villa.STATUS_OCCUPIED).count()
        available_villas = Villa.query.filter_by(status=Villa.STATUS_AVAILABLE).count()
        construction_villas = Villa.query.filter_by(status=Villa.STATUS_UNDER_CONSTRUCTION).count()
        occupancy_rate = round((occupied_villas / total_villas * 100), 1) if total_villas > 0 else 0.0

        # 2. Maintenance metrics
        active_maintenance = MaintenanceRequest.query.filter(
            MaintenanceRequest.status.in_([MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS])
        ).count()
        urgent_maintenance = MaintenanceRequest.query.filter(
            MaintenanceRequest.status.in_([MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS]),
            MaintenanceRequest.priority == MaintenanceRequest.PRIORITY_URGENT
        ).count()

        # 3. Financial metrics
        total_invoiced = db.session.query(func.sum(FeeCharge.amount)).scalar() or 0.0
        total_collected = db.session.query(func.sum(PaymentRecord.amount)).scalar() or 0.0
        total_expenses = db.session.query(func.sum(ExpenseRecord.amount)).scalar() or 0.0
        outstanding_balance = max(0.0, total_invoiced - total_collected)
        collection_rate = round((total_collected / total_invoiced * 100), 1) if total_invoiced > 0 else 0.0

        # 4. Recent activity / urgent tickets
        recent_tickets = MaintenanceRequest.query.order_by(MaintenanceRequest.reported_date.desc()).limit(5).all()
        urgent_tickets = MaintenanceRequest.query.filter(
            MaintenanceRequest.status.in_([MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS]),
            MaintenanceRequest.priority.in_([MaintenanceRequest.PRIORITY_URGENT, MaintenanceRequest.PRIORITY_HIGH])
        ).order_by(MaintenanceRequest.reported_date.desc()).limit(5).all()

        recent_payments = PaymentRecord.query.order_by(PaymentRecord.payment_date.desc()).limit(5).all()

        return {
            "villas": {
                "total": total_villas,
                "occupied": occupied_villas,
                "available": available_villas,
                "under_construction": construction_villas,
                "occupancy_rate": occupancy_rate
            },
            "maintenance": {
                "active": active_maintenance,
                "urgent": urgent_maintenance
            },
            "finance": {
                "invoiced": round(total_invoiced, 2),
                "collected": round(total_collected, 2),
                "expenses": round(total_expenses, 2),
                "outstanding": round(outstanding_balance, 2),
                "collection_rate": collection_rate,
                "net_surplus": round(total_collected - total_expenses, 2)
            },
            "recent_tickets": recent_tickets,
            "urgent_tickets": urgent_tickets,
            "recent_payments": recent_payments
        }

    @staticmethod
    def get_chart_data() -> Dict[str, Any]:
        """Provides structured datasets for Chart.js interactive charts."""
        # Occupancy chart
        occupied = Villa.query.filter_by(status=Villa.STATUS_OCCUPIED).count()
        available = Villa.query.filter_by(status=Villa.STATUS_AVAILABLE).count()
        under_construction = Villa.query.filter_by(status=Villa.STATUS_UNDER_CONSTRUCTION).count()

        occupancy_chart = {
            "labels": ["Occupied", "Available", "Under Construction"],
            "data": [occupied, available, under_construction]
        }

        # Maintenance by category
        cat_counts = (
            db.session.query(MaintenanceRequest.category, func.count(MaintenanceRequest.id))
            .group_by(MaintenanceRequest.category)
            .order_by(func.count(MaintenanceRequest.id).desc())
            .all()
        )
        maintenance_category_chart = {
            "labels": [c[0] for c in cat_counts],
            "data": [c[1] for c in cat_counts]
        }

        # Monthly collections vs expenses
        # Invoiced by period_month
        fee_periods = (
            db.session.query(FeeCharge.period_month, func.sum(FeeCharge.amount))
            .group_by(FeeCharge.period_month)
            .order_by(FeeCharge.period_month.asc())
            .limit(6)
            .all()
        )
        period_months = [p[0] for p in fee_periods]
        invoiced_data = [float(p[1]) for p in fee_periods]

        # Collections per period_month (via associated charge period)
        collected_map = {}
        for pm in period_months:
            col = (
                db.session.query(func.sum(PaymentRecord.amount))
                .join(FeeCharge)
                .filter(FeeCharge.period_month == pm)
                .scalar() or 0.0
            )
            collected_map[pm] = float(col)
        collected_data = [collected_map.get(pm, 0.0) for pm in period_months]

        # Expense by month
        expense_map = {}
        expenses_raw = (
            db.session.query(
                func.strftime("%Y-%m", ExpenseRecord.expense_date),
                func.sum(ExpenseRecord.amount)
            )
            .group_by(func.strftime("%Y-%m", ExpenseRecord.expense_date))
            .all()
        )
        for row in expenses_raw:
            if row[0]:
                expense_map[row[0]] = float(row[1])
        expense_data = [expense_map.get(pm, 0.0) for pm in period_months]

        cashflow_chart = {
            "labels": period_months if period_months else ["Current Period"],
            "invoiced": invoiced_data if invoiced_data else [0.0],
            "collected": collected_data if collected_data else [0.0],
            "expenses": expense_data if expense_data else [0.0]
        }

        return {
            "occupancy": occupancy_chart,
            "maintenance_categories": maintenance_category_chart,
            "cashflow": cashflow_chart
        }

    @staticmethod
    def export_villas_csv() -> str:
        """Export all registered villas as CSV formatted string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Villa ID", "Plot Number", "Type", "Status",
            "Built-up Area (sq ft)", "Bedrooms", "Bathrooms",
            "Stories", "Private Pool", "Current Primary Resident", "Outstanding Balance ($)"
        ])

        villas = Villa.query.order_by(Villa.villa_id.asc()).all()
        for v in villas:
            res_name = v.primary_resident.full_name if v.primary_resident else "None"
            writer.writerow([
                v.villa_id,
                v.plot_number,
                v.villa_type,
                v.status,
                f"{v.built_up_area:.1f}",
                v.bedrooms,
                v.bathrooms,
                v.stories,
                "Yes" if v.has_private_pool else "No",
                res_name,
                f"{v.outstanding_balance:.2f}"
            ])

        return output.getvalue()

    @staticmethod
    def export_maintenance_csv() -> str:
        """Export all maintenance tickets as CSV formatted string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Ticket Number", "Villa ID", "Category", "Title",
            "Priority", "Status", "Assigned To", "Cost ($)",
            "Reported Date", "Resolved Date", "Resolution Notes"
        ])

        tickets = MaintenanceRequest.query.order_by(MaintenanceRequest.reported_date.desc()).all()
        for t in tickets:
            writer.writerow([
                t.ticket_number,
                t.villa.villa_id if t.villa else "N/A",
                t.category,
                t.title,
                t.priority,
                t.status,
                t.assigned_to or "Unassigned",
                f"{t.cost:.2f}",
                t.reported_date.strftime("%Y-%m-%d %H:%M"),
                t.resolved_date.strftime("%Y-%m-%d %H:%M") if t.resolved_date else "",
                t.resolution_notes or ""
            ])

        return output.getvalue()

    @staticmethod
    def export_finance_csv() -> str:
        """Export financial fee charges and collections as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Invoice Number", "Villa ID", "Period Month", "Charge Type",
            "Invoiced Amount ($)", "Total Paid ($)", "Balance ($)", "Status", "Due Date"
        ])

        charges = FeeCharge.query.order_by(FeeCharge.due_date.desc()).all()
        for c in charges:
            writer.writerow([
                c.invoice_number,
                c.villa.villa_id if c.villa else "N/A",
                c.period_month,
                c.charge_type,
                f"{c.amount:.2f}",
                f"{c.total_paid:.2f}",
                f"{c.balance:.2f}",
                c.status,
                c.due_date.strftime("%Y-%m-%d")
            ])

        return output.getvalue()
