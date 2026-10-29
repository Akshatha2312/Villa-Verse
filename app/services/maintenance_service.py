from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy import or_, desc
from app.extensions import db
from app.models.maintenance import MaintenanceRequest
from app.models.villa import Villa
from app.services.base import BaseService
from app.exceptions import EntityNotFoundError, VillaNotFoundError, BusinessRuleViolationError

class MaintenanceService(BaseService[MaintenanceRequest]):
    """
    Service layer for maintenance operations and ticket lifecycles.
    Demonstrates OOP:
      - Encapsulates ticket number generation
      - Enforces SLA inspection and status transitions
    """

    def get_by_id(self, entity_id: int) -> Optional[MaintenanceRequest]:
        return db.session.get(MaintenanceRequest, entity_id)

    def get_by_ticket(self, ticket_number: str) -> Optional[MaintenanceRequest]:
        return MaintenanceRequest.query.filter_by(ticket_number=ticket_number.strip().upper()).first()

    def get_or_404(self, identifier: int | str) -> MaintenanceRequest:
        req = None
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            req = self.get_by_id(int(identifier))
        if not req and isinstance(identifier, str):
            req = self.get_by_ticket(identifier)

        if not req:
            raise EntityNotFoundError("MaintenanceRequest", identifier)
        return req

    def list_all(self, **filters) -> List[MaintenanceRequest]:
        query = MaintenanceRequest.query
        if "status" in filters and filters["status"]:
            query = query.filter_by(status=filters["status"])
        if "villa_id" in filters and filters["villa_id"]:
            query = query.filter_by(villa_id=filters["villa_id"])
        return query.order_by(MaintenanceRequest.reported_date.desc()).all()

    def search_requests(
        self,
        search_query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        villa_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 15
    ) -> Tuple[List[MaintenanceRequest], int, int]:
        """Search and paginate maintenance work orders."""
        query = MaintenanceRequest.query

        if search_query:
            q = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    MaintenanceRequest.ticket_number.ilike(q),
                    MaintenanceRequest.title.ilike(q),
                    MaintenanceRequest.description.ilike(q),
                    MaintenanceRequest.assigned_to.ilike(q)
                )
            )

        if status:
            query = query.filter(MaintenanceRequest.status == status)
        if priority:
            query = query.filter(MaintenanceRequest.priority == priority)
        if category:
            query = query.filter(MaintenanceRequest.category == category)
        if villa_id:
            query = query.filter(MaintenanceRequest.villa_id == villa_id)

        query = query.order_by(MaintenanceRequest.reported_date.desc())
        total_count = query.count()
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total_count, total_pages

    def create_request(self, data: Dict[str, Any]) -> MaintenanceRequest:
        """Create a new maintenance request with auto-generated ticket ID."""
        villa_id = data.get("villa_id")
        villa = db.session.get(Villa, villa_id)
        if not villa:
            raise VillaNotFoundError(villa_id)

        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        if not title:
            raise BusinessRuleViolationError("Request title is required.")
        if not description:
            raise BusinessRuleViolationError("Request description is required.")

        category = data.get("category", "General Maintenance")
        priority = data.get("priority", MaintenanceRequest.PRIORITY_MEDIUM)

        # Generate unique sequential ticket number: REQ-YYYYMM-XXXX
        year_month = datetime.now().strftime("%Y%m")
        count = MaintenanceRequest.query.count() + 1
        ticket_number = f"REQ-{year_month}-{count:04d}"

        request = MaintenanceRequest(
            ticket_number=ticket_number,
            villa_id=villa.id,
            reported_by_id=data.get("reported_by_id"),
            category=category,
            title=title,
            description=description,
            priority=priority,
            status=MaintenanceRequest.STATUS_OPEN,
            assigned_to=data.get("assigned_to", "").strip() or None
        )

        if request.assigned_to:
            request.status = MaintenanceRequest.STATUS_IN_PROGRESS

        db.session.add(request)
        self.commit_or_rollback()
        return request

    def update_request(
        self,
        request_id: int,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        cost: Optional[float] = None
    ) -> MaintenanceRequest:
        """Update request state and lifecycle."""
        req = self.get_or_404(request_id)

        if assigned_to is not None:
            assigned = assigned_to.strip()
            if assigned:
                req.assign_technician(assigned)

        if status:
            if status == MaintenanceRequest.STATUS_RESOLVED:
                req.resolve(
                    resolution_notes=resolution_notes or req.resolution_notes or "Resolved per inspection.",
                    cost=float(cost if cost is not None else req.cost)
                )
            elif status == MaintenanceRequest.STATUS_CANCELLED:
                req.cancel(reason=resolution_notes or "Cancelled by management")
            elif status in (MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS):
                req.status = status

        self.commit_or_rollback()
        return req

    def get_urgent_or_overdue(self) -> List[MaintenanceRequest]:
        """Fetch open or in-progress requests flagged as Urgent or Overdue."""
        active = MaintenanceRequest.query.filter(
            MaintenanceRequest.status.in_([MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS])
        ).order_by(MaintenanceRequest.reported_date.asc()).all()

        return [req for req in active if req.is_urgent or req.is_overdue]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Aggregate stats for maintenance dashboard."""
        total = MaintenanceRequest.query.count()
        open_count = MaintenanceRequest.query.filter_by(status=MaintenanceRequest.STATUS_OPEN).count()
        in_progress = MaintenanceRequest.query.filter_by(status=MaintenanceRequest.STATUS_IN_PROGRESS).count()
        resolved = MaintenanceRequest.query.filter_by(status=MaintenanceRequest.STATUS_RESOLVED).count()
        urgent_open = MaintenanceRequest.query.filter(
            MaintenanceRequest.status.in_([MaintenanceRequest.STATUS_OPEN, MaintenanceRequest.STATUS_IN_PROGRESS]),
            MaintenanceRequest.priority == MaintenanceRequest.PRIORITY_URGENT
        ).count()

        total_costs = db.session.query(db.func.sum(MaintenanceRequest.cost)).scalar() or 0.0

        return {
            "total_requests": total,
            "open_requests": open_count,
            "in_progress_requests": in_progress,
            "resolved_requests": resolved,
            "urgent_active_requests": urgent_open,
            "total_maintenance_expenditure": round(total_costs, 2)
        }
