from datetime import datetime, timezone, date
from app.extensions import db
from app.models.base import BaseModel
from app.exceptions import BusinessRuleViolationError

class VillaOccupancy(BaseModel):
    """
    Association entity linking CommunityMember with a Villa.
    Maintains historical residency logs, move-in/move-out timestamps,
    and supports multiple residents per villa.
    """
    __tablename__ = "villa_occupancies"

    ROLE_OWNER_OCCUPANT = "Owner-Occupant"
    ROLE_TENANT = "Tenant"
    ROLE_NON_RESIDENT_OWNER = "Non-Resident Owner"

    ALLOWED_ROLES = (
        ROLE_OWNER_OCCUPANT,
        ROLE_TENANT,
        ROLE_NON_RESIDENT_OWNER
    )

    villa_id = db.Column(db.Integer, db.ForeignKey("villas.id"), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("community_members.id"), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default=ROLE_TENANT)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    move_in_date = db.Column(db.Date, nullable=False, default=date.today)
    move_out_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    notes = db.Column(db.String(255), nullable=True)

    # Relationships
    villa = db.relationship("Villa", back_populates="occupancies")
    member = db.relationship("CommunityMember", back_populates="occupancies")

    def vacate(self, vacate_date: date | None = None, reason: str = ""):
        """
        Marks this occupancy record as inactive while preserving historical data.
        """
        if not self.is_active:
            raise BusinessRuleViolationError("This occupancy record is already inactive.")

        self.is_active = False
        self.move_out_date = vacate_date or date.today()
        if reason:
            self.notes = f"{self.notes or ''} [Vacated: {reason}]".strip()

    def __repr__(self) -> str:
        status_str = "Active" if self.is_active else "Past"
        return f"<VillaOccupancy Villa:{self.villa_id} Member:{self.member_id} ({self.role}, {status_str})>"
