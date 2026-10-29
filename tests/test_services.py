import pytest
from datetime import date
from app.services import (
    villa_service,
    resident_service,
    maintenance_service,
    finance_service,
    report_service
)
from app.models.villa import Villa
from app.models.member import Owner, Resident
from app.models.finance import FeeCharge
from app.models.maintenance import MaintenanceRequest
from app.exceptions import (
    DuplicateVillaIdError,
    DuplicatePlotError,
    ResidentAssignmentError,
    VillaNotFoundError
)

class TestVillaService:
    def test_create_and_reject_duplicates(self, db_session):
        data = {
            "villa_id": "V-500",
            "plot_number": "PL-500",
            "villa_type": "The Royal Tuscan (5BHK)",
            "built_up_area": 5500.0,
            "bedrooms": 5,
            "bathrooms": 6,
            "stories": 3
        }
        v = villa_service.create_villa(data)
        assert v.id is not None
        assert v.villa_id == "V-500"

        # Re-creating same villa_id must raise DuplicateVillaIdError
        with pytest.raises(DuplicateVillaIdError):
            villa_service.create_villa(data)

        # Re-creating different villa_id with same plot_number must raise DuplicatePlotError
        data2 = dict(data, villa_id="V-501")
        with pytest.raises(DuplicatePlotError):
            villa_service.create_villa(data2)

    def test_search_and_filter(self, db_session, sample_villa):
        results, count, pages = villa_service.search_and_filter(search_query="TEST-01")
        assert count == 1
        assert results[0].villa_id == "V-TEST-01"

        # Filter by status
        results, count, pages = villa_service.search_and_filter(status=Villa.STATUS_OCCUPIED)
        assert count == 0


class TestResidentService:
    def test_assign_occupant_and_auto_transition(self, db_session, sample_villa, sample_owner):
        assert sample_villa.status == Villa.STATUS_AVAILABLE

        occ = resident_service.assign_to_villa(
            villa_id=sample_villa.id,
            member_id=sample_owner.id,
            role="Owner-Occupant",
            is_primary=True
        )
        assert occ.is_active is True
        # Villa must automatically transition to Occupied
        assert sample_villa.status == Villa.STATUS_OCCUPIED
        assert sample_villa.primary_resident.id == sample_owner.id

    def test_cannot_assign_to_under_construction_villa(self, db_session, sample_villa, sample_owner):
        sample_villa.status = Villa.STATUS_UNDER_CONSTRUCTION
        db_session.commit()

        with pytest.raises(ResidentAssignmentError, match="Under Construction"):
            resident_service.assign_to_villa(
                villa_id=sample_villa.id,
                member_id=sample_owner.id,
                role="Owner-Occupant"
            )

    def test_vacate_occupant_reverts_villa_to_available(self, db_session, sample_villa, sample_owner):
        occ = resident_service.assign_to_villa(
            villa_id=sample_villa.id,
            member_id=sample_owner.id,
            role="Owner-Occupant"
        )
        assert sample_villa.status == Villa.STATUS_OCCUPIED

        # Vacate
        resident_service.vacate_occupancy(occ.id, reason="Owner relocated abroad")
        assert occ.is_active is False
        assert occ.move_out_date is not None
        # Villa should revert to Available
        assert sample_villa.status == Villa.STATUS_AVAILABLE


class TestMaintenanceService:
    def test_create_and_resolve_request(self, db_session, sample_villa):
        ticket_data = {
            "villa_id": sample_villa.id,
            "category": "Electrical",
            "title": "Circuit breaker tripping",
            "description": "Kitchen sub-panel main trip during oven operation.",
            "priority": MaintenanceRequest.PRIORITY_HIGH,
            "assigned_to": "Sterling Electricians Co."
        }
        req = maintenance_service.create_request(ticket_data)
        assert req.ticket_number.startswith("REQ-")
        assert req.status == MaintenanceRequest.STATUS_IN_PROGRESS

        # Resolve ticket
        updated = maintenance_service.update_request(
            request_id=req.id,
            status=MaintenanceRequest.STATUS_RESOLVED,
            resolution_notes="Oven heating element replaced and calibrated.",
            cost=240.0
        )
        assert updated.status == MaintenanceRequest.STATUS_RESOLVED
        assert updated.cost == 240.0


class TestFinanceService:
    def test_generate_monthly_charges_proportional_to_sqft(self, db_session, sample_villa):
        # sample_villa is 4500 sq ft, rate 0.15/sq.ft => ₹675
        count = finance_service.generate_monthly_charges(period_month="2026-10", rate_per_sqft=0.15)
        assert count == 1

        charges = FeeCharge.query.filter_by(villa_id=sample_villa.id, period_month="2026-10").all()
        assert len(charges) == 1
        assert charges[0].amount == 675.0
        assert charges[0].balance == 675.0

        # Idempotency check: running again for same month must generate 0 new charges
        count2 = finance_service.generate_monthly_charges(period_month="2026-10", rate_per_sqft=0.15)
        assert count2 == 0

    def test_record_expense_and_summary(self, db_session):
        exp_data = {
            "category": "Security & Guard Services",
            "title": "Perimeter Patrol",
            "amount": 2500.0,
            "vendor_name": "Apex Shield",
            "expense_date": "2026-10-01"
        }
        exp = finance_service.add_expense(exp_data)
        assert exp.id is not None
        assert exp.amount == 2500.0

        summary = finance_service.get_financial_summary()
        assert summary["total_expenses"] == 2500.0


class TestReportService:
    def test_csv_exports(self, db_session, sample_villa):
        charge = FeeCharge(
            invoice_number="INV-202610-V-TEST-01",
            villa_id=sample_villa.id,
            period_month="2026-10",
            amount=150000.0,
            due_date=date(2026, 10, 31),
            status=FeeCharge.STATUS_UNPAID
        )
        ticket = MaintenanceRequest(
            ticket_number="REQ-TEST-01",
            villa_id=sample_villa.id,
            category="Electrical",
            title="Electrical panel repair",
            description="Repair a faulty electrical panel.",
            priority=MaintenanceRequest.PRIORITY_HIGH,
            status=MaintenanceRequest.STATUS_RESOLVED,
            cost=25000.0
        )
        db_session.add_all([charge, ticket])
        db_session.commit()

        villas_csv = report_service.export_villas_csv()
        assert "Villa ID,Plot Number" in villas_csv
        assert "V-TEST-01" in villas_csv
        assert "Outstanding Balance (INR)" in villas_csv
        assert "₹1,50,000" in villas_csv

        maint_csv = report_service.export_maintenance_csv()
        assert "Ticket Number,Villa ID" in maint_csv
        assert "Cost (INR)" in maint_csv
        assert "₹25,000" in maint_csv

        fin_csv = report_service.export_finance_csv()
        assert "Invoice Number,Villa ID" in fin_csv
        assert "Invoiced Amount (INR)" in fin_csv
        assert "₹1,50,000" in fin_csv
