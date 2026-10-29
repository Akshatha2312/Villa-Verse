import pytest
from datetime import date, datetime, timezone, timedelta
from app.models.villa import Villa
from app.models.member import CommunityMember, Owner, Resident
from app.models.occupancy import VillaOccupancy
from app.models.maintenance import MaintenanceRequest
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord
from app.exceptions import (
    BusinessRuleViolationError,
    InvalidStatusTransitionError,
    InvalidPaymentError
)

class TestVillaModelOOP:
    """Tests OOP Encapsulation, Validation, and Computed Properties on Villa."""

    def test_villa_creation_and_properties(self, sample_villa):
        assert sample_villa.villa_id == "V-TEST-01"
        assert sample_villa.plot_number == "PL-TEST-01"
        assert sample_villa.built_up_area == 4500.0
        assert sample_villa.is_available is True
        assert sample_villa.is_occupied is False
        # Unit conversion property
        assert sample_villa.area_sqm == round(4500.0 * 0.092903, 2)

    def test_villa_invalid_built_up_area_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="positive number"):
            Villa.create_villa(
                villa_id="V-ERR",
                plot_number="PL-ERR",
                villa_type="The Royal Tuscan (5BHK)",
                built_up_area=-50.0
            )

    def test_villa_invalid_bedrooms_raises_error(self):
        with pytest.raises(BusinessRuleViolationError, match="at least 1 bedroom"):
            Villa.create_villa(
                villa_id="V-ERR",
                plot_number="PL-ERR",
                villa_type="The Grand Palm (4BHK)",
                built_up_area=3500.0,
                bedrooms=0
            )

    def test_villa_status_transition_encapsulation(self, sample_villa):
        # Valid transition: Available -> Occupied
        sample_villa.change_status(Villa.STATUS_OCCUPIED)
        assert sample_villa.status == Villa.STATUS_OCCUPIED
        assert sample_villa.is_occupied is True

        # Valid transition: Occupied -> Available
        sample_villa.change_status(Villa.STATUS_AVAILABLE)
        assert sample_villa.status == Villa.STATUS_AVAILABLE

        # Invalid transition to unknown status
        with pytest.raises(InvalidStatusTransitionError):
            sample_villa.change_status("Demolished")

    def test_villa_under_construction_cannot_be_occupied_directly(self, sample_villa):
        sample_villa.status = Villa.STATUS_UNDER_CONSTRUCTION
        with pytest.raises(InvalidStatusTransitionError, match="must first be marked Available"):
            sample_villa.change_status(Villa.STATUS_OCCUPIED)


class TestMemberInheritanceAndPolymorphism:
    """Tests OOP Inheritance and Polymorphic behavior of Owner and Resident."""

    def test_owner_polymorphic_methods(self, sample_owner):
        assert isinstance(sample_owner, CommunityMember)
        assert isinstance(sample_owner, Owner)
        assert sample_owner.full_name == "Arthur Pendelton"
        assert sample_owner.get_role_label() == "Property Owner"
        assert "bg-gold" in sample_owner.get_badge_class()
        # Polymorphic AGM voting rights: Owners vote
        assert sample_owner.can_vote_in_agm() is True
        assert "Owner: Arthur Pendelton" in sample_owner.format_summary()

    def test_resident_polymorphic_methods(self, sample_resident):
        assert isinstance(sample_resident, CommunityMember)
        assert isinstance(sample_resident, Resident)
        assert sample_resident.full_name == "Beatrice Vance"
        assert sample_resident.get_role_label() == "Resident Tenant"
        assert "bg-forest-light" in sample_resident.get_badge_class()
        # Polymorphic AGM voting rights: Tenants cannot vote on property matters
        assert sample_resident.can_vote_in_agm() is False
        assert "Resident: Beatrice Vance" in sample_resident.format_summary()

    def test_invalid_email_validation(self):
        with pytest.raises(BusinessRuleViolationError, match="Invalid email"):
            owner = Owner(first_name="Test", last_name="User", email="invalid-email", phone="1234567")
            owner.validate_contact_info()


class TestFeeChargeEncapsulation:
    """Tests financial transactions, balances, and payment validations."""

    def test_fee_charge_payment_application(self, db_session, sample_villa):
        charge = FeeCharge(
            invoice_number="INV-TEST-001",
            villa_id=sample_villa.id,
            period_month="2026-10",
            charge_type="Monthly Maintenance",
            amount=500.0,
            due_date=date(2026, 10, 15)
        )
        db_session.add(charge)
        db_session.commit()

        assert charge.balance == 500.0
        assert charge.status == FeeCharge.STATUS_UNPAID

        # Apply partial payment
        payment1 = charge.record_payment(amount=200.0, payment_method="Bank Wire Transfer")
        assert charge.total_paid == 200.0
        assert charge.balance == 300.0
        assert charge.status == FeeCharge.STATUS_PARTIAL

        # Apply remaining payment
        payment2 = charge.record_payment(amount=300.0, payment_method="Credit / Debit Card")
        assert charge.total_paid == 500.0
        assert charge.balance == 0.0
        assert charge.status == FeeCharge.STATUS_PAID

    def test_payment_exceeding_balance_raises_error(self, db_session, sample_villa):
        charge = FeeCharge(
            invoice_number="INV-TEST-002",
            villa_id=sample_villa.id,
            period_month="2026-10",
            amount=100.0,
            due_date=date(2026, 10, 15)
        )
        db_session.add(charge)
        db_session.commit()

        with pytest.raises(InvalidPaymentError, match="exceeds the outstanding balance"):
            charge.record_payment(amount=150.0, payment_method="Direct Cash Deposit")

    def test_negative_payment_raises_error(self, db_session, sample_villa):
        charge = FeeCharge(
            invoice_number="INV-TEST-003",
            villa_id=sample_villa.id,
            period_month="2026-10",
            amount=100.0,
            due_date=date(2026, 10, 15)
        )
        db_session.add(charge)
        db_session.commit()

        with pytest.raises(InvalidPaymentError, match="greater than zero"):
            charge.record_payment(amount=-50.0, payment_method="Bank Wire Transfer")


class TestMaintenanceRequestLifecycle:
    """Tests maintenance state machine, assignment, and resolution."""

    def test_maintenance_ticket_resolution(self, db_session, sample_villa):
        ticket = MaintenanceRequest(
            ticket_number="REQ-TEST-001",
            villa_id=sample_villa.id,
            category="Plumbing",
            title="Main line leakage",
            description="High pressure pipe burst near outer perimeter wall.",
            priority=MaintenanceRequest.PRIORITY_URGENT,
            status=MaintenanceRequest.STATUS_OPEN
        )
        db_session.add(ticket)
        db_session.commit()

        assert ticket.is_urgent is True
        assert ticket.status == MaintenanceRequest.STATUS_OPEN

        # Assign technician transitions to In Progress
        ticket.assign_technician("Apex Contractors")
        assert ticket.assigned_to == "Apex Contractors"
        assert ticket.status == MaintenanceRequest.STATUS_IN_PROGRESS

        # Resolve ticket
        ticket.resolve(resolution_notes="Pipe welded and pressure tested to 6 bar.", cost=350.0)
        assert ticket.status == MaintenanceRequest.STATUS_RESOLVED
        assert ticket.is_resolved is True
        assert ticket.cost == 350.0
        assert ticket.resolved_date is not None
