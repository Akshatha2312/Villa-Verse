from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.services import villa_service, resident_service, maintenance_service
from app.models.villa import Villa
from app.forms.villa_forms import VillaForm
from app.exceptions import VillaVerseError

villas_bp = Blueprint("villas", __name__, url_prefix="/villas")

@villas_bp.route("/")
def index():
    """Directory of community villas with filtering, search, and pagination."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    type_filter = request.args.get("type", "").strip()
    sort_by = request.args.get("sort_by", "villa_id")
    sort_dir = request.args.get("sort_dir", "asc")

    per_page = current_app.config.get("ITEMS_PER_PAGE", 12)

    villas, total_count, total_pages = villa_service.search_and_filter(
        search_query=search_query,
        status=status_filter,
        villa_type=type_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        per_page=per_page
    )

    stats = villa_service.get_community_stats()

    return render_template(
        "villas/index.html",
        villas=villas,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        search_query=search_query,
        status_filter=status_filter,
        type_filter=type_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
        stats=stats,
        villa_types=Villa.VILLA_TYPES,
        statuses=Villa.ALLOWED_STATUSES
    )

@villas_bp.route("/<int:villa_id>")
def detail(villa_id: int):
    """Detailed profile of an individual villa."""
    try:
        villa = villa_service.get_or_404(villa_id)
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("villas.index"))

    return render_template("villas/detail.html", villa=villa)

@villas_bp.route("/new", methods=["GET", "POST"])
def create():
    """Register a new villa in the community."""
    form = VillaForm()
    if form.validate_on_submit():
        try:
            data = {
                "villa_id": form.villa_id.data,
                "plot_number": form.plot_number.data,
                "villa_type": form.villa_type.data,
                "built_up_area": form.built_up_area.data,
                "bedrooms": form.bedrooms.data,
                "bathrooms": form.bathrooms.data,
                "stories": form.stories.data,
                "parking_slots": form.parking_slots.data,
                "has_private_pool": form.has_private_pool.data,
                "garden_area_sqft": form.garden_area_sqft.data,
                "status": form.status.data,
                "notes": form.notes.data
            }
            villa = villa_service.create_villa(data)
            flash(f"Villa {villa.villa_id} (Plot {villa.plot_number}) registered successfully!", "success")
            return redirect(url_for("villas.detail", villa_id=villa.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("villas/form.html", form=form, title="Register New Villa", is_edit=False)

@villas_bp.route("/<int:villa_id>/edit", methods=["GET", "POST"])
def edit(villa_id: int):
    """Edit existing villa specifications."""
    try:
        villa = villa_service.get_or_404(villa_id)
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("villas.index"))

    form = VillaForm(obj=villa)

    if form.validate_on_submit():
        try:
            data = {
                "plot_number": form.plot_number.data,
                "villa_type": form.villa_type.data,
                "built_up_area": form.built_up_area.data,
                "bedrooms": form.bedrooms.data,
                "bathrooms": form.bathrooms.data,
                "stories": form.stories.data,
                "parking_slots": form.parking_slots.data,
                "has_private_pool": form.has_private_pool.data,
                "garden_area_sqft": form.garden_area_sqft.data,
                "status": form.status.data,
                "notes": form.notes.data
            }
            villa_service.update_villa(villa.id, data)
            flash(f"Villa {villa.villa_id} records updated successfully.", "success")
            return redirect(url_for("villas.detail", villa_id=villa.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("villas/form.html", form=form, title=f"Edit Villa {villa.villa_id}", is_edit=True, villa=villa)
