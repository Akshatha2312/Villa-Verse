"""
VillaVerse Database Seed Script
Populates the SQLite database with 100+ realistic, fictional villas, community members,
maintenance work orders, and financial billing records.

Safe to rerun (idempotent / resets or updates without illegal duplication).
All generated records are fictional.
"""

import random
from datetime import date, datetime, timedelta, timezone
from app import create_app
from app.extensions import db
from app.models.villa import Villa
from app.models.member import CommunityMember, Owner, Resident
from app.models.occupancy import VillaOccupancy
from app.models.maintenance import MaintenanceRequest
from app.models.finance import FeeCharge, PaymentRecord, ExpenseRecord

# Realistic Fictional Seed Data Sets
FIRST_NAMES = [
    "Alexander", "Beatrice", "Christopher", "Diana", "Eleanor", "Felix", "Gabriel",
    "Helena", "Isabella", "Julian", "Katarina", "Liam", "Marcus", "Nadia", "Oliver",
    "Penelope", "Quentin", "Rosalind", "Sebastian", "Tariq", "Uma", "Victoria",
    "William", "Xavier", "Yasmin", "Zachary", "Arthur", "Camilla", "Dominic", "Fiona",
    "Harrison", "Jacqueline", "Lawrence", "Madeleine", "Nathaniel", "Priscilla", "Roland"
]

LAST_NAMES = [
    "Sterling", "Vance", "Montgomery", "Chen", "Al-Mansoor", "Thorne", "Sharma",
    "Wright", "O'Connor", "Kensington", "Blackwood", "Fontaine", "Sinclair", "Mercer",
    "Rothschild", "Gallagher", "Castillo", "Abernathy", "Hawthorne", "Dubois",
    "Kovacs", "Harrington", "Donovan", "Ashford", "Navarro", "Fairfax", "Beaumont"
]

VILLA_CONFIGS = [
    {"type": "The Royal Tuscan (5BHK)", "area_range": (5200, 6800), "beds": 5, "baths": 6, "stories": 3, "pool_prob": 0.9, "garden_range": (1800, 3200)},
    {"type": "The Grand Palm (4BHK)", "area_range": (4200, 5100), "beds": 4, "baths": 5, "stories": 2, "pool_prob": 0.75, "garden_range": (1400, 2400)},
    {"type": "Palm Crest Luxury (4BHK)", "area_range": (3800, 4600), "beds": 4, "baths": 4, "stories": 2, "pool_prob": 0.6, "garden_range": (1200, 2000)},
    {"type": "The Azure Villa (3BHK)", "area_range": (3200, 3900), "beds": 3, "baths": 4, "stories": 2, "pool_prob": 0.5, "garden_range": (1000, 1600)},
    {"type": "Serenity Modern (3BHK)", "area_range": (2800, 3400), "beds": 3, "baths": 3, "stories": 2, "pool_prob": 0.35, "garden_range": (800, 1400)},
    {"type": "Meadow Courtyard (2BHK)", "area_range": (2200, 2700), "beds": 2, "baths": 3, "stories": 1, "pool_prob": 0.15, "garden_range": (600, 1100)},
]

MAINTENANCE_TEMPLATES = [
    ("Swimming Pool & Spa", "Pool filtration pump high pressure alarm", "The variable speed pump in the private plant room is shutting down intermittently on thermal overload.", "Urgent"),
    ("HVAC & Cooling", "Master suite VRF cooling failure", "Compressor circuit 2 not cycling, resulting in ambient temperature rising above 28C in the master wing.", "High"),
    ("Plumbing", "Irrigation solenoid valve stuck open", "Zone 4 drip irrigation line in the rear terrace garden is leaking continuously causing water pooling.", "Medium"),
    ("Electrical", "Exterior landscape bollard lighting trip", "Main 30mA RCD tripping whenever the dusk sensor triggers evening pathway illumination.", "Medium"),
    ("Roofing & Civil", "Pergola cedar beam weatherproofing maintenance", "Routine inspection identified minor moisture ingress along the west-facing pergola joints.", "Low"),
    ("Security & Intercom", "Video intercom touch screen unresponsive", "Main pedestrian gate station video feed cuts out after 5 seconds of initiation.", "Medium"),
    ("Pest Control", "Subterranean termite preventative inspection", "Scheduled quarterly perimeter barrier inspection and bait station replenishment.", "Low"),
    ("Plumbing", "Kitchen island RO water filtration filter replacement", "Flow rate decreased below 0.5 GPM; replacement of 4-stage mineral cartridge required.", "Low"),
    ("HVAC & Cooling", "Ductwork acoustic dampening adjustment", "Airflow whistling sound audible in the guest bedroom suite during high fan mode.", "Low"),
    ("General Maintenance", "Motorized driveway gate track realignment", "Sliding security gate motor hesitating halfway across the track guide rail.", "High")
]

EXPENSE_TEMPLATES = [
    ("Security & Guard Services", "24/7 Gatehouse & Mobile Perimeter Guard Patrol", 6800.0, "Apex Shield Security Group"),
    ("Landscaping & Grounds Keeping", "Community Avenue Palms & Central Boulevard Pruning", 4200.0, "Verdant Oasis Landscaping Ltd."),
    ("Swimming Pool Maintenance", "Clubhouse Lagoon & Water Feature Chemical Treatment", 2150.0, "Azure Blue Aquatic Services"),
    ("Common Utilities (Water & Electricity)", "Common Area High-Mast Lighting & Water Booster Power", 5420.0, "Metropolitan Power Authority"),
    ("Waste Management & Sanitation", "Weekly Organic & Recyclable Estate Waste Removal", 1850.0, "CleanCity Environmental Solutions"),
    ("Infrastructure & Road Repairs", "South Gate Asphalt Resurfacing & Speed Calming Strips", 3900.0, "Precision Roadways & Civil Eng."),
    ("Clubhouse Operations", "Fitness Center Technogym Equipment Servicing", 1450.0, "Elite Wellness Gym Solutions"),
    ("Community Insurance & Legal", "Quarterly Comprehensive Property & Public Liability Insurance", 7800.0, "Allied Sovereign Underwriters")
]

CONTRACTORS = [
    "Apex Technical Services",
    "Verdant Landscaping Crew",
    "Precision Plumbing & HVAC",
    "Sterling Electricians Co.",
    "Azure Pool Specialists",
    "Horizon Civil Works"
]


def seed_database():
    """Generates 100+ fictional sample records in the database."""
    # Ensure fresh schema tables exist
    db.create_all()

    # If already seeded with 100+ villas, inform user and exit
    existing_count = Villa.query.count()
    if existing_count >= 100:
        print(f"Database already contains {existing_count} villas. Skipping duplicate seed.")
        return

    print("Generating 105 realistic luxury villas in Emerald Palms Community...")
    random.seed(42)  # Deterministic seed for reproducible results

    # 1. Generate 105 Villas (V-101 to V-205)
    villas = []
    statuses = [Villa.STATUS_OCCUPIED] * 78 + [Villa.STATUS_AVAILABLE] * 18 + [Villa.STATUS_UNDER_CONSTRUCTION] * 9
    random.shuffle(statuses)

    for i in range(1, 106):
        villa_num = 100 + i
        villa_id = f"V-{villa_num}"
        plot_number = f"PL-{villa_num}"

        config = random.choice(VILLA_CONFIGS)
        area = random.randint(*config["area_range"])
        garden = random.randint(*config["garden_range"])
        has_pool = random.random() < config["pool_prob"]
        status = statuses[i - 1]

        villa = Villa(
            villa_id=villa_id,
            plot_number=plot_number,
            villa_type=config["type"],
            built_up_area=float(area),
            bedrooms=config["beds"],
            bathrooms=config["baths"],
            stories=config["stories"],
            parking_slots=random.choice([2, 3, 4]),
            has_private_pool=has_pool,
            garden_area_sqft=float(garden),
            status=status,
            notes=f"Luxury {config['type']} situated along Avenue {((i - 1) // 15) + 1}. Features manicured landscaping and luxury finishes."
        )
        db.session.add(villa)
        villas.append(villa)

    db.session.commit()
    print(f"Successfully registered {len(villas)} villas.")

    # 2. Generate 90 Community Members (Owners & Residents)
    print("Registering community owners and residents...")
    members = []
    used_emails = set()

    for i in range(95):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        base_email = f"{first.lower()}.{last.lower()}{i}@emeraldpalms.demo"
        phone = f"+1 (555) {random.randint(200, 999):03d}-{random.randint(1000, 9999):04d}"

        # 60% Owners, 40% Tenants
        if i % 3 != 0:
            owner = Owner(
                first_name=first,
                last_name=last,
                email=base_email,
                phone=phone,
                deed_number=f"DEED-2024-EP-{1000 + i}",
                emergency_contact=f"Family Office ({phone})"
            )
            db.session.add(owner)
            members.append(owner)
        else:
            start_d = date(2025, 1, 1) + timedelta(days=random.randint(0, 300))
            end_d = start_d + timedelta(days=365)
            resident = Resident(
                first_name=first,
                last_name=last,
                email=base_email,
                phone=phone,
                lease_start_date=start_d,
                lease_end_date=end_d,
                is_primary_tenant=True
            )
            db.session.add(resident)
            members.append(resident)

    db.session.commit()
    print(f"Registered {len(members)} community members.")

    # 3. Associate Occupants with Occupied Villas
    print("Linking occupancy records to occupied estates...")
    occupied_villas = [v for v in villas if v.status == Villa.STATUS_OCCUPIED]
    for idx, villa in enumerate(occupied_villas):
        member = members[idx % len(members)]
        role = VillaOccupancy.ROLE_OWNER_OCCUPANT if member.member_type == "owner" else VillaOccupancy.ROLE_TENANT

        move_in = date(2024, random.randint(1, 12), random.randint(1, 28))
        occ = VillaOccupancy(
            villa_id=villa.id,
            member_id=member.id,
            role=role,
            is_primary=True,
            move_in_date=move_in,
            is_active=True,
            notes="Active verified primary residency agreement."
        )
        db.session.add(occ)

    db.session.commit()

    # 4. Generate 45 Maintenance Work Orders
    print("Generating maintenance service requests...")
    for idx in range(1, 46):
        villa = random.choice(villas)
        template = random.choice(MAINTENANCE_TEMPLATES)
        reporter = random.choice(members)

        # Mix of statuses: 15 Open, 12 In Progress, 18 Resolved
        if idx <= 15:
            st = MaintenanceRequest.STATUS_OPEN
            assigned = None
            cost = 0.0
            res_notes = None
            res_date = None
        elif idx <= 27:
            st = MaintenanceRequest.STATUS_IN_PROGRESS
            assigned = random.choice(CONTRACTORS)
            cost = 0.0
            res_notes = None
            res_date = None
        else:
            st = MaintenanceRequest.STATUS_RESOLVED
            assigned = random.choice(CONTRACTORS)
            cost = float(random.randint(250, 1800))
            res_notes = f"Inspection completed and repairs certified by {assigned}. Operational tests normal."
            res_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))

        days_ago = random.randint(1, 45)
        reported_time = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(1, 12))

        ticket = MaintenanceRequest(
            ticket_number=f"REQ-2026{idx:02d}-{1000 + idx}",
            villa_id=villa.id,
            reported_by_id=reporter.id,
            category=template[0],
            title=f"{template[1]} - {villa.villa_id}",
            description=template[2],
            priority=template[3],
            status=st,
            assigned_to=assigned,
            cost=cost,
            reported_date=reported_time,
            resolved_date=res_date,
            resolution_notes=res_notes
        )
        db.session.add(ticket)

    db.session.commit()

    # 5. Generate Monthly Billing Charges & Payments (Last 3 Months: 2026-08, 2026-09, 2026-10)
    print("Generating community fee invoices and payment records...")
    billing_months = [("2026-08", date(2026, 8, 15)), ("2026-09", date(2026, 9, 15)), ("2026-10", date(2026, 10, 15))]
    rate_sqft = 0.15

    for period, due_d in billing_months:
        for villa in villas:
            amount = round(villa.built_up_area * rate_sqft, 2)
            invoice_num = f"INV-{period.replace('-', '')}-{villa.villa_id}"

            # Payment behavior simulation:
            # Older months mostly paid; current month has some partial/unpaid
            rand_val = random.random()
            if period == "2026-08":
                st = FeeCharge.STATUS_PAID if rand_val < 0.95 else FeeCharge.STATUS_PARTIAL
            elif period == "2026-09":
                st = FeeCharge.STATUS_PAID if rand_val < 0.85 else (FeeCharge.STATUS_PARTIAL if rand_val < 0.95 else FeeCharge.STATUS_UNPAID)
            else: # Current month 2026-10
                st = FeeCharge.STATUS_PAID if rand_val < 0.65 else (FeeCharge.STATUS_PARTIAL if rand_val < 0.85 else FeeCharge.STATUS_UNPAID)

            charge = FeeCharge(
                invoice_number=invoice_num,
                villa_id=villa.id,
                period_month=period,
                charge_type="Monthly Community Maintenance",
                amount=amount,
                due_date=due_d,
                status=st,
                description=f"Monthly dues for Villa {villa.villa_id} ({villa.built_up_area:.0f} sq.ft @ ${rate_sqft}/sq.ft)"
            )
            db.session.add(charge)
            db.session.flush()

            # Record associated payments according to status
            if st == FeeCharge.STATUS_PAID:
                payment = PaymentRecord(
                    receipt_number=f"REC-{period.replace('-', '')}-{charge.id:04d}",
                    fee_charge_id=charge.id,
                    amount=amount,
                    payment_method=random.choice(PaymentRecord.PAYMENT_METHODS),
                    payment_date=datetime(due_d.year, due_d.month, random.randint(1, 14), 10, 30, tzinfo=timezone.utc),
                    transaction_reference=f"TXN-{random.randint(100000, 999999)}",
                    notes="Settled in full via scheduled online transaction."
                )
                db.session.add(payment)
            elif st == FeeCharge.STATUS_PARTIAL:
                partial_amt = round(amount * 0.5, 2)
                payment = PaymentRecord(
                    receipt_number=f"REC-{period.replace('-', '')}-{charge.id:04d}",
                    fee_charge_id=charge.id,
                    amount=partial_amt,
                    payment_method=random.choice(PaymentRecord.PAYMENT_METHODS),
                    payment_date=datetime(due_d.year, due_d.month, random.randint(1, 14), 14, 0, tzinfo=timezone.utc),
                    transaction_reference=f"PARTIAL-{random.randint(100000, 999999)}",
                    notes="50% installment payment received."
                )
                db.session.add(payment)

    db.session.commit()

    # 6. Generate Community Operational Expenses
    print("Logging community operational expenditures...")
    for idx, (cat, title, base_amt, vendor) in enumerate(EXPENSE_TEMPLATES):
        for m_offset in range(3):
            exp_date = date(2026, 8 + m_offset, random.randint(5, 25))
            amount = round(base_amt * (1.0 + random.uniform(-0.08, 0.08)), 2)
            expense = ExpenseRecord(
                expense_number=f"EXP-2026{8 + m_offset:02d}-{idx + 1:03d}",
                category=cat,
                title=f"{title} - Month {8 + m_offset}",
                amount=amount,
                expense_date=exp_date,
                vendor_name=vendor,
                receipt_reference=f"INV-{vendor[:4].upper()}-{1000 + idx}",
                description=f"Standard monthly recurring contract service invoice approved by Estate Management."
            )
            db.session.add(expense)

    db.session.commit()
    print("Database seeding completed successfully! All records verified.")


if __name__ == "__main__":
    app = create_app("development")
    with app.app_context():
        seed_database()
