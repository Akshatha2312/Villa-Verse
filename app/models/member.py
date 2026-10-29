from datetime import datetime, timezone
import re
from app.extensions import db
from app.models.base import BaseModel
from app.exceptions import BusinessRuleViolationError

class CommunityMember(BaseModel):
    """
    Base class representing any individual registered in the community.
    Demonstrates OOP:
      - Inheritance (extended by Owner and Resident)
      - Polymorphism (common interface overridden in subclasses)
      - Encapsulation (protected fields with property getters/setters and validations)
    """
    __tablename__ = "community_members"

    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(25), nullable=False)
    member_type = db.Column(db.String(20), nullable=False)  # 'owner' or 'resident'
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Polymorphic Single-Table configuration
    __mapper_args__ = {
        "polymorphic_on": member_type,
        "polymorphic_identity": "member"
    }

    # Relationships
    occupancies = db.relationship("VillaOccupancy", back_populates="member", cascade="all, delete-orphan", lazy="select")
    maintenance_reports = db.relationship("MaintenanceRequest", back_populates="reported_by", foreign_keys="MaintenanceRequest.reported_by_id", lazy="select")

    # Encapsulation via Properties
    @property
    def full_name(self) -> str:
        """Returns the full name of the community member."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def contact_summary(self) -> str:
        return f"{self.full_name} ({self.email} | {self.phone})"

    def validate_contact_info(self):
        """Enforces contact details sanity."""
        if not self.first_name or not self.last_name:
            raise BusinessRuleViolationError("First and last names are mandatory.")
        if not self.email or "@" not in self.email:
            raise BusinessRuleViolationError(f"Invalid email address: {self.email}")
        if not self.phone or len(re.sub(r"\D", "", self.phone)) < 7:
            raise BusinessRuleViolationError("Phone number must contain at least 7 digits.")

    # Polymorphic methods (intended to be overridden by subclasses)
    def get_role_label(self) -> str:
        """Polymorphic method: returns a human-readable role."""
        return "Community Member"

    def get_badge_class(self) -> str:
        """Polymorphic method: returns CSS class for UI badges."""
        return "bg-secondary text-white"

    def can_vote_in_agm(self) -> bool:
        """Polymorphic method: checks voting rights in Annual General Meetings."""
        return False

    def format_summary(self) -> str:
        """Polymorphic method: returns role-specific formatted summary."""
        return f"{self.full_name} - {self.get_role_label()}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}: {self.full_name} ({self.email})>"


class Owner(CommunityMember):
    """
    Specialized subclass representing a registered property owner.
    Demonstrates OOP Inheritance & Polymorphism.
    """
    deed_number = db.Column(db.String(50), nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "owner"
    }

    def __init__(self, **kwargs):
        kwargs["member_type"] = "owner"
        super().__init__(**kwargs)

    # Polymorphic overrides
    def get_role_label(self) -> str:
        return "Property Owner"

    def get_badge_class(self) -> str:
        return "bg-gold text-dark"

    def can_vote_in_agm(self) -> bool:
        """Only legal owners have voting power in the community AGM."""
        return True

    def format_summary(self) -> str:
        deed_info = f" [Deed: {self.deed_number}]" if self.deed_number else ""
        return f"Owner: {self.full_name}{deed_info}"


class Resident(CommunityMember):
    """
    Specialized subclass representing a tenant or resident leasing a villa.
    Demonstrates OOP Inheritance & Polymorphism.
    """
    lease_start_date = db.Column(db.Date, nullable=True)
    lease_end_date = db.Column(db.Date, nullable=True)
    is_primary_tenant = db.Column(db.Boolean, default=True, nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "resident"
    }

    def __init__(self, **kwargs):
        kwargs["member_type"] = "resident"
        super().__init__(**kwargs)

    # Polymorphic overrides
    def get_role_label(self) -> str:
        return "Resident Tenant"

    def get_badge_class(self) -> str:
        return "bg-forest-light text-forest"

    def can_vote_in_agm(self) -> bool:
        """Tenants do not have voting rights on property ownership resolutions."""
        return False

    def is_lease_active(self) -> bool:
        """Check if lease is currently active."""
        if not self.lease_end_date:
            return True
        return self.lease_end_date >= datetime.now(timezone.utc).date()

    def format_summary(self) -> str:
        active_status = "Active Lease" if self.is_lease_active() else "Lease Expired"
        return f"Resident: {self.full_name} ({active_status})"
