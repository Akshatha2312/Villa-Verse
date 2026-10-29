from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import maintenance_service, villa_service
from app.models.villa import Villa
from app.models.maintenance import MaintenanceRequest
from app.forms.maintenance_forms import MaintenanceRequestForm, MaintenanceUpdateForm
from app.exceptions import VillaVerseError

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")

@maintenance_bp.route("/")
def index():
    """Directory and filtering of maintenance requests."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    category_filter = request.args.get("category", "").strip()
    villa_id_filter = request.args.get("villa_id", type=int)

    requests, total_count, total_pages = maintenance_service.search_requests(
        search_query=search_query,
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        villa_id=villa_id_filter,
        page=page,
        per_page=15
    )

    stats = maintenance_service.get_summary_stats()
    urgent_tickets = maintenance_service.get_urgent_or_overdue()

    return render_template(
        "maintenance/index.html",
        requests=requests,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        search_query=search_query,
        status_filter=status_filter,
        priority_filter=priority_filter,
        category_filter=category_filter,
        stats=stats,
        urgent_tickets=urgent_tickets,
        categories=MaintenanceRequest.CATEGORIES,
        statuses=MaintenanceRequest.ALLOWED_STATUSES,
        priorities=MaintenanceRequest.ALLOWED_PRIORITIES
    )

@maintenance_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new maintenance work order."""
    form = MaintenanceRequestForm()
    villas = Villa.query.order_by(Villa.villa_id.asc()).all()
    form.villa_id.choices = [(v.id, f"{v.villa_id} (Plot: {v.plot_number})") for v in villas]

    pre_villa = request.args.get("villa_id", type=int)
    if request.method == "GET" and pre_villa:
        form.villa_id.data = pre_villa

    if form.validate_on_submit():
        try:
            data = {
                "villa_id": form.villa_id.data,
                "category": form.category.data,
                "title": form.title.data,
                "description": form.description.data,
                "priority": form.priority.data,
                "assigned_to": form.assigned_to.data
            }
            req = maintenance_service.create_request(data)
            flash(f"Work order {req.ticket_number} logged successfully!", "success")
            return redirect(url_for("maintenance.detail", ticket_id=req.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("maintenance/new.html", form=form)

@maintenance_bp.route("/<int:ticket_id>", methods=["GET", "POST"])
def detail(ticket_id: int):
    """View and update a maintenance request."""
    try:
        req = maintenance_service.get_or_404(ticket_id)
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("maintenance.index"))

    form = MaintenanceUpdateForm(obj=req)

    if form.validate_on_submit():
        try:
            maintenance_service.update_request(
                request_id=req.id,
                status=form.status.data,
                assigned_to=form.assigned_to.data,
                resolution_notes=form.resolution_notes.data,
                cost=form.cost.data
            )
            flash(f"Work order {req.ticket_number} updated successfully.", "success")
            return redirect(url_for("maintenance.detail", ticket_id=req.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("maintenance/detail.html", req=req, form=form)
