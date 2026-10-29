from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import or_, func, desc
from app.extensions import db
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord
from app.models.villa import Villa
from app.services.base import BaseService
from app.exceptions import EntityNotFoundError, VillaNotFoundError, BusinessRuleViolationError, InvalidPaymentError

class FinanceService(BaseService[FeeCharge]):
    """
    Service layer handling Community Dues, Payments, and Operating Expenses.
    Demonstrates OOP:
      - Encapsulation of financial transactions and balance tracking
      - Separation of resident revenue from community operational expenses
    """

    def get_by_id(self, entity_id: int) -> Optional[FeeCharge]:
        return db.session.get(FeeCharge, entity_id)

    def get_or_404(self, charge_id: int) -> FeeCharge:
        charge = self.get_by_id(charge_id)
        if not charge:
            raise EntityNotFoundError("FeeCharge", charge_id)
        return charge

    def list_all(self, **filters) -> List[FeeCharge]:
        query = FeeCharge.query
        if "status" in filters and filters["status"]:
            query = query.filter_by(status=filters["status"])
        if "villa_id" in filters and filters["villa_id"]:
            query = query.filter_by(villa_id=filters["villa_id"])
        return query.order_by(FeeCharge.due_date.desc()).all()

    def generate_monthly_charges(
        self,
        period_month: str,  # Format: "YYYY-MM"
        rate_per_sqft: float = 0.15,
        due_days: int = 15
    ) -> int:
        """
        Generates monthly maintenance charges for all registered villas.
        Calculates amount based on villa built-up area: area * rate_per_sqft.
        Idempotent: Skips villas that already have an invoice for this period.
        """
        if rate_per_sqft <= 0:
            raise BusinessRuleViolationError("Fee rate per square foot must be positive.")

        try:
            year, month = map(int, period_month.split("-"))
            # Due date 15th of the month
            due_date = date(year, month, min(due_days, 28))
        except (ValueError, TypeError):
            raise BusinessRuleViolationError("Period month must be in 'YYYY-MM' format.")

        villas = Villa.query.all()
        created_count = 0

        for villa in villas:
            # Check if invoice already exists for this period
            existing = FeeCharge.query.filter_by(
                villa_id=villa.id,
                period_month=period_month
            ).first()

            if existing:
                continue

            amount = round(villa.built_up_area * rate_per_sqft, 2)
            invoice_num = f"INV-{period_month.replace('-', '')}-{villa.villa_id}"

            charge = FeeCharge(
                invoice_number=invoice_num,
                villa_id=villa.id,
                period_month=period_month,
                charge_type="Monthly Community Maintenance",
                amount=amount,
                due_date=due_date,
                status=FeeCharge.STATUS_UNPAID,
                description=f"Monthly maintenance fee for Villa {villa.villa_id} ({villa.built_up_area:.0f} sq.ft @ ${rate_per_sqft}/sq.ft)"
            )
            db.session.add(charge)
            created_count += 1

        self.commit_or_rollback()
        return created_count

    def record_payment(
        self,
        fee_charge_id: int,
        amount: float,
        payment_method: str,
        transaction_reference: str = "",
        notes: str = ""
    ) -> PaymentRecord:
        """
        Apply a payment to a fee charge.
        Delegates validation and balance calculation to FeeCharge entity (Encapsulation).
        """
        charge = self.get_or_404(fee_charge_id)
        payment = charge.record_payment(
            amount=amount,
            payment_method=payment_method,
            reference=transaction_reference,
            notes=notes
        )
        self.commit_or_rollback()
        return payment

    def add_expense(self, data: Dict[str, Any]) -> ExpenseRecord:
        """Record an operational expense incurred by the community."""
        title = data.get("title", "").strip()
        vendor = data.get("vendor_name", "").strip()
        category = data.get("category", "General Operations")
        try:
            amount = float(data.get("amount", 0))
        except (ValueError, TypeError):
            raise BusinessRuleViolationError("Expense amount must be a valid number.")

        expense_date = data.get("expense_date")
        if isinstance(expense_date, str) and expense_date:
            expense_date = datetime.strptime(expense_date, "%Y-%m-%d").date()
        elif not expense_date:
            expense_date = date.today()

        count = ExpenseRecord.query.count() + 1
        expense_num = f"EXP-{expense_date.strftime('%Y%m')}-{count:04d}"

        expense = ExpenseRecord(
            expense_number=expense_num,
            category=category,
            title=title,
            amount=amount,
            expense_date=expense_date,
            vendor_name=vendor,
            receipt_reference=data.get("receipt_reference", "").strip() or None,
            description=data.get("description", "").strip() or None
        )
        expense.validate()
        db.session.add(expense)
        self.commit_or_rollback()
        return expense

    def search_charges(
        self,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        period_month: Optional[str] = None,
        page: int = 1,
        per_page: int = 15
    ) -> Tuple[List[FeeCharge], int, int]:
        """Search and paginate fee charges."""
        query = FeeCharge.query

        if search_query:
            q = f"%{search_query.strip()}%"
            query = query.join(Villa).filter(
                or_(
                    FeeCharge.invoice_number.ilike(q),
                    Villa.villa_id.ilike(q),
                    Villa.plot_number.ilike(q)
                )
            )

        if status in (FeeCharge.STATUS_PAID, FeeCharge.STATUS_PARTIAL, FeeCharge.STATUS_UNPAID):
            query = query.filter(FeeCharge.status == status)

        if period_month:
            query = query.filter(FeeCharge.period_month == period_month)

        query = query.order_by(FeeCharge.due_date.desc())
        total_count = query.count()
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total_count, total_pages

    def search_expenses(
        self,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 15
    ) -> Tuple[List[ExpenseRecord], int, int]:
        """Search and paginate expenses."""
        query = ExpenseRecord.query
        if category:
            query = query.filter(ExpenseRecord.category == category)
        query = query.order_by(ExpenseRecord.expense_date.desc())
        total_count = query.count()
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total_count, total_pages

    def get_financial_summary(self) -> Dict[str, Any]:
        """Compute aggregated community financial metrics."""
        total_invoiced = db.session.query(func.sum(FeeCharge.amount)).scalar() or 0.0
        total_collected = db.session.query(func.sum(PaymentRecord.amount)).scalar() or 0.0
        total_expenses = db.session.query(func.sum(ExpenseRecord.amount)).scalar() or 0.0
        outstanding_balance = max(0.0, total_invoiced - total_collected)
        collection_rate = round((total_collected / total_invoiced * 100), 1) if total_invoiced > 0 else 0.0
        net_surplus = total_collected - total_expenses

        return {
            "total_invoiced": round(total_invoiced, 2),
            "total_collected": round(total_collected, 2),
            "total_expenses": round(total_expenses, 2),
            "outstanding_balance": round(outstanding_balance, 2),
            "collection_rate": collection_rate,
            "net_surplus": round(net_surplus, 2)
        }
