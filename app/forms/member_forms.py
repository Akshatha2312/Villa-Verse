from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SelectField, BooleanField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.models.occupancy import VillaOccupancy

class OwnerForm(FlaskForm):
    """Form to register a property owner."""
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=60)])
    email = EmailField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=7, max=25)])
    deed_number = StringField("Ownership Title / Deed Number", validators=[Optional(), Length(max=50)])
    emergency_contact = StringField("Emergency Contact Details", validators=[Optional(), Length(max=100)])
    submit = SubmitField("Register Owner")


class ResidentForm(FlaskForm):
    """Form to register a tenant / resident."""
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=60)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=60)])
    email = EmailField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=7, max=25)])
    lease_start_date = DateField("Lease Start Date", validators=[Optional()])
    lease_end_date = DateField("Lease End Date", validators=[Optional()])
    is_primary_tenant = BooleanField("Is Primary Leaseholder", default=True)
    submit = SubmitField("Register Resident")


class AssignResidentForm(FlaskForm):
    """Form to link an owner or resident to a villa."""
    villa_id = SelectField("Target Villa", coerce=int, validators=[DataRequired()])
    member_id = SelectField("Community Member", coerce=int, validators=[DataRequired()])
    role = SelectField(
        "Occupancy Role",
        choices=[(r, r) for r in VillaOccupancy.ALLOWED_ROLES],
        default=VillaOccupancy.ROLE_TENANT,
        validators=[DataRequired()]
    )
    is_primary = BooleanField("Designate as Primary Contact for Villa", default=True)
    move_in_date = DateField("Move-in Date", validators=[Optional()])
    notes = TextAreaField("Tenancy / Assignment Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Assign to Villa")
