from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.base import BaseModel
from app.exceptions import InvalidStatusTransitionError, BusinessRuleViolationError

class MaintenanceRequest(BaseModel):
    """
    Entity representing a maintenance work order associated with a villa.
    Demonstrates OOP:
      - Encapsulation: Status flow management (Open -> In Progress -> Resolved)
      - Computed properties for urgency, overdue tracking, and SLA monitoring
    """
    __tablename__ = "maintenance_requests"

    # Status Constants
    STATUS_OPEN = "Open"
    STATUS_IN_PROGRESS = "In Progress"
    STATUS_RESOLVED = "Resolved"
    STATUS_CANCELLED = "Cancelled"

    ALLOWED_STATUSES = (
        STATUS_OPEN,
        STATUS_IN_PROGRESS,
        STATUS_RESOLVED,
        STATUS_CANCELLED
    )

    # Priority Constants
    PRIORITY_LOW = "Low"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_HIGH = "High"
    PRIORITY_URGENT = "Urgent"

    ALLOWED_PRIORITIES = (
        PRIORITY_LOW,
        PRIORITY_MEDIUM,
        PRIORITY_HIGH,
        PRIORITY_URGENT
    )

    # Categories
    CATEGORIES = [
        "Plumbing",
        "Electrical",
        "HVAC & Cooling",
        "Landscaping & Irrigation",
        "Roofing & Civil",
        "Swimming Pool & Spa",
        "Pest Control",
        "Security & Intercom",
        "General Maintenance"
    ]

    ticket_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    villa_id = db.Column(db.Integer, db.ForeignKey("villas.id"), nullable=False, index=True)
    reported_by_id = db.Column(db.Integer, db.ForeignKey("community_members.id"), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False, default=PRIORITY_MEDIUM, index=True)
    status = db.Column(db.String(20), nullable=False, default=STATUS_OPEN, index=True)
    assigned_to = db.Column(db.String(80), nullable=True)  # Technician or contractor
    cost = db.Column(db.Float, nullable=False, default=0.0)
    reported_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    resolved_date = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    # Relationships
    villa = db.relationship("Villa", back_populates="maintenance_requests")
    reported_by = db.relationship("CommunityMember", back_populates="maintenance_reports", foreign_keys=[reported_by_id])

    # Domain Methods & State Machine
    def assign_technician(self, technician_name: str):
        """Assign contractor/staff and move status to In Progress if Open."""
        if not technician_name or not technician_name.strip():
            raise BusinessRuleViolationError("Technician name cannot be empty.")
        self.assigned_to = technician_name.strip()
        if self.status == self.STATUS_OPEN:
            self.status = self.STATUS_IN_PROGRESS

    def resolve(self, resolution_notes: str, cost: float = 0.0):
        """Transition request to Resolved with mandatory resolution notes."""
        if self.status == self.STATUS_RESOLVED:
            return
        if self.status == self.STATUS_CANCELLED:
            raise InvalidStatusTransitionError("MaintenanceRequest", self.status, self.STATUS_RESOLVED)
        if not resolution_notes or len(resolution_notes.strip()) < 5:
            raise BusinessRuleViolationError("Meaningful resolution notes (at least 5 characters) are required.")
        if cost < 0:
            raise BusinessRuleViolationError("Maintenance repair cost cannot be negative.")

        self.status = self.STATUS_RESOLVED
        self.resolution_notes = resolution_notes.strip()
        self.cost = float(cost)
        self.resolved_date = datetime.now(timezone.utc)

    def cancel(self, reason: str):
        """Cancel a maintenance ticket."""
        if self.status == self.STATUS_RESOLVED:
            raise InvalidStatusTransitionError("MaintenanceRequest", self.status, self.STATUS_CANCELLED)
        self.status = self.STATUS_CANCELLED
        self.resolution_notes = f"Cancelled: {reason}".strip()

    # Properties
    @property
    def is_urgent(self) -> bool:
        return self.priority == self.PRIORITY_URGENT

    @property
    def is_resolved(self) -> bool:
        return self.status == self.STATUS_RESOLVED

    @property
    def is_overdue(self) -> bool:
        """
        Calculates whether the SLA has been breached:
        Urgent: > 24 hours
        High: > 48 hours
        Medium/Low: > 5 days
        """
        if self.is_resolved or self.status == self.STATUS_CANCELLED:
            return False

        now = datetime.now(timezone.utc)
        created = self.reported_date
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        elapsed = now - created
        if self.priority == self.PRIORITY_URGENT and elapsed > timedelta(hours=24):
            return True
        elif self.priority == self.PRIORITY_HIGH and elapsed > timedelta(hours=48):
            return True
        elif elapsed > timedelta(days=5):
            return True
        return False

    @property
    def priority_badge_class(self) -> str:
        mapping = {
            self.PRIORITY_URGENT: "badge-priority-urgent",
            self.PRIORITY_HIGH: "badge-priority-high",
            self.PRIORITY_MEDIUM: "badge-priority-medium",
            self.PRIORITY_LOW: "badge-priority-low",
        }
        return mapping.get(self.priority, "badge-secondary")

    @property
    def status_badge_class(self) -> str:
        mapping = {
            self.STATUS_OPEN: "badge-maint-open",
            self.STATUS_IN_PROGRESS: "badge-maint-progress",
            self.STATUS_RESOLVED: "badge-maint-resolved",
            self.STATUS_CANCELLED: "badge-maint-cancelled"
        }
        return mapping.get(self.status, "badge-secondary")

    def __repr__(self) -> str:
        return f"<MaintenanceRequest {self.ticket_number} - {self.category} ({self.priority}, {self.status})>"
