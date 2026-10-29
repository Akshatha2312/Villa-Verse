from datetime import datetime, timezone, date
from app.extensions import db
from app.models.base import BaseModel
from app.exceptions import InvalidPaymentError, BusinessRuleViolationError
from app.currency import format_inr

class FeeCharge(BaseModel):
    """
    Represents an invoiced fee or maintenance assessment assigned to a villa.
    Demonstrates OOP:
      - Encapsulation: Balances, payment applications, and status recalculation
      - Composition: Holds collection of PaymentRecords
    """
    __tablename__ = "fee_charges"

    STATUS_UNPAID = "Unpaid"
    STATUS_PARTIAL = "Partially Paid"
    STATUS_PAID = "Paid"

    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    villa_id = db.Column(db.Integer, db.ForeignKey("villas.id"), nullable=False, index=True)
    period_month = db.Column(db.String(7), nullable=False, index=True)
    charge_type = db.Column(db.String(50), nullable=False, default="Monthly Community Maintenance")
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_UNPAID, index=True)
    description = db.Column(db.String(255), nullable=True)

    villa = db.relationship("Villa", back_populates="fee_charges")
    payments = db.relationship("PaymentRecord", back_populates="fee_charge", cascade="all, delete-orphan", lazy="select")

    @property
    def total_paid(self) -> float:
        """Sum of all applied payments."""
        return round(sum(p.amount for p in self.payments), 2)

    @property
    def balance(self) -> float:
        """Remaining outstanding balance."""
        rem = self.amount - self.total_paid
        return round(max(0.0, rem), 2)

    @property
    def is_overdue(self) -> bool:
        if self.status == self.STATUS_PAID:
            return False
        return self.due_date < date.today()

    def record_payment(self, amount: float, payment_method: str, reference: str = "", notes: str = "") -> "PaymentRecord":
        """
        Encapsulated method to apply a payment.
        Validates amount and updates charge status accordingly.
        """
        if amount <= 0:
            raise InvalidPaymentError("Payment amount must be greater than zero.")
        
        current_balance = self.balance
        if amount > current_balance + 0.001:  # small float tolerance
            raise InvalidPaymentError(
                f"Payment amount ({format_inr(amount)}) exceeds the outstanding balance ({format_inr(current_balance)})."
            )

        receipt_no = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.id}"
        payment = PaymentRecord(
            receipt_number=receipt_no,
            fee_charge_id=self.id,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=reference.strip() or f"MANUAL-REF-{receipt_no[-6:]}",
            notes=notes.strip()
        )
        self.payments.append(payment)

        new_balance = self.balance - amount
        if new_balance <= 0.01:
            self.status = self.STATUS_PAID
        else:
            self.status = self.STATUS_PARTIAL

        return payment

    @property
    def status_badge_class(self) -> str:
        mapping = {
            self.STATUS_PAID: "badge-fee-paid",
            self.STATUS_PARTIAL: "badge-fee-partial",
            self.STATUS_UNPAID: "badge-fee-unpaid"
        }
        return mapping.get(self.status, "badge-secondary")

    def __repr__(self) -> str:
        return f"<FeeCharge {self.invoice_number} Villa:{self.villa_id} ({format_inr(self.amount)}, {self.status})>"


class PaymentRecord(BaseModel):
    """
    Represents an administrative payment received against an invoiced fee.
    Note: VillaVerse is a community management ledger, not a payment gateway.
    """
    __tablename__ = "payment_records"

    PAYMENT_METHODS = [
        "NEFT / RTGS Bank Transfer",
        "UPI Payment",
        "Credit / Debit Card",
        "IMPS Online Transfer",
        "Demand Draft / Cheque",
        "Cash Deposit"
    ]

    receipt_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    fee_charge_id = db.Column(db.Integer, db.ForeignKey("fee_charges.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(40), nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    transaction_reference = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.String(255), nullable=True)

    fee_charge = db.relationship("FeeCharge", back_populates="payments")

    def __repr__(self) -> str:
        return f"<PaymentRecord {self.receipt_number} ({format_inr(self.amount)} via {self.payment_method})>"


class ExpenseRecord(BaseModel):
    """
    Tracks community operational expenses (Security, Landscaping, Common Utilities, etc.)
    Separate from resident payments, to provide accurate P&L community cashflow.
    """
    __tablename__ = "expense_records"

    CATEGORIES = [
        "Security & Guard Services",
        "Landscaping & Grounds Keeping",
        "Swimming Pool Maintenance",
        "Common Utilities (Water & Electricity)",
        "Waste Management & Sanitation",
        "Clubhouse Operations",
        "Infrastructure & Road Repairs",
        "Community Insurance & Legal",
        "Administrative & Office"
    ]

    expense_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    vendor_name = db.Column(db.String(100), nullable=False)
    receipt_reference = db.Column(db.String(60), nullable=True)
    description = db.Column(db.Text, nullable=True)

    def validate(self):
        if self.amount <= 0:
            raise BusinessRuleViolationError("Expense amount must be a positive number.")
        if not self.title:
            raise BusinessRuleViolationError("Expense title cannot be empty.")
        if not self.vendor_name:
            raise BusinessRuleViolationError("Vendor name cannot be empty.")

    def __repr__(self) -> str:
        return f"<ExpenseRecord {self.expense_number} - {self.category} ({format_inr(self.amount)})>"
