from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models.finance import PaymentRecord, ExpenseRecord

class GenerateChargesForm(FlaskForm):
    """Form to generate bulk monthly maintenance dues."""
    period_month = StringField("Billing Month (YYYY-MM)", validators=[DataRequired(), Length(min=7, max=7)])
    rate_per_sqft = FloatField(
        "Rate per Square Foot (₹)",
        default=0.15,
        validators=[DataRequired(), NumberRange(min=0.01, max=10.0)]
    )
    due_days = IntegerField("Payment Due Day of Month", default=15, validators=[DataRequired(), NumberRange(min=1, max=28)])
    submit = SubmitField("Generate Invoices")


class RecordPaymentForm(FlaskForm):
    """Form to record an administrative payment against an invoice."""
    amount = FloatField("Payment Amount (₹)", validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField(
        "Payment Channel",
        choices=[(m, m) for m in PaymentRecord.PAYMENT_METHODS],
        validators=[DataRequired()]
    )
    transaction_reference = StringField("Bank / Cheque / Transaction Ref", validators=[Optional(), Length(max=80)])
    notes = TextAreaField("Administrative Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Record Payment")


class ExpenseForm(FlaskForm):
    """Form to record an operational community expense."""
    category = SelectField(
        "Expense Category",
        choices=[(c, c) for c in ExpenseRecord.CATEGORIES],
        validators=[DataRequired()]
    )
    title = StringField("Expense Title / Purpose", validators=[DataRequired(), Length(max=120)])
    amount = FloatField("Amount (₹)", validators=[DataRequired(), NumberRange(min=0.01)])
    expense_date = DateField("Date Incurred", validators=[Optional()])
    vendor_name = StringField("Vendor / Contractor Name", validators=[DataRequired(), Length(max=100)])
    receipt_reference = StringField("Invoice / Receipt Number", validators=[Optional(), Length(max=60)])
    description = TextAreaField("Description & Scope", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Record Community Expense")
