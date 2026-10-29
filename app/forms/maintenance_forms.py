from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, FloatField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app.models.maintenance import MaintenanceRequest

class MaintenanceRequestForm(FlaskForm):
    """Form to submit a new maintenance work order."""
    villa_id = SelectField("Villa", coerce=int, validators=[DataRequired()])
    category = SelectField(
        "Maintenance Category",
        choices=[(c, c) for c in MaintenanceRequest.CATEGORIES],
        validators=[DataRequired()]
    )
    title = StringField("Issue Summary", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Detailed Description & Location", validators=[DataRequired(), Length(max=2000)])
    priority = SelectField(
        "Priority Level",
        choices=[(p, p) for p in MaintenanceRequest.ALLOWED_PRIORITIES],
        default=MaintenanceRequest.PRIORITY_MEDIUM,
        validators=[DataRequired()]
    )
    assigned_to = StringField("Assign Technician / Contractor (Optional)", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Submit Work Order")


class MaintenanceUpdateForm(FlaskForm):
    """Form to update or resolve an existing maintenance ticket."""
    status = SelectField(
        "Update Status",
        choices=[(s, s) for s in MaintenanceRequest.ALLOWED_STATUSES],
        validators=[DataRequired()]
    )
    assigned_to = StringField("Assigned Technician / Contractor", validators=[Optional(), Length(max=80)])
    cost = FloatField("Incurred Cost ($)", default=0.0, validators=[Optional(), NumberRange(min=0.0)])
    resolution_notes = TextAreaField("Resolution / Progress Notes", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Update Ticket")
