"""FastAPI application for the Member Center backend."""

import logging
from contextlib import asynccontextmanager
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db, init_db, seed_demo_data, SessionLocal
from models import (
    Member,
    Benefit,
    Enrollment,
    MilitaryBranch,
    MembershipStatus,
    BenefitCategory,
)
from agents import process_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
        logger.info("Database initialized and seeded.")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Member Center API",
    description="API for Military Life Insurance Member Center - Managing member profiles, benefits, and enrollments",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic Models ============


class MemberBase(BaseModel):
    """Base member data model."""

    email: EmailStr
    first_name: str
    last_name: str
    date_of_birth: date
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    military_branch: MilitaryBranch
    service_start_date: Optional[date] = None
    service_end_date: Optional[date] = None
    rank: Optional[str] = None
    is_active_duty: bool = False


class MemberCreate(MemberBase):
    """Member creation model."""

    password: str


class MemberResponse(MemberBase):
    """Member response model."""

    id: int
    member_number: str
    membership_status: MembershipStatus
    membership_start_date: Optional[date] = None

    class Config:
        from_attributes = True


class MemberLogin(BaseModel):
    """Member login model."""

    email: EmailStr
    password: str


class BenefitResponse(BaseModel):
    """Benefit response model."""

    id: int
    name: str
    description: Optional[str] = None
    category: BenefitCategory
    coverage_amount: float
    monthly_premium: float
    deductible: float
    min_age: int
    max_age: int
    requires_active_duty: bool
    plan_code: str
    is_active: bool

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    """Enrollment creation model."""

    benefit_id: int
    beneficiary_name: Optional[str] = None
    beneficiary_relationship: Optional[str] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response model."""

    id: int
    member_id: int
    benefit_id: int
    enrollment_date: date
    effective_date: date
    termination_date: Optional[date] = None
    is_active: bool
    coverage_amount: float
    monthly_premium: float
    beneficiary_name: Optional[str] = None
    beneficiary_relationship: Optional[str] = None
    benefit: Optional[BenefitResponse] = None

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """Dashboard data response model."""

    member: MemberResponse
    enrollments: List[EnrollmentResponse]
    total_monthly_premium: float
    total_coverage: float


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str


# ============ Health Check Endpoints ============


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "healthy", "message": "Member Center API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============ Chat Endpoint ============


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message through the CrewAI agent."""
    try:
        response = await process_message(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message") from e


# ============ Member Endpoints ============


@app.get("/api/members/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get a member by ID."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.get("/api/members/by-email/{email}", response_model=MemberResponse)
def get_member_by_email(email: str, db: Session = Depends(get_db)):
    """Get a member by email."""
    member = db.query(Member).filter(Member.email == email).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.post("/api/members/login", response_model=MemberResponse)
def login_member(login_data: MemberLogin, db: Session = Depends(get_db)):
    """Simple login endpoint (demo - not for production use)."""
    member = db.query(Member).filter(Member.email == login_data.email).first()
    if not member:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # In production, you would verify password hash here
    return member


@app.post("/api/members", response_model=MemberResponse)
def create_member(member_data: MemberCreate, db: Session = Depends(get_db)):
    """Create a new member."""
    # Check if email already exists
    existing = db.query(Member).filter(Member.email == member_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate member number
    count = db.query(Member).count()
    member_number = f"MIL-{date.today().year}-{str(count + 1).zfill(6)}"

    member = Member(
        email=member_data.email,
        password_hash=member_data.password,  # In production, hash this!
        first_name=member_data.first_name,
        last_name=member_data.last_name,
        date_of_birth=member_data.date_of_birth,
        phone=member_data.phone,
        address=member_data.address,
        city=member_data.city,
        state=member_data.state,
        zip_code=member_data.zip_code,
        military_branch=member_data.military_branch,
        service_start_date=member_data.service_start_date,
        service_end_date=member_data.service_end_date,
        rank=member_data.rank,
        is_active_duty=member_data.is_active_duty,
        member_number=member_number,
        membership_status=MembershipStatus.ACTIVE,
        membership_start_date=date.today(),
    )

    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# ============ Dashboard Endpoint ============


@app.get("/api/members/{member_id}/dashboard", response_model=DashboardResponse)
def get_member_dashboard(member_id: int, db: Session = Depends(get_db)):
    """Get dashboard data for a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.member_id == member_id, Enrollment.is_active == True)
        .all()
    )

    # Calculate totals
    total_monthly_premium = sum(e.monthly_premium for e in enrollments)
    total_coverage = sum(e.coverage_amount for e in enrollments)

    # Load benefit details for each enrollment
    enrollment_responses = []
    for enrollment in enrollments:
        benefit = db.query(Benefit).filter(Benefit.id == enrollment.benefit_id).first()
        enrollment_dict = {
            "id": enrollment.id,
            "member_id": enrollment.member_id,
            "benefit_id": enrollment.benefit_id,
            "enrollment_date": enrollment.enrollment_date,
            "effective_date": enrollment.effective_date,
            "termination_date": enrollment.termination_date,
            "is_active": enrollment.is_active,
            "coverage_amount": enrollment.coverage_amount,
            "monthly_premium": enrollment.monthly_premium,
            "beneficiary_name": enrollment.beneficiary_name,
            "beneficiary_relationship": enrollment.beneficiary_relationship,
            "benefit": benefit,
        }
        enrollment_responses.append(enrollment_dict)

    return DashboardResponse(
        member=member,
        enrollments=enrollment_responses,
        total_monthly_premium=total_monthly_premium,
        total_coverage=total_coverage,
    )


# ============ Benefits Endpoints ============


@app.get("/api/benefits", response_model=List[BenefitResponse])
def get_benefits(
    category: Optional[BenefitCategory] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Get all available benefits, optionally filtered by category."""
    query = db.query(Benefit)

    if active_only:
        query = query.filter(Benefit.is_active == True)

    if category:
        query = query.filter(Benefit.category == category)

    return query.all()


@app.get("/api/benefits/{benefit_id}", response_model=BenefitResponse)
def get_benefit(benefit_id: int, db: Session = Depends(get_db)):
    """Get a specific benefit by ID."""
    benefit = db.query(Benefit).filter(Benefit.id == benefit_id).first()
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found")
    return benefit


# ============ Enrollment Endpoints ============


@app.get(
    "/api/members/{member_id}/enrollments", response_model=List[EnrollmentResponse]
)
def get_member_enrollments(
    member_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Get all enrollments for a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    query = db.query(Enrollment).filter(Enrollment.member_id == member_id)

    if active_only:
        query = query.filter(Enrollment.is_active == True)

    enrollments = query.all()

    # Load benefit details
    result = []
    for enrollment in enrollments:
        benefit = db.query(Benefit).filter(Benefit.id == enrollment.benefit_id).first()
        enrollment_dict = {
            "id": enrollment.id,
            "member_id": enrollment.member_id,
            "benefit_id": enrollment.benefit_id,
            "enrollment_date": enrollment.enrollment_date,
            "effective_date": enrollment.effective_date,
            "termination_date": enrollment.termination_date,
            "is_active": enrollment.is_active,
            "coverage_amount": enrollment.coverage_amount,
            "monthly_premium": enrollment.monthly_premium,
            "beneficiary_name": enrollment.beneficiary_name,
            "beneficiary_relationship": enrollment.beneficiary_relationship,
            "benefit": benefit,
        }
        result.append(enrollment_dict)

    return result


@app.post("/api/members/{member_id}/enrollments", response_model=EnrollmentResponse)
def create_enrollment(
    member_id: int,
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
):
    """Enroll a member in a benefit."""
    # Verify member exists
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Verify benefit exists
    benefit = db.query(Benefit).filter(Benefit.id == enrollment_data.benefit_id).first()
    if not benefit:
        raise HTTPException(status_code=404, detail="Benefit not found")

    # Check if already enrolled
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.member_id == member_id,
            Enrollment.benefit_id == enrollment_data.benefit_id,
            Enrollment.is_active == True,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this benefit")

    # Check eligibility (age)
    today = date.today()
    age = (
        today.year
        - member.date_of_birth.year
        - (
            (today.month, today.day)
            < (member.date_of_birth.month, member.date_of_birth.day)
        )
    )

    if age < benefit.min_age or age > benefit.max_age:
        raise HTTPException(
            status_code=400,
            detail=f"Age requirement not met. Must be between {benefit.min_age} and {benefit.max_age}.",
        )

    if benefit.requires_active_duty and not member.is_active_duty:
        raise HTTPException(
            status_code=400,
            detail="This benefit requires active duty status.",
        )

    # Create enrollment
    enrollment = Enrollment(
        member_id=member_id,
        benefit_id=enrollment_data.benefit_id,
        enrollment_date=today,
        effective_date=date(today.year, today.month + 1 if today.month < 12 else 1, 1),
        is_active=True,
        coverage_amount=benefit.coverage_amount,
        monthly_premium=benefit.monthly_premium,
        beneficiary_name=enrollment_data.beneficiary_name,
        beneficiary_relationship=enrollment_data.beneficiary_relationship,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return {
        "id": enrollment.id,
        "member_id": enrollment.member_id,
        "benefit_id": enrollment.benefit_id,
        "enrollment_date": enrollment.enrollment_date,
        "effective_date": enrollment.effective_date,
        "termination_date": enrollment.termination_date,
        "is_active": enrollment.is_active,
        "coverage_amount": enrollment.coverage_amount,
        "monthly_premium": enrollment.monthly_premium,
        "beneficiary_name": enrollment.beneficiary_name,
        "beneficiary_relationship": enrollment.beneficiary_relationship,
        "benefit": benefit,
    }


@app.delete("/api/members/{member_id}/enrollments/{enrollment_id}")
def cancel_enrollment(
    member_id: int,
    enrollment_id: int,
    db: Session = Depends(get_db),
):
    """Cancel an enrollment."""
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.id == enrollment_id,
            Enrollment.member_id == member_id,
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    enrollment.is_active = False
    enrollment.termination_date = date.today()

    db.commit()

    return {"message": "Enrollment cancelled successfully"}


if __name__ == "__main__":
    import uvicorn

    from config import settings

    uvicorn.run(app, host=settings.host, port=settings.port)
