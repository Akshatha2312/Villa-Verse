from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from app.models.villa import Villa

class VillaForm(FlaskForm):
    """Form for registering and updating villas."""
    villa_id = StringField("Villa ID", validators=[DataRequired(), Length(max=20)])
    plot_number = StringField("Plot Number", validators=[DataRequired(), Length(max=20)])
    villa_type = SelectField(
        "Villa Architectural Type",
        choices=[(vt, vt) for vt in Villa.VILLA_TYPES],
        validators=[DataRequired()]
    )
    built_up_area = FloatField("Built-up Area (sq. ft.)", validators=[DataRequired(), NumberRange(min=100.0, max=50000.0)])
    bedrooms = IntegerField("Bedrooms", default=3, validators=[DataRequired(), NumberRange(min=1, max=15)])
    bathrooms = IntegerField("Bathrooms", default=3, validators=[DataRequired(), NumberRange(min=1, max=15)])
    stories = IntegerField("Stories / Floors", default=2, validators=[DataRequired(), NumberRange(min=1, max=5)])
    parking_slots = IntegerField("Covered Parking Slots", default=2, validators=[DataRequired(), NumberRange(min=0, max=10)])
    has_private_pool = BooleanField("Private Swimming Pool")
    garden_area_sqft = FloatField("Private Garden Area (sq. ft.)", default=0.0, validators=[Optional(), NumberRange(min=0.0)])
    status = SelectField(
        "Occupancy Status",
        choices=[(s, s) for s in Villa.ALLOWED_STATUSES],
        default=Villa.STATUS_AVAILABLE,
        validators=[DataRequired()]
    )
    notes = TextAreaField("Property Notes & Highlights", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Villa Record")
