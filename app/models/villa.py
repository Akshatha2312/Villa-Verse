from datetime import datetime, timezone
from app.extensions import db
from app.models.base import BaseModel
from app.exceptions import InvalidStatusTransitionError, BusinessRuleViolationError

class Villa(BaseModel):
    """
    Core Villa domain entity representing an individual villa plot in the community.
    Demonstrates OOP:
      - Encapsulation: Status transitions, validation rules, calculated properties
      - Class attributes & class methods
      - Composition: Aggregates occupancies, maintenance requests, and financial charges
    """
    __tablename__ = "villas"

    STATUS_AVAILABLE = "Available"
    STATUS_OCCUPIED = "Occupied"
    STATUS_UNDER_CONSTRUCTION = "Under Construction"

    ALLOWED_STATUSES = (
        STATUS_AVAILABLE,
        STATUS_OCCUPIED,
        STATUS_UNDER_CONSTRUCTION
    )

    VILLA_TYPES = [
        "The Royal Tuscan (5BHK)",
        "The Grand Palm (4BHK)",
        "The Azure Villa (3BHK)",
        "Serenity Modern (3BHK)",
        "Palm Crest Luxury (4BHK)",
        "Meadow Courtyard (2BHK)"
    ]

    villa_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    plot_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    villa_type = db.Column(db.String(60), nullable=False)
    built_up_area = db.Column(db.Float, nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False, default=3)
    bathrooms = db.Column(db.Integer, nullable=False, default=3)
    stories = db.Column(db.Integer, nullable=False, default=2)
    parking_slots = db.Column(db.Integer, nullable=False, default=2)
    has_private_pool = db.Column(db.Boolean, nullable=False, default=False)
    garden_area_sqft = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(30), nullable=False, default=STATUS_AVAILABLE, index=True)
    notes = db.Column(db.Text, nullable=True)

    occupancies = db.relationship(
        "VillaOccupancy", 
        back_populates="villa", 
        cascade="all, delete-orphan", 
        lazy="select",
        order_by="desc(VillaOccupancy.is_active)"
    )
    maintenance_requests = db.relationship(
        "MaintenanceRequest", 
        back_populates="villa", 
        cascade="all, delete-orphan", 
        lazy="select",
        order_by="desc(MaintenanceRequest.created_at)"
    )
    fee_charges = db.relationship(
        "FeeCharge", 
        back_populates="villa", 
        cascade="all, delete-orphan", 
        lazy="select",
        order_by="desc(FeeCharge.due_date)"
    )

    @classmethod
    def get_allowed_statuses(cls) -> tuple[str, ...]:
        return cls.ALLOWED_STATUSES

    @classmethod
    def create_villa(cls, villa_id: str, plot_number: str, villa_type: str, built_up_area: float, **kwargs) -> "Villa":
        """Factory method validating constraints before instantiating."""
        villa = cls(
            villa_id=villa_id.strip().upper(),
            plot_number=plot_number.strip().upper(),
            villa_type=villa_type.strip(),
            built_up_area=built_up_area,
            **kwargs
        )
        villa.validate()
        return villa

    def validate(self):
        """Enforce domain rules for villa specifications."""
        if not self.villa_id:
            raise BusinessRuleViolationError("Villa ID cannot be empty.")
        if not self.plot_number:
            raise BusinessRuleViolationError("Plot number cannot be empty.")
        if self.built_up_area <= 0:
            raise BusinessRuleViolationError("Built-up area must be a positive number greater than 0.")
        if self.bedrooms < 1:
            raise BusinessRuleViolationError("A villa must have at least 1 bedroom.")
        if self.bathrooms < 1:
            raise BusinessRuleViolationError("A villa must have at least 1 bathroom.")
        if self.status not in self.ALLOWED_STATUSES:
            raise BusinessRuleViolationError(f"Invalid status '{self.status}'. Must be one of {self.ALLOWED_STATUSES}.")

    def change_status(self, new_status: str) -> None:
        """
        Encapsulated state transition method.
        Prevents arbitrary state mutations and enforces business constraints.
        """
        if new_status not in self.ALLOWED_STATUSES:
            raise InvalidStatusTransitionError("Villa", self.status, new_status)

        if self.status == new_status:
            return

        if new_status == self.STATUS_OCCUPIED:
            if self.status == self.STATUS_UNDER_CONSTRUCTION:
                raise InvalidStatusTransitionError(
                    "Villa", 
                    self.status, 
                    f"{new_status} (Villa under construction must first be marked Available before occupation)"
                )
        
        self.status = new_status

    @property
    def area_sqm(self) -> float:
        """Encapsulated unit conversion (sq ft to sq meters)."""
        return round(self.built_up_area * 0.092903, 2)

    @property
    def is_occupied(self) -> bool:
        return self.status == self.STATUS_OCCUPIED

    @property
    def is_available(self) -> bool:
        return self.status == self.STATUS_AVAILABLE

    @property
    def is_under_construction(self) -> bool:
        return self.status == self.STATUS_UNDER_CONSTRUCTION

    @property
    def active_occupancies(self) -> list:
        """Return all current active residents/owners for this villa."""
        return [occ for occ in self.occupancies if occ.is_active]

    @property
    def primary_resident(self):
        """Return the primary resident or owner for communication."""
        for occ in self.active_occupancies:
            if occ.is_primary:
                return occ.member
        return self.active_occupancies[0].member if self.active_occupancies else None

    @property
    def active_maintenance_count(self) -> int:
        """Number of pending/in-progress maintenance requests."""
        return sum(1 for req in self.maintenance_requests if req.status in ("Open", "In Progress"))

    @property
    def outstanding_balance(self) -> float:
        """Total unpaid fees for this villa."""
        return sum(charge.balance for charge in self.fee_charges if charge.balance > 0)

    @property
    def status_badge_class(self) -> str:
        """Returns Bootstrap badge class depending on status."""
        mapping = {
            self.STATUS_OCCUPIED: "badge-status-occupied",
            self.STATUS_AVAILABLE: "badge-status-available",
            self.STATUS_UNDER_CONSTRUCTION: "badge-status-construction"
        }
        return mapping.get(self.status, "badge-secondary")

    def __repr__(self) -> str:
        return f"<Villa {self.villa_id} (Plot: {self.plot_number}) - {self.status}>"
