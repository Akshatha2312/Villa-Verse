from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from app.services import finance_service
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord
from app.forms.finance_forms import GenerateChargesForm, RecordPaymentForm, ExpenseForm
from app.exceptions import VillaVerseError

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

@finance_bp.route("/")
def index():
    """Financial ledger overview and fee charges listing."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    period_filter = request.args.get("period", "").strip()

    charges, total_count, total_pages = finance_service.search_charges(
        search_query=search_query,
        status=status_filter,
        period_month=period_filter,
        page=page,
        per_page=15
    )

    summary = finance_service.get_financial_summary()
    recent_payments = PaymentRecord.query.order_by(PaymentRecord.payment_date.desc()).limit(8).all()

    return render_template(
        "finance/index.html",
        charges=charges,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        search_query=search_query,
        status_filter=status_filter,
        period_filter=period_filter,
        summary=summary,
        recent_payments=recent_payments,
        statuses=[FeeCharge.STATUS_UNPAID, FeeCharge.STATUS_PARTIAL, FeeCharge.STATUS_PAID]
    )

@finance_bp.route("/generate", methods=["GET", "POST"])
def generate():
    """Generate monthly community maintenance dues."""
    form = GenerateChargesForm()
    # Default to current month: YYYY-MM
    if request.method == "GET" and not form.period_month.data:
        form.period_month.data = datetime.now().strftime("%Y-%m")

    if form.validate_on_submit():
        try:
            created = finance_service.generate_monthly_charges(
                period_month=form.period_month.data,
                rate_per_sqft=form.rate_per_sqft.data,
                due_days=form.due_days.data
            )
            flash(f"Successfully generated {created} monthly invoices for {form.period_month.data}.", "success")
            return redirect(url_for("finance.index"))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("finance/generate.html", form=form)

@finance_bp.route("/charges/<int:charge_id>/pay", methods=["GET", "POST"])
def record_payment(charge_id: int):
    """Record an administrative payment toward a fee charge."""
    try:
        charge = finance_service.get_or_404(charge_id)
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("finance.index"))

    form = RecordPaymentForm()

    if request.method == "GET":
        form.amount.data = charge.balance

    if form.validate_on_submit():
        try:
            payment = finance_service.record_payment(
                fee_charge_id=charge.id,
                amount=form.amount.data,
                payment_method=form.payment_method.data,
                transaction_reference=form.transaction_reference.data,
                notes=form.notes.data
            )
            flash(f"Payment of ${payment.amount:.2f} logged successfully (Receipt: {payment.receipt_number})!", "success")
            return redirect(url_for("finance.index"))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("finance/pay.html", charge=charge, form=form)

@finance_bp.route("/expenses", methods=["GET", "POST"])
def expenses():
    """View and record community operational expenses."""
    form = ExpenseForm()
    page = request.args.get("page", 1, type=int)
    category_filter = request.args.get("category", "").strip()

    if form.validate_on_submit():
        try:
            data = {
                "category": form.category.data,
                "title": form.title.data,
                "amount": form.amount.data,
                "expense_date": form.expense_date.data,
                "vendor_name": form.vendor_name.data,
                "receipt_reference": form.receipt_reference.data,
                "description": form.description.data
            }
            exp = finance_service.add_expense(data)
            flash(f"Operational expense '{exp.title}' (${exp.amount:.2f}) recorded successfully.", "success")
            return redirect(url_for("finance.expenses"))
        except VillaVerseError as e:
            flash(e.message, "danger")

    expenses_list, total_count, total_pages = finance_service.search_expenses(
        category=category_filter,
        page=page,
        per_page=15
    )

    total_expense_sum = sum(e.amount for e in ExpenseRecord.query.all())

    return render_template(
        "finance/expenses.html",
        form=form,
        expenses=expenses_list,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        category_filter=category_filter,
        categories=ExpenseRecord.CATEGORIES,
        total_expense_sum=total_expense_sum
    )
