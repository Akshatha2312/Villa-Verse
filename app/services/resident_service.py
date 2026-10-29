from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime, timezone
from sqlalchemy import or_
from app.extensions import db
from app.models.member import CommunityMember, Owner, Resident
from app.models.villa import Villa
from app.models.occupancy import VillaOccupancy
from app.services.base import BaseService
from app.exceptions import (
    MemberNotFoundError,
    VillaNotFoundError,
    ResidentAssignmentError,
    BusinessRuleViolationError
)

class ResidentService(BaseService[CommunityMember]):
    """
    Service layer handling Member (Owner/Resident) and Villa Occupancy workflows.
    Demonstrates OOP:
      - Polymorphic creation and management of Owner vs Resident
      - Encapsulation of occupancy lifecycle, transfers, and vacancy history
    """

    def get_by_id(self, entity_id: int) -> Optional[CommunityMember]:
        return db.session.get(CommunityMember, entity_id)

    def get_or_404(self, entity_id: int) -> CommunityMember:
        member = self.get_by_id(entity_id)
        if not member:
            raise MemberNotFoundError(entity_id)
        return member

    def list_all(self, **filters) -> List[CommunityMember]:
        query = CommunityMember.query
        if "member_type" in filters and filters["member_type"]:
            query = query.filter_by(member_type=filters["member_type"])
        return query.order_by(CommunityMember.first_name.asc(), CommunityMember.last_name.asc()).all()

    def search_members(
        self,
        search_query: Optional[str] = None,
        member_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 15
    ) -> Tuple[List[CommunityMember], int, int]:
        """Search and paginate owners and residents."""
        query = CommunityMember.query

        if search_query:
            q = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    CommunityMember.first_name.ilike(q),
                    CommunityMember.last_name.ilike(q),
                    CommunityMember.email.ilike(q),
                    CommunityMember.phone.ilike(q)
                )
            )

        if member_type in ("owner", "resident"):
            query = query.filter(CommunityMember.member_type == member_type)

        query = query.order_by(CommunityMember.created_at.desc())
        total_count = query.count()
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total_count, total_pages

    def register_owner(self, data: Dict[str, Any]) -> Owner:
        """Register a property owner with deed information."""
        email = data.get("email", "").strip().lower()
        if CommunityMember.query.filter_by(email=email).first():
            raise BusinessRuleViolationError(f"A member with email '{email}' already exists.")

        owner = Owner(
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            email=email,
            phone=data.get("phone", "").strip(),
            deed_number=data.get("deed_number", "").strip() or None,
            emergency_contact=data.get("emergency_contact", "").strip() or None
        )
        owner.validate_contact_info()
        db.session.add(owner)
        self.commit_or_rollback()
        return owner

    def register_resident(self, data: Dict[str, Any]) -> Resident:
        """Register a tenant/resident with lease details."""
        email = data.get("email", "").strip().lower()
        if CommunityMember.query.filter_by(email=email).first():
            raise BusinessRuleViolationError(f"A member with email '{email}' already exists.")

        lease_start = data.get("lease_start_date")
        if isinstance(lease_start, str) and lease_start:
            lease_start = datetime.strptime(lease_start, "%Y-%m-%d").date()

        lease_end = data.get("lease_end_date")
        if isinstance(lease_end, str) and lease_end:
            lease_end = datetime.strptime(lease_end, "%Y-%m-%d").date()

        resident = Resident(
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            email=email,
            phone=data.get("phone", "").strip(),
            lease_start_date=lease_start,
            lease_end_date=lease_end,
            is_primary_tenant=bool(data.get("is_primary_tenant", True))
        )
        resident.validate_contact_info()
        db.session.add(resident)
        self.commit_or_rollback()
        return resident

    def assign_to_villa(
        self,
        villa_id: int,
        member_id: int,
        role: str,
        is_primary: bool = False,
        move_in_date: Optional[date] = None,
        notes: str = ""
    ) -> VillaOccupancy:
        """
        Assign a member to a villa.
        Validates villa status and auto-updates villa occupancy state.
        """
        villa = db.session.get(Villa, villa_id)
        if not villa:
            raise VillaNotFoundError(villa_id)

        member = db.session.get(CommunityMember, member_id)
        if not member:
            raise MemberNotFoundError(member_id)

        # Domain Constraint: Cannot assign to a villa under construction
        if villa.status == Villa.STATUS_UNDER_CONSTRUCTION:
            raise ResidentAssignmentError(
                f"Cannot assign residents to Villa {villa.villa_id} because it is currently Under Construction."
            )

        # Check if already active in this villa
        existing = VillaOccupancy.query.filter_by(
            villa_id=villa.id,
            member_id=member.id,
            is_active=True
        ).first()

        if existing:
            raise ResidentAssignmentError(
                f"{member.full_name} is already an active resident of Villa {villa.villa_id}."
            )

        # If designated as primary, clear any existing primary flag on this villa
        if is_primary:
            for occ in villa.occupancies:
                if occ.is_active:
                    occ.is_primary = False

        occupancy = VillaOccupancy(
            villa_id=villa.id,
            member_id=member.id,
            role=role,
            is_primary=is_primary,
            move_in_date=move_in_date or date.today(),
            is_active=True,
            notes=notes.strip()
        )
        db.session.add(occupancy)

        # Auto-update villa status to Occupied
        if villa.status == Villa.STATUS_AVAILABLE:
            villa.change_status(Villa.STATUS_OCCUPIED)

        self.commit_or_rollback()
        return occupancy

    def vacate_occupancy(self, occupancy_id: int, vacate_date: Optional[date] = None, reason: str = "") -> VillaOccupancy:
        """
        Vacate an occupancy record while preserving historical tracking.
        If no active occupants remain, reverts villa to Available.
        """
        occupancy = db.session.get(VillaOccupancy, occupancy_id)
        if not occupancy:
            raise BusinessRuleViolationError("Occupancy record not found.")

        villa = occupancy.villa
        occupancy.vacate(vacate_date or date.today(), reason)

        # Check if any active occupancies remain
        active_remaining = [occ for occ in villa.occupancies if occ.is_active and occ.id != occupancy.id]
        if not active_remaining:
            villa.change_status(Villa.STATUS_AVAILABLE)

        self.commit_or_rollback()
        return occupancy

    def transfer_resident(
        self,
        occupancy_id: int,
        new_villa_id: int,
        transfer_date: Optional[date] = None,
        reason: str = "Transfer to another villa"
    ) -> VillaOccupancy:
        """
        Transfers an active resident from their current villa to a new one.
        Historical occupancy is closed and a new record is generated.
        """
        old_occ = db.session.get(VillaOccupancy, occupancy_id)
        if not old_occ or not old_occ.is_active:
            raise BusinessRuleViolationError("Active occupancy record required for transfer.")

        member_id = old_occ.member_id
        role = old_occ.role
        is_primary = old_occ.is_primary
        eff_date = transfer_date or date.today()

        # Vacate old villa
        self.vacate_occupancy(old_occ.id, eff_date, reason)

        # Assign to new villa
        new_occ = self.assign_to_villa(
            villa_id=new_villa_id,
            member_id=member_id,
            role=role,
            is_primary=is_primary,
            move_in_date=eff_date,
            notes=f"Transferred from Villa {old_occ.villa.villa_id}"
        )
        return new_occ
