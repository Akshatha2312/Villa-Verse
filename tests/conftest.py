import pytest
from datetime import date, datetime, timezone
from app import create_app
from app.extensions import db
from app.models.villa import Villa
from app.models.member import Owner, Resident
from app.models.occupancy import VillaOccupancy
from app.models.maintenance import MaintenanceRequest
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask test application instance with in-memory database."""
    test_app = create_app("testing")
    return test_app

@pytest.fixture(scope="function")
def client(app):
    """Flask HTTP test client."""
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    """Set up and tear down a pristine database schema for each test."""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()

@pytest.fixture
def sample_villa(db_session):
    """Fixture providing a standard testing Villa."""
    villa = Villa.create_villa(
        villa_id="V-TEST-01",
        plot_number="PL-TEST-01",
        villa_type="The Grand Palm (4BHK)",
        built_up_area=4500.0,
        bedrooms=4,
        bathrooms=5,
        stories=2,
        has_private_pool=True,
        garden_area_sqft=1500.0,
        status=Villa.STATUS_AVAILABLE
    )
    db.session.add(villa)
    db.session.commit()
    return villa

@pytest.fixture
def sample_owner(db_session):
    """Fixture providing a registered property owner."""
    owner = Owner(
        first_name="Arthur",
        last_name="Pendelton",
        email="arthur.pendelton@test.com",
        phone="+15551234567",
        deed_number="DEED-TEST-99"
    )
    owner.validate_contact_info()
    db.session.add(owner)
    db.session.commit()
    return owner

@pytest.fixture
def sample_resident(db_session):
    """Fixture providing a registered resident tenant."""
    res = Resident(
        first_name="Beatrice",
        last_name="Vance",
        email="beatrice.vance@test.com",
        phone="+15559876543",
        lease_start_date=date(2026, 1, 1),
        lease_end_date=date(2027, 1, 1),
        is_primary_tenant=True
    )
    res.validate_contact_info()
    db.session.add(res)
    db.session.commit()
    return res
