"""SQLAlchemy models for the Member Center application."""

from datetime import date, datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models."""


class MilitaryBranch(str, PyEnum):
    """Military branch enumeration."""

    ARMY = "Army"
    NAVY = "Navy"
    AIR_FORCE = "Air Force"
    MARINE_CORPS = "Marine Corps"
    COAST_GUARD = "Coast Guard"
    SPACE_FORCE = "Space Force"


class MembershipStatus(str, PyEnum):
    """Membership status enumeration."""

    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    SUSPENDED = "Suspended"


class BenefitCategory(str, PyEnum):
    """Benefit category enumeration."""

    LIFE_INSURANCE = "Life Insurance"
    DISABILITY = "Disability"
    ACCIDENT = "Accident"
    CRITICAL_ILLNESS = "Critical Illness"
    SUPPLEMENTAL = "Supplemental"


class Member(Base):
    """Member model representing a member of the life insurance company."""

    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    # Military information
    military_branch = Column(Enum(MilitaryBranch), nullable=False)
    service_start_date = Column(Date)
    service_end_date = Column(Date)
    rank = Column(String(50))
    is_active_duty = Column(Boolean, default=False)

    # Membership information
    member_number = Column(String(20), unique=True, index=True, nullable=False)
    membership_status = Column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    membership_start_date = Column(Date)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollments = relationship(
        "Enrollment", back_populates="member", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Member {self.member_number}: {self.first_name} {self.last_name}>"


class Benefit(Base):
    """Benefit model representing available insurance benefits."""

    __tablename__ = "benefits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(Enum(BenefitCategory), nullable=False)

    # Coverage details
    coverage_amount = Column(Float, nullable=False)
    monthly_premium = Column(Float, nullable=False)
    deductible = Column(Float, default=0)

    # Eligibility
    min_age = Column(Integer, default=18)
    max_age = Column(Integer, default=65)
    requires_active_duty = Column(Boolean, default=False)

    # Plan details
    plan_code = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    effective_date = Column(Date)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="benefit")

    def __repr__(self):
        return f"<Benefit {self.plan_code}: {self.name}>"


class Enrollment(Base):
    """Enrollment model representing a member's enrollment in a benefit."""

    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    benefit_id = Column(Integer, ForeignKey("benefits.id"), nullable=False)

    # Enrollment details
    enrollment_date = Column(Date, default=date.today)
    effective_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    is_active = Column(Boolean, default=True)

    # Coverage specifics for this enrollment
    coverage_amount = Column(Float, nullable=False)
    monthly_premium = Column(Float, nullable=False)

    # Beneficiary information
    beneficiary_name = Column(String(200))
    beneficiary_relationship = Column(String(100))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    member = relationship("Member", back_populates="enrollments")
    benefit = relationship("Benefit", back_populates="enrollments")

    def __repr__(self):
        return f"<Enrollment Member:{self.member_id} Benefit:{self.benefit_id}>"
