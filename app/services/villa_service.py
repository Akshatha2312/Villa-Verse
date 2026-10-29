from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import or_, desc, asc
from app.extensions import db
from app.models.villa import Villa
from app.services.base import BaseService
from app.exceptions import (
    VillaNotFoundError,
    DuplicatePlotError,
    DuplicateVillaIdError,
    BusinessRuleViolationError
)

class VillaService(BaseService[Villa]):
    """
    Service layer handling Villa domain business logic.
    Demonstrates OOP:
      - Inherits from abstract BaseService
      - Encapsulates business validation, duplicate prevention, and transaction handling
    """

    def get_by_id(self, entity_id: int) -> Optional[Villa]:
        """Fetch villa by internal database primary key."""
        return db.session.get(Villa, entity_id)

    def get_by_code(self, villa_id: str) -> Optional[Villa]:
        """Fetch villa by human-readable unique identifier (e.g., 'V-101')."""
        return Villa.query.filter_by(villa_id=villa_id.strip().upper()).first()

    def get_or_404(self, identifier: int | str) -> Villa:
        """Fetch villa or raise meaningful domain exception."""
        villa = None
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            villa = self.get_by_id(int(identifier))
        if not villa and isinstance(identifier, str):
            villa = self.get_by_code(identifier)

        if not villa:
            raise VillaNotFoundError(identifier)
        return villa

    def list_all(self, **filters) -> List[Villa]:
        """Retrieve all villas with optional status filtering."""
        query = Villa.query
        if "status" in filters and filters["status"]:
            query = query.filter_by(status=filters["status"])
        return query.order_by(Villa.villa_id.asc()).all()

    def search_and_filter(
        self,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        villa_type: Optional[str] = None,
        sort_by: str = "villa_id",
        sort_dir: str = "asc",
        page: int = 1,
        per_page: int = 12
    ) -> Tuple[List[Villa], int, int]:
        """
        Server-side filtered and paginated search for community villas.
        Returns: (items, total_count, total_pages)
        """
        query = Villa.query

        if search_query:
            q = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Villa.villa_id.ilike(q),
                    Villa.plot_number.ilike(q),
                    Villa.villa_type.ilike(q),
                    Villa.notes.ilike(q)
                )
            )

        if status and status in Villa.ALLOWED_STATUSES:
            query = query.filter(Villa.status == status)

        if villa_type:
            query = query.filter(Villa.villa_type == villa_type)

        sort_column = getattr(Villa, sort_by, Villa.villa_id)
        if sort_dir.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        total_count = query.count()
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        
        paginated_items = query.offset((page - 1) * per_page).limit(per_page).all()
        return paginated_items, total_count, total_pages

    def create_villa(self, data: Dict[str, Any]) -> Villa:
        """
        Register a new villa in the community with duplicate checking.
        """
        villa_id = data.get("villa_id", "").strip().upper()
        plot_number = data.get("plot_number", "").strip().upper()

        # Check unique constraints
        if Villa.query.filter_by(villa_id=villa_id).first():
            raise DuplicateVillaIdError(villa_id)
        if Villa.query.filter_by(plot_number=plot_number).first():
            raise DuplicatePlotError(plot_number)

        try:
            built_up_area = float(data.get("built_up_area", 0))
        except (ValueError, TypeError):
            raise BusinessRuleViolationError("Built-up area must be a valid numeric value.")

        villa = Villa.create_villa(
            villa_id=villa_id,
            plot_number=plot_number,
            villa_type=data.get("villa_type", "The Grand Palm (4BHK)"),
            built_up_area=built_up_area,
            bedrooms=int(data.get("bedrooms", 3)),
            bathrooms=int(data.get("bathrooms", 3)),
            stories=int(data.get("stories", 2)),
            parking_slots=int(data.get("parking_slots", 2)),
            has_private_pool=bool(data.get("has_private_pool", False)),
            garden_area_sqft=float(data.get("garden_area_sqft", 0.0) or 0.0),
            status=data.get("status", Villa.STATUS_AVAILABLE),
            notes=data.get("notes", "").strip()
        )

        db.session.add(villa)
        self.commit_or_rollback()
        return villa

    def update_villa(self, villa_id_or_pk: int | str, data: Dict[str, Any]) -> Villa:
        """Update existing villa details and validate status transition."""
        villa = self.get_or_404(villa_id_or_pk)

        # Handle plot number change with uniqueness check
        new_plot = data.get("plot_number", "").strip().upper()
        if new_plot and new_plot != villa.plot_number:
            existing = Villa.query.filter_by(plot_number=new_plot).first()
            if existing and existing.id != villa.id:
                raise DuplicatePlotError(new_plot)
            villa.plot_number = new_plot

        if "villa_type" in data:
            villa.villa_type = data["villa_type"]
        if "built_up_area" in data:
            villa.built_up_area = float(data["built_up_area"])
        if "bedrooms" in data:
            villa.bedrooms = int(data["bedrooms"])
        if "bathrooms" in data:
            villa.bathrooms = int(data["bathrooms"])
        if "stories" in data:
            villa.stories = int(data["stories"])
        if "parking_slots" in data:
            villa.parking_slots = int(data["parking_slots"])
        if "has_private_pool" in data:
            villa.has_private_pool = bool(data["has_private_pool"])
        if "garden_area_sqft" in data:
            villa.garden_area_sqft = float(data["garden_area_sqft"] or 0.0)
        if "notes" in data:
            villa.notes = data["notes"].strip()

        # Encapsulated status change
        if "status" in data and data["status"] != villa.status:
            villa.change_status(data["status"])

        villa.validate()
        self.commit_or_rollback()
        return villa

    def get_community_stats(self) -> Dict[str, Any]:
        """Compute aggregated villa community metrics."""
        total = Villa.query.count()
        occupied = Villa.query.filter_by(status=Villa.STATUS_OCCUPIED).count()
        available = Villa.query.filter_by(status=Villa.STATUS_AVAILABLE).count()
        under_construction = Villa.query.filter_by(status=Villa.STATUS_UNDER_CONSTRUCTION).count()

        occupancy_rate = round((occupied / total * 100), 1) if total > 0 else 0.0

        return {
            "total_villas": total,
            "occupied_villas": occupied,
            "available_villas": available,
            "under_construction_villas": under_construction,
            "occupancy_rate": occupancy_rate,
        }
