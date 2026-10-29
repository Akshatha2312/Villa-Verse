from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import resident_service, villa_service
from app.models.villa import Villa
from app.models.member import CommunityMember, Owner, Resident
from app.forms.member_forms import OwnerForm, ResidentForm, AssignResidentForm
from app.exceptions import VillaVerseError

residents_bp = Blueprint("residents", __name__, url_prefix="/residents")

@residents_bp.route("/")
def index():
    """Directory of community owners and residents."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    member_type = request.args.get("type", "").strip()

    members, total_count, total_pages = resident_service.search_members(
        search_query=search_query,
        member_type=member_type,
        page=page,
        per_page=15
    )

    total_owners = CommunityMember.query.filter_by(member_type="owner").count()
    total_residents = CommunityMember.query.filter_by(member_type="resident").count()

    return render_template(
        "residents/index.html",
        members=members,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        search_query=search_query,
        member_type=member_type,
        total_owners=total_owners,
        total_residents=total_residents
    )

@residents_bp.route("/<int:member_id>")
def detail(member_id: int):
    """Detailed profile of a community member."""
    try:
        member = resident_service.get_or_404(member_id)
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("residents.index"))

    return render_template("residents/detail.html", member=member)

@residents_bp.route("/new-owner", methods=["GET", "POST"])
def new_owner():
    """Register a new property owner."""
    form = OwnerForm()
    if form.validate_on_submit():
        try:
            data = {
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "email": form.email.data,
                "phone": form.phone.data,
                "deed_number": form.deed_number.data,
                "emergency_contact": form.emergency_contact.data
            }
            owner = resident_service.register_owner(data)
            flash(f"Property Owner {owner.full_name} registered successfully!", "success")
            return redirect(url_for("residents.detail", member_id=owner.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("residents/form.html", form=form, title="Register Property Owner", member_type="owner")

@residents_bp.route("/new-resident", methods=["GET", "POST"])
def new_resident():
    """Register a new tenant resident."""
    form = ResidentForm()
    if form.validate_on_submit():
        try:
            data = {
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "email": form.email.data,
                "phone": form.phone.data,
                "lease_start_date": form.lease_start_date.data,
                "lease_end_date": form.lease_end_date.data,
                "is_primary_tenant": form.is_primary_tenant.data
            }
            resident = resident_service.register_resident(data)
            flash(f"Resident Tenant {resident.full_name} registered successfully!", "success")
            return redirect(url_for("residents.detail", member_id=resident.id))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("residents/form.html", form=form, title="Register Resident Tenant", member_type="resident")

@residents_bp.route("/assign", methods=["GET", "POST"])
def assign():
    """Assign a member to a villa."""
    form = AssignResidentForm()

    villas = Villa.query.order_by(Villa.villa_id.asc()).all()
    form.villa_id.choices = [(v.id, f"{v.villa_id} (Plot: {v.plot_number} - {v.status})") for v in villas]

    members = CommunityMember.query.order_by(CommunityMember.first_name.asc()).all()
    form.member_id.choices = [(m.id, f"{m.full_name} ({m.get_role_label()})") for m in members]

    pre_villa = request.args.get("villa_id", type=int)
    pre_member = request.args.get("member_id", type=int)
    if request.method == "GET":
        if pre_villa:
            form.villa_id.data = pre_villa
        if pre_member:
            form.member_id.data = pre_member

    if form.validate_on_submit():
        try:
            resident_service.assign_to_villa(
                villa_id=form.villa_id.data,
                member_id=form.member_id.data,
                role=form.role.data,
                is_primary=form.is_primary.data,
                move_in_date=form.move_in_date.data,
                notes=form.notes.data or ""
            )
            flash("Occupancy successfully assigned to villa!", "success")
            return redirect(url_for("villas.detail", villa_id=form.villa_id.data))
        except VillaVerseError as e:
            flash(e.message, "danger")

    return render_template("residents/assign.html", form=form)

@residents_bp.route("/occupancy/<int:occupancy_id>/vacate", methods=["POST"])
def vacate(occupancy_id: int):
    """Vacate an occupancy record."""
    reason = request.form.get("reason", "Lease concluded")
    try:
        occ = resident_service.vacate_occupancy(occupancy_id, reason=reason)
        flash(f"{occ.member.full_name} has vacated Villa {occ.villa.villa_id}.", "info")
        return redirect(url_for("villas.detail", villa_id=occ.villa_id))
    except VillaVerseError as e:
        flash(e.message, "danger")
        return redirect(url_for("residents.index"))
