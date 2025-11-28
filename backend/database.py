"""Database connection and session management."""

import os
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import (
    Base,
    Member,
    Benefit,
    MilitaryBranch,
    MembershipStatus,
    BenefitCategory,
)


# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://membercenter:membercenter_password@localhost:5432/membercenter",
)

# Create synchronous engine
engine = create_engine(DATABASE_URL, echo=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def seed_demo_data(db: Session):
    """Seed the database with demo data."""

    # Check if data already exists
    existing_members = db.query(Member).first()
    if existing_members:
        return

    # Create demo benefits
    benefits = [
        Benefit(
            name="Service Members' Group Life Insurance (SGLI)",
            description="Primary life insurance coverage for active duty service members. Provides financial protection for your family with competitive rates available only to military personnel.",
            category=BenefitCategory.LIFE_INSURANCE,
            coverage_amount=400000.00,
            monthly_premium=25.00,
            deductible=0,
            min_age=18,
            max_age=65,
            requires_active_duty=True,
            plan_code="SGLI-400",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Family Service Members' Group Life Insurance (FSGLI)",
            description="Life insurance coverage for spouses and dependent children of service members. Protect your entire family with affordable coverage.",
            category=BenefitCategory.LIFE_INSURANCE,
            coverage_amount=100000.00,
            monthly_premium=15.00,
            deductible=0,
            min_age=18,
            max_age=65,
            requires_active_duty=False,
            plan_code="FSGLI-100",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Veterans' Group Life Insurance (VGLI)",
            description="Renewable term life insurance for veterans. Continue your coverage after separation from service with no medical exam required within 240 days of discharge.",
            category=BenefitCategory.LIFE_INSURANCE,
            coverage_amount=250000.00,
            monthly_premium=35.00,
            deductible=0,
            min_age=18,
            max_age=75,
            requires_active_duty=False,
            plan_code="VGLI-250",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Service-Disabled Veterans Insurance (S-DVI)",
            description="Life insurance for veterans with service-connected disabilities. Available to veterans who receive a service-connected disability rating.",
            category=BenefitCategory.LIFE_INSURANCE,
            coverage_amount=10000.00,
            monthly_premium=8.00,
            deductible=0,
            min_age=18,
            max_age=70,
            requires_active_duty=False,
            plan_code="SDVI-10",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Military Disability Protection Plus",
            description="Comprehensive disability coverage providing income replacement if you become unable to serve due to injury or illness. Covers both service-related and non-service-related disabilities.",
            category=BenefitCategory.DISABILITY,
            coverage_amount=5000.00,
            monthly_premium=45.00,
            deductible=250,
            min_age=18,
            max_age=60,
            requires_active_duty=True,
            plan_code="MDP-PLUS",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Accident Protection Plan",
            description="Coverage for accidental injuries during active duty or civilian life. Includes benefits for hospitalization, emergency care, and rehabilitation.",
            category=BenefitCategory.ACCIDENT,
            coverage_amount=50000.00,
            monthly_premium=12.00,
            deductible=100,
            min_age=18,
            max_age=65,
            requires_active_duty=False,
            plan_code="APP-50",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Critical Illness Shield",
            description="Lump-sum payment upon diagnosis of covered critical illnesses including cancer, heart attack, and stroke. Use the funds for treatment, bills, or any purpose.",
            category=BenefitCategory.CRITICAL_ILLNESS,
            coverage_amount=75000.00,
            monthly_premium=28.00,
            deductible=0,
            min_age=18,
            max_age=65,
            requires_active_duty=False,
            plan_code="CIS-75",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
        Benefit(
            name="Supplemental Term Life",
            description="Additional life insurance coverage to supplement your primary policy. Ideal for growing families or those with increased financial responsibilities.",
            category=BenefitCategory.SUPPLEMENTAL,
            coverage_amount=500000.00,
            monthly_premium=55.00,
            deductible=0,
            min_age=21,
            max_age=55,
            requires_active_duty=False,
            plan_code="STL-500",
            is_active=True,
            effective_date=date(2024, 1, 1),
        ),
    ]

    for benefit in benefits:
        db.add(benefit)

    # Create a demo member
    demo_member = Member(
        email="john.doe@military.mil",
        password_hash="demo_hash_replace_with_real_auth",  # In production, use proper password hashing
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1985, 6, 15),
        phone="555-123-4567",
        address="123 Base Housing Rd",
        city="Fort Liberty",
        state="NC",
        zip_code="28307",
        military_branch=MilitaryBranch.ARMY,
        service_start_date=date(2005, 8, 1),
        rank="Sergeant First Class",
        is_active_duty=True,
        member_number="MIL-2024-001234",
        membership_status=MembershipStatus.ACTIVE,
        membership_start_date=date(2020, 1, 15),
    )
    db.add(demo_member)

    db.commit()

    # Create enrollment for demo member
    from models import Enrollment

    # Get the member and benefits from db
    member = db.query(Member).filter(Member.email == "john.doe@military.mil").first()
    sgli_benefit = db.query(Benefit).filter(Benefit.plan_code == "SGLI-400").first()
    accident_benefit = db.query(Benefit).filter(Benefit.plan_code == "APP-50").first()

    if member and sgli_benefit:
        enrollment1 = Enrollment(
            member_id=member.id,
            benefit_id=sgli_benefit.id,
            enrollment_date=date(2020, 1, 15),
            effective_date=date(2020, 2, 1),
            is_active=True,
            coverage_amount=sgli_benefit.coverage_amount,
            monthly_premium=sgli_benefit.monthly_premium,
            beneficiary_name="Jane Doe",
            beneficiary_relationship="Spouse",
        )
        db.add(enrollment1)

    if member and accident_benefit:
        enrollment2 = Enrollment(
            member_id=member.id,
            benefit_id=accident_benefit.id,
            enrollment_date=date(2021, 6, 1),
            effective_date=date(2021, 7, 1),
            is_active=True,
            coverage_amount=accident_benefit.coverage_amount,
            monthly_premium=accident_benefit.monthly_premium,
            beneficiary_name="Jane Doe",
            beneficiary_relationship="Spouse",
        )
        db.add(enrollment2)

    db.commit()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database tables created.")

    db = SessionLocal()
    try:
        print("Seeding demo data...")
        seed_demo_data(db)
        print("Demo data seeded successfully.")
    finally:
        db.close()
