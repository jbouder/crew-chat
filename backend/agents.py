"""CrewAI agent configuration and crew setup."""

import logging
from typing import Optional

import boto3
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import Member, Benefit, Enrollment

logger = logging.getLogger(__name__)

# Global variable to store current user context for tools
_current_user_id: Optional[int] = None


def set_current_user(user_id: Optional[int]):
    """Set the current user ID for database queries."""
    global _current_user_id
    _current_user_id = user_id


def get_current_user_id() -> Optional[int]:
    """Get the current user ID."""
    return _current_user_id


# ============ Database Query Tools ============


@tool("Get Member Profile")
def get_member_profile() -> str:
    """
    Retrieve the current logged-in member's profile information including
    personal details, military service information, and membership status.
    Use this tool when the user asks about their profile, personal information,
    account details, military service, or membership status.
    """
    user_id = get_current_user_id()
    if not user_id:
        return "No user is currently logged in. Please ask the user to log in first."

    db: Session = SessionLocal()
    try:
        member = db.query(Member).filter(Member.id == user_id).first()
        if not member:
            return "Member profile not found."

        profile_info = f"""
**Member Profile Information:**

**Personal Details:**
- Name: {member.first_name} {member.last_name}
- Email: {member.email}
- Phone: {member.phone or 'Not provided'}
- Date of Birth: {member.date_of_birth}

**Address:**
- Street: {member.address or 'Not provided'}
- City: {member.city or 'Not provided'}
- State: {member.state or 'Not provided'}
- ZIP Code: {member.zip_code or 'Not provided'}

**Military Service:**
- Branch: {member.military_branch.value if member.military_branch else 'Not specified'}
- Rank: {member.rank or 'Not specified'}
- Service Start Date: {member.service_start_date or 'Not specified'}
- Service End Date: {member.service_end_date or 'Still serving'}
- Active Duty Status: {'Yes' if member.is_active_duty else 'No'}

**Membership:**
- Member Number: {member.member_number}
- Status: {member.membership_status.value if member.membership_status else 'Unknown'}
- Membership Start Date: {member.membership_start_date or 'Not specified'}
"""
        return profile_info
    finally:
        db.close()


@tool("Get Current Benefits and Enrollments")
def get_member_benefits() -> str:
    """
    Retrieve the current logged-in member's active benefit enrollments including
    coverage details, premiums, and beneficiary information.
    Use this tool when the user asks about their current benefits, coverage,
    enrollments, premiums, or what plans they are enrolled in.
    """
    user_id = get_current_user_id()
    if not user_id:
        return "No user is currently logged in. Please ask the user to log in first."

    db: Session = SessionLocal()
    try:
        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.member_id == user_id, Enrollment.is_active == True)
            .all()
        )

        if not enrollments:
            return "You are not currently enrolled in any benefits."

        total_premium = sum(e.monthly_premium for e in enrollments)
        total_coverage = sum(e.coverage_amount for e in enrollments)

        benefits_info = f"""
**Your Current Benefit Enrollments:**

**Summary:**
- Total Monthly Premium: ${total_premium:,.2f}
- Total Coverage Amount: ${total_coverage:,.2f}
- Number of Active Enrollments: {len(enrollments)}

**Enrolled Benefits:**
"""

        for i, enrollment in enumerate(enrollments, 1):
            benefit = (
                db.query(Benefit).filter(Benefit.id == enrollment.benefit_id).first()
            )
            if benefit:
                benefits_info += f"""
**{i}. {benefit.name}**
   - Plan Code: {benefit.plan_code}
   - Category: {benefit.category.value if benefit.category else 'N/A'}
   - Coverage Amount: ${enrollment.coverage_amount:,.2f}
   - Monthly Premium: ${enrollment.monthly_premium:,.2f}
   - Enrollment Date: {enrollment.enrollment_date}
   - Effective Date: {enrollment.effective_date}
   - Beneficiary: {enrollment.beneficiary_name or 'Not specified'} ({enrollment.beneficiary_relationship or 'N/A'})
   - Description: {benefit.description or 'No description available'}
"""

        return benefits_info
    finally:
        db.close()


@tool("Get Available Benefits")
def get_available_benefits() -> str:
    """
    Retrieve all available benefit plans that the member can enroll in.
    Use this tool when the user asks about available benefits, what plans
    they can sign up for, or wants to explore coverage options.
    """
    user_id = get_current_user_id()

    db: Session = SessionLocal()
    try:
        # Get member info for eligibility checking
        member = None
        if user_id:
            member = db.query(Member).filter(Member.id == user_id).first()

        benefits = db.query(Benefit).filter(Benefit.is_active == True).all()

        if not benefits:
            return "No benefits are currently available."

        # Get current enrollments to show which ones the member already has
        current_enrollment_ids = set()
        if user_id:
            enrollments = (
                db.query(Enrollment)
                .filter(Enrollment.member_id == user_id, Enrollment.is_active == True)
                .all()
            )
            current_enrollment_ids = {e.benefit_id for e in enrollments}

        benefits_info = """
**Available Benefit Plans:**

"""

        for benefit in benefits:
            enrolled_status = (
                "✓ Currently Enrolled"
                if benefit.id in current_enrollment_ids
                else "○ Not Enrolled"
            )

            # Check eligibility if member is logged in
            eligibility_note = ""
            if member:
                from datetime import date

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
                    eligibility_note = (
                        f" ⚠️ Age requirement: {benefit.min_age}-{benefit.max_age}"
                    )
                if benefit.requires_active_duty and not member.is_active_duty:
                    eligibility_note += " ⚠️ Requires active duty"

            benefits_info += f"""
**{benefit.name}** [{enrolled_status}]{eligibility_note}
- Plan Code: {benefit.plan_code}
- Category: {benefit.category.value if benefit.category else 'N/A'}
- Coverage Amount: ${benefit.coverage_amount:,.2f}
- Monthly Premium: ${benefit.monthly_premium:,.2f}
- Deductible: ${benefit.deductible:,.2f}
- Age Eligibility: {benefit.min_age} - {benefit.max_age} years
- Requires Active Duty: {'Yes' if benefit.requires_active_duty else 'No'}
- Description: {benefit.description or 'No description available'}

"""

        return benefits_info
    finally:
        db.close()


@tool("Get Benefit Coverage Summary")
def get_coverage_summary() -> str:
    """
    Get a summary of the member's total coverage across all enrolled benefits.
    Use this tool when the user asks about their total coverage, overall protection,
    or wants a high-level summary of their insurance portfolio.
    """
    user_id = get_current_user_id()
    if not user_id:
        return "No user is currently logged in. Please ask the user to log in first."

    db: Session = SessionLocal()
    try:
        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.member_id == user_id, Enrollment.is_active == True)
            .all()
        )

        if not enrollments:
            return "You have no active benefit enrollments to summarize."

        # Group by category
        from collections import defaultdict

        category_summary = defaultdict(
            lambda: {"count": 0, "coverage": 0, "premium": 0}
        )

        for enrollment in enrollments:
            benefit = (
                db.query(Benefit).filter(Benefit.id == enrollment.benefit_id).first()
            )
            if benefit:
                category = benefit.category.value if benefit.category else "Other"
                category_summary[category]["count"] += 1
                category_summary[category]["coverage"] += enrollment.coverage_amount
                category_summary[category]["premium"] += enrollment.monthly_premium

        total_premium = sum(e.monthly_premium for e in enrollments)
        total_coverage = sum(e.coverage_amount for e in enrollments)

        summary = f"""
**Your Coverage Summary:**

**Overall Totals:**
- Total Coverage: ${total_coverage:,.2f}
- Total Monthly Premium: ${total_premium:,.2f}
- Annual Premium Cost: ${total_premium * 12:,.2f}
- Number of Active Benefits: {len(enrollments)}

**Coverage by Category:**
"""

        for category, data in category_summary.items():
            summary += f"""
**{category}:**
- Number of Plans: {data['count']}
- Total Coverage: ${data['coverage']:,.2f}
- Monthly Premium: ${data['premium']:,.2f}
"""

        return summary
    finally:
        db.close()


# ============ Premium Calculator Tools ============


@tool("Calculate Premium")
def calculate_premium(
    benefit_id: int, coverage_amount: float, member_age: int, is_smoker: bool = False
) -> str:
    """
    Calculate the monthly premium for a specific benefit based on coverage amount, age, and health factors.
    Use this tool when the user asks about premium costs, wants a quote, or needs pricing information.

    Args:
        benefit_id: The ID of the benefit to calculate premium for
        coverage_amount: The desired coverage amount in dollars
        member_age: The member's current age
        is_smoker: Whether the member uses tobacco products (default False)
    """
    db: Session = SessionLocal()
    try:
        benefit = db.query(Benefit).filter(Benefit.id == benefit_id).first()
        benefit_name = benefit.name if benefit else f"Benefit ID {benefit_id}"

        # Base premium rates per $1000 of coverage (varies by benefit type)
        base_rates = {
            1: 0.08,  # SGLI
            2: 0.12,  # FSGLI
            3: 0.15,  # VGLI
            4: 0.10,  # S-DVI
            5: 2.50,  # Disability Protection (per $100 benefit)
            6: 0.25,  # Accident Protection
            7: 0.35,  # Critical Illness
            8: 0.18,  # Supplemental Term Life
        }

        base_rate = base_rates.get(benefit_id, 0.15)

        # Age adjustment factor
        if member_age < 30:
            age_factor = 1.0
            age_bracket = "Under 30"
        elif member_age < 40:
            age_factor = 1.15
            age_bracket = "30-39"
        elif member_age < 50:
            age_factor = 1.35
            age_bracket = "40-49"
        elif member_age < 60:
            age_factor = 1.65
            age_bracket = "50-59"
        else:
            age_factor = 2.10
            age_bracket = "60+"

        # Smoker adjustment
        smoker_factor = 1.50 if is_smoker else 1.0

        # Calculate premium
        if benefit_id == 5:  # Disability is per $100 benefit
            base_premium = (coverage_amount / 100) * base_rate
        else:
            base_premium = (coverage_amount / 1000) * base_rate

        adjusted_premium = base_premium * age_factor * smoker_factor

        return f"""
**Premium Calculation for {benefit_name}**

| Factor | Value |
|--------|-------|
| Coverage Amount | ${coverage_amount:,.2f} |
| Base Monthly Rate | ${base_premium:.2f} |
| Age Bracket ({age_bracket}) | {age_factor}x adjustment |
| Tobacco Use Factor | {smoker_factor}x |
| **Estimated Monthly Premium** | **${adjusted_premium:.2f}** |
| **Annual Cost** | **${adjusted_premium * 12:.2f}** |

*Note: This is an estimate. Final premium may vary based on underwriting review.*
"""
    finally:
        db.close()


@tool("Compare Plans")
def compare_plans(category: str, coverage_amount: float, member_age: int) -> str:
    """
    Compare multiple benefit plans within a category to help members choose the best option.
    Use this tool when the user wants to compare plans, see options side-by-side, or decide between benefits.

    Args:
        category: The benefit category (e.g., "Life Insurance", "Disability", "Accident", "Critical Illness")
        coverage_amount: The desired coverage amount for comparison
        member_age: The member's current age for premium calculation
    """
    comparisons = {
        "Life Insurance": [
            {
                "name": "SGLI",
                "coverage": "$400,000 max",
                "premium_rate": 0.08,
                "features": "Active duty, automatic coverage, low cost",
                "waiting_period": "None",
            },
            {
                "name": "FSGLI",
                "coverage": "$100,000 max",
                "premium_rate": 0.12,
                "features": "Spouse coverage, dependent children included",
                "waiting_period": "None",
            },
            {
                "name": "VGLI",
                "coverage": "$250,000 max",
                "premium_rate": 0.15,
                "features": "Converts from SGLI, no health exam if applied within 240 days",
                "waiting_period": "None",
            },
            {
                "name": "Supplemental Term Life",
                "coverage": "$500,000 max",
                "premium_rate": 0.18,
                "features": "Additional coverage, flexible terms",
                "waiting_period": "30 days",
            },
        ],
        "Disability": [
            {
                "name": "Military Disability Protection Plus",
                "coverage": "$5,000/mo max",
                "premium_rate": 2.50,
                "features": "Income replacement, own-occupation definition",
                "waiting_period": "90 days",
            },
            {
                "name": "S-DVI",
                "coverage": "$10,000 max",
                "premium_rate": 0.10,
                "features": "Service-disabled veterans, low premiums",
                "waiting_period": "None",
            },
        ],
        "Accident": [
            {
                "name": "Accident Protection Plan",
                "coverage": "$50,000 max",
                "premium_rate": 0.25,
                "features": "24/7 coverage, on/off duty",
                "waiting_period": "None",
            },
        ],
        "Critical Illness": [
            {
                "name": "Critical Illness Shield",
                "coverage": "$75,000 max",
                "premium_rate": 0.35,
                "features": "Covers 25+ conditions, lump sum payout",
                "waiting_period": "30 days",
            },
        ],
    }

    plans = comparisons.get(category, [])
    if not plans:
        return f"No plans found in the '{category}' category. Available categories: Life Insurance, Disability, Accident, Critical Illness."

    # Age factor for premium calculation
    if member_age < 30:
        age_factor = 1.0
    elif member_age < 40:
        age_factor = 1.15
    elif member_age < 50:
        age_factor = 1.35
    elif member_age < 60:
        age_factor = 1.65
    else:
        age_factor = 2.10

    result = f"""
## {category} Plan Comparison

| Plan | Max Coverage | Est. Monthly Premium | Key Features | Waiting Period |
|------|-------------|---------------------|--------------|----------------|
"""

    for plan in plans:
        est_premium = (coverage_amount / 1000) * plan["premium_rate"] * age_factor
        result += f"| {plan['name']} | {plan['coverage']} | ${est_premium:.2f} | {plan['features']} | {plan['waiting_period']} |\n"

    result += (
        f"\n*Estimates based on ${coverage_amount:,.0f} coverage for age {member_age}*"
    )
    return result


@tool("Estimate Coverage Needs")
def estimate_coverage_needs(
    annual_income: float,
    num_dependents: int,
    total_debt: float,
    years_of_income_replacement: int = 10,
) -> str:
    """
    Estimate the recommended life insurance coverage based on financial factors.
    Use this tool when the user asks how much coverage they need, wants recommendations, or is planning their insurance.

    Args:
        annual_income: The member's annual income
        num_dependents: Number of dependents (spouse, children)
        total_debt: Total outstanding debt (mortgage, loans, etc.)
        years_of_income_replacement: Number of years of income to replace (default 10)
    """
    # DIME method: Debt + Income + Mortgage + Education
    income_replacement = annual_income * years_of_income_replacement
    dependent_costs = num_dependents * 50000  # Education/care estimate per dependent
    total_needs = income_replacement + total_debt + dependent_costs

    # Recommended coverage tiers
    minimum = total_debt + (annual_income * 2)
    recommended = total_needs
    comprehensive = total_needs * 1.25

    return f"""
## Life Insurance Coverage Needs Analysis

### Your Financial Profile
| Factor | Value |
|--------|-------|
| Annual Income | ${annual_income:,.2f} |
| Number of Dependents | {num_dependents} |
| Total Debt | ${total_debt:,.2f} |
| Income Replacement Years | {years_of_income_replacement} |

### Coverage Recommendations

| Level | Coverage Amount | What It Covers |
|-------|----------------|----------------|
| **Minimum** | ${minimum:,.0f} | Debt payoff + 2 years income |
| **Recommended** | ${recommended:,.0f} | Full income replacement + debt + dependent care |
| **Comprehensive** | ${comprehensive:,.0f} | Recommended + 25% buffer for inflation |

### Suggested Plans
Based on your needs (${recommended:,.0f} recommended):
- **SGLI** ($400,000) - Primary coverage for active duty
- **Supplemental Term Life** (up to $500,000) - Additional coverage if needed
- Consider **FSGLI** ($100,000) for spouse coverage

*This is a general estimate. Consult with a benefits specialist for personalized advice.*
"""


# ============ Eligibility Verification Tools ============


@tool("Check Eligibility")
def check_eligibility(benefit_id: int) -> str:
    """
    Check if the current logged-in member is eligible for a specific benefit.
    Use this tool when the user asks if they qualify for a benefit or wants to know eligibility requirements.

    Args:
        benefit_id: The benefit ID to check eligibility for
    """
    user_id = get_current_user_id()
    if not user_id:
        return "No user is currently logged in. Please log in to check your eligibility for specific benefits."

    db: Session = SessionLocal()
    try:
        member = db.query(Member).filter(Member.id == user_id).first()
        benefit = db.query(Benefit).filter(Benefit.id == benefit_id).first()

        if not member:
            return "Member profile not found."
        if not benefit:
            return f"Benefit with ID {benefit_id} not found."

        # Calculate member's age
        from datetime import date

        today = date.today()
        age = (
            today.year
            - member.date_of_birth.year
            - (
                (today.month, today.day)
                < (member.date_of_birth.month, member.date_of_birth.day)
            )
        )

        # Check various eligibility criteria
        eligibility_checks = []
        is_eligible = True

        # Age check
        if age < benefit.min_age:
            eligibility_checks.append(
                f"❌ **Age Requirement**: You are {age} years old, but minimum age is {benefit.min_age}"
            )
            is_eligible = False
        elif age > benefit.max_age:
            eligibility_checks.append(
                f"❌ **Age Requirement**: You are {age} years old, but maximum age is {benefit.max_age}"
            )
            is_eligible = False
        else:
            eligibility_checks.append(
                f"✅ **Age Requirement**: You are {age} years old (eligible range: {benefit.min_age}-{benefit.max_age})"
            )

        # Active duty check
        if benefit.requires_active_duty:
            if member.is_active_duty:
                eligibility_checks.append(
                    "✅ **Active Duty**: You are currently on active duty"
                )
            else:
                eligibility_checks.append(
                    "❌ **Active Duty**: This benefit requires active duty status"
                )
                is_eligible = False
        else:
            eligibility_checks.append(
                "✅ **Active Duty**: Not required for this benefit"
            )

        # Check if already enrolled
        existing_enrollment = (
            db.query(Enrollment)
            .filter(
                Enrollment.member_id == user_id,
                Enrollment.benefit_id == benefit_id,
                Enrollment.is_active == True,
            )
            .first()
        )

        if existing_enrollment:
            eligibility_checks.append(
                "ℹ️ **Enrollment Status**: You are already enrolled in this benefit"
            )
        else:
            eligibility_checks.append(
                "✅ **Enrollment Status**: Not currently enrolled"
            )

        status = "**ELIGIBLE**" if is_eligible else "**NOT ELIGIBLE**"

        return f"""
## Eligibility Check: {benefit.name}

### Overall Status: {status}

### Eligibility Details:
{chr(10).join(eligibility_checks)}

### Benefit Information:
- **Category**: {benefit.category.value if benefit.category else 'N/A'}
- **Coverage Amount**: ${benefit.coverage_amount:,.2f}
- **Monthly Premium**: ${benefit.monthly_premium:,.2f}
- **Description**: {benefit.description or 'No description available'}
"""
    finally:
        db.close()


@tool("Get Military Status")
def get_military_status() -> str:
    """
    Get the current member's military service status and how it affects their benefit eligibility.
    Use this tool when the user asks about their military status, service record, or how it impacts their benefits.
    """
    user_id = get_current_user_id()
    if not user_id:
        return "No user is currently logged in. Please log in to view your military status."

    db: Session = SessionLocal()
    try:
        member = db.query(Member).filter(Member.id == user_id).first()
        if not member:
            return "Member profile not found."

        # Determine eligibility implications
        if member.is_active_duty:
            status_implications = """
### Benefits Available to Active Duty:
- ✅ **SGLI** - Full eligibility for Service Members' Group Life Insurance
- ✅ **FSGLI** - Family coverage available
- ✅ **Military Disability Protection Plus** - Full eligibility
- ✅ **Accident Protection Plan** - On and off-duty coverage
- ✅ **Critical Illness Shield** - Available
- ✅ **Supplemental Term Life** - Available
"""
        else:
            status_implications = """
### Benefits Available to Veterans/Non-Active Duty:
- ✅ **VGLI** - Veterans' Group Life Insurance (convert from SGLI within 240 days)
- ✅ **S-DVI** - If service-disabled
- ⚠️ **SGLI** - Not available (active duty only)
- ⚠️ **FSGLI** - Not available (active duty only)
- ✅ **Accident Protection Plan** - Available
- ✅ **Critical Illness Shield** - Available
- ✅ **Supplemental Term Life** - Available
"""

        return f"""
## Military Service Status

### Your Service Information:
| Field | Value |
|-------|-------|
| Branch | {member.military_branch.value if member.military_branch else 'Not specified'} |
| Rank | {member.rank or 'Not specified'} |
| Service Start Date | {member.service_start_date or 'Not specified'} |
| Service End Date | {member.service_end_date or 'Currently serving'} |
| **Active Duty Status** | **{'Yes - Currently Active' if member.is_active_duty else 'No - Not Active Duty'}** |

{status_implications}
"""
    finally:
        db.close()


@tool("Verify Documentation Requirements")
def verify_documentation_requirements(benefit_id: int) -> str:
    """
    Get the documentation requirements for enrolling in a specific benefit.
    Use this tool when the user asks what documents they need, what paperwork is required, or how to prepare for enrollment.

    Args:
        benefit_id: The benefit ID to check documentation requirements for
    """
    db: Session = SessionLocal()
    try:
        benefit = db.query(Benefit).filter(Benefit.id == benefit_id).first()
        if not benefit:
            return f"Benefit with ID {benefit_id} not found."

        # Documentation requirements by benefit type
        doc_requirements = {
            1: {  # SGLI
                "required": [
                    "SGLV 8286 - Servicemembers' Group Life Insurance Election",
                    "Valid military ID",
                ],
                "optional": ["DD Form 214 (if recently separated)"],
                "notes": "Enrollment is typically automatic for active duty. Form needed for changes or beneficiary updates.",
            },
            2: {  # FSGLI
                "required": [
                    "SGLV 8286A - Family Coverage Election",
                    "Spouse's date of birth and SSN",
                    "Marriage certificate",
                ],
                "optional": [
                    "Spouse's medical questionnaire (if coverage over $100,000)"
                ],
                "notes": "Coverage for spouse requires service member to have SGLI.",
            },
            3: {  # VGLI
                "required": [
                    "SGLV 8714 - Application for VGLI",
                    "DD Form 214",
                    "Valid ID",
                ],
                "optional": [
                    "Medical evidence (if applying after 240 days from separation)"
                ],
                "notes": "Apply within 240 days of separation to avoid medical underwriting.",
            },
            4: {  # S-DVI
                "required": [
                    "VA Form 29-4364 - Application for S-DVI",
                    "VA disability rating letter",
                    "Valid ID",
                ],
                "optional": ["Medical records related to disability"],
                "notes": "Must have service-connected disability rating from VA.",
            },
            5: {  # Disability Protection Plus
                "required": [
                    "Application form",
                    "Proof of income (LES or tax returns)",
                    "Medical questionnaire",
                ],
                "optional": ["Physician's statement"],
                "notes": "Income verification required for benefit amount determination.",
            },
            6: {  # Accident Protection
                "required": [
                    "Application form",
                    "Valid ID",
                    "Beneficiary designation form",
                ],
                "optional": [],
                "notes": "No medical underwriting required.",
            },
            7: {  # Critical Illness
                "required": ["Application form", "Medical questionnaire", "Valid ID"],
                "optional": ["Recent medical records", "Physician's statement"],
                "notes": "Pre-existing conditions may affect coverage.",
            },
            8: {  # Supplemental Term Life
                "required": [
                    "Application form",
                    "Medical questionnaire",
                    "Valid ID",
                    "Beneficiary designation",
                ],
                "optional": ["Paramedical exam (for coverage over $250,000)"],
                "notes": "Higher coverage amounts may require additional underwriting.",
            },
        }

        reqs = doc_requirements.get(
            benefit_id,
            {
                "required": ["Standard application form", "Valid ID"],
                "optional": ["Supporting documentation as needed"],
                "notes": "Contact a benefits specialist for specific requirements.",
            },
        )

        required_list = "\n".join([f"- {doc}" for doc in reqs["required"]])
        optional_list = (
            "\n".join([f"- {doc}" for doc in reqs["optional"]])
            if reqs["optional"]
            else "- None"
        )

        return f"""
## Documentation Requirements: {benefit.name}

### Required Documents:
{required_list}

### Optional/Conditional Documents:
{optional_list}

### Important Notes:
{reqs["notes"]}

### Submission Options:
- **Online**: Upload documents through the Member Portal
- **Mail**: Send to Patriot Life Insurance, PO Box 12345, Arlington, VA 22201
- **In Person**: Visit any Patriot Life office with original documents

*Documents should be submitted within 30 days of application to avoid processing delays.*
"""
    finally:
        db.close()


# ============ Document Assistant Tools ============


@tool("Get Required Documents")
def get_required_documents(action_type: str) -> str:
    """
    Get a list of required documents for a specific action (enrollment, claims, changes, etc.).
    Use this tool when the user asks what documents or forms they need for a particular action.

    Args:
        action_type: Type of action - "enrollment", "beneficiary_change", "address_change", "claim", "cancellation"
    """
    document_lists = {
        "enrollment": {
            "title": "New Benefit Enrollment",
            "documents": [
                (
                    "Benefit Application Form",
                    "Specific to the benefit you're enrolling in",
                ),
                ("Valid Government ID", "Military ID, driver's license, or passport"),
                ("Proof of Eligibility", "DD-214, LES, or active duty orders"),
                (
                    "Beneficiary Designation Form",
                    "Required for life insurance products",
                ),
                ("Medical Questionnaire", "Required for some benefits"),
            ],
            "timeline": "Submit within 30 days of qualifying event for guaranteed issue",
        },
        "beneficiary_change": {
            "title": "Beneficiary Change",
            "documents": [
                ("Beneficiary Change Form", "Form BC-100 or benefit-specific form"),
                ("Valid Government ID", "To verify your identity"),
                (
                    "Beneficiary Information",
                    "Full name, SSN, DOB, and relationship for each beneficiary",
                ),
            ],
            "timeline": "Changes typically effective within 5-7 business days",
        },
        "address_change": {
            "title": "Address Change",
            "documents": [
                ("Address Change Form", "Form AC-200 or update through Member Portal"),
                ("Proof of New Address", "Utility bill, lease, or official mail"),
            ],
            "timeline": "Updates processed within 2-3 business days",
        },
        "claim": {
            "title": "Filing a Claim",
            "documents": [
                (
                    "Claim Form",
                    "Specific to benefit type (life, disability, accident, illness)",
                ),
                ("Death Certificate", "For life insurance claims - certified copy"),
                (
                    "Medical Records",
                    "Supporting documentation from healthcare providers",
                ),
                ("Police Report", "For accident claims, if applicable"),
                ("Proof of Loss", "Documentation of the covered event"),
                ("Beneficiary ID", "Valid ID of the person filing the claim"),
            ],
            "timeline": "Claims typically processed within 30-60 days of complete submission",
        },
        "cancellation": {
            "title": "Benefit Cancellation",
            "documents": [
                ("Cancellation Request Form", "Form CR-300"),
                ("Valid Government ID", "To verify your identity"),
                ("Written Statement", "Reason for cancellation (optional but helpful)"),
            ],
            "timeline": "Cancellation effective at end of current billing period",
        },
    }

    if action_type.lower() not in document_lists:
        available = ", ".join(document_lists.keys())
        return (
            f"Unknown action type '{action_type}'. Available action types: {available}"
        )

    info = document_lists[action_type.lower()]
    docs_formatted = "\n".join(
        [f"| {doc[0]} | {doc[1]} |" for doc in info["documents"]]
    )

    return f"""
## Required Documents: {info["title"]}

| Document | Purpose |
|----------|---------|
{docs_formatted}

### Timeline:
{info["timeline"]}

### How to Submit:
1. **Online Portal**: Upload scanned copies through your Member Dashboard
2. **Email**: Send to documents@patriotlife.com
3. **Fax**: (800) 555-1234
4. **Mail**: Patriot Life Insurance, Document Processing, PO Box 12345, Arlington, VA 22201

*Tip: Keep copies of all submitted documents for your records.*
"""


@tool("Generate Form")
def generate_form(form_type: str) -> str:
    """
    Get information about how to access and complete a specific form.
    Use this tool when the user needs a specific form or wants to know where to find it.

    Args:
        form_type: The type of form needed - "enrollment", "beneficiary", "claim", "cancellation", "address_change"
    """
    forms = {
        "enrollment": {
            "name": "Benefit Enrollment Application",
            "form_number": "ENR-100",
            "pages": 4,
            "sections": [
                "Personal Information",
                "Military Service Details",
                "Benefit Selection",
                "Beneficiary Designation",
                "Signature & Authorization",
            ],
            "url": "/forms/ENR-100.pdf",
            "tips": [
                "Complete all sections in blue or black ink",
                "Ensure SSN and DOB are accurate",
                "Sign and date on the last page",
                "Attach required supporting documents",
            ],
        },
        "beneficiary": {
            "name": "Beneficiary Designation Form",
            "form_number": "BC-100",
            "pages": 2,
            "sections": [
                "Policy Information",
                "Primary Beneficiary",
                "Contingent Beneficiary",
                "Signature",
            ],
            "url": "/forms/BC-100.pdf",
            "tips": [
                "Percentages must total 100% for each beneficiary level",
                "Include full legal names of beneficiaries",
                "Update after major life events (marriage, birth, divorce)",
                "Both spouses should sign if community property state",
            ],
        },
        "claim": {
            "name": "Insurance Claim Form",
            "form_number": "CLM-200",
            "pages": 6,
            "sections": [
                "Claimant Information",
                "Deceased/Insured Information",
                "Cause of Loss",
                "Medical Authorization",
                "Payment Instructions",
                "Signature",
            ],
            "url": "/forms/CLM-200.pdf",
            "tips": [
                "Attach certified death certificate for life claims",
                "Include all medical provider information",
                "Specify preferred payment method",
                "Allow 30-60 days for processing",
            ],
        },
        "cancellation": {
            "name": "Benefit Cancellation Request",
            "form_number": "CR-300",
            "pages": 1,
            "sections": [
                "Member Information",
                "Benefit to Cancel",
                "Reason (Optional)",
                "Signature",
            ],
            "url": "/forms/CR-300.pdf",
            "tips": [
                "Consider coverage implications before canceling",
                "Note the effective cancellation date",
                "Review any refund or proration policies",
                "Keep confirmation for your records",
            ],
        },
        "address_change": {
            "name": "Address/Contact Update Form",
            "form_number": "AC-200",
            "pages": 1,
            "sections": ["Current Information", "New Information", "Signature"],
            "url": "/forms/AC-200.pdf",
            "tips": [
                "Update all policies at once",
                "Include effective date of change",
                "Attach proof of new address",
                "Also update with DEERS if military",
            ],
        },
    }

    if form_type.lower() not in forms:
        available = ", ".join(forms.keys())
        return f"Unknown form type '{form_type}'. Available forms: {available}"

    form = forms[form_type.lower()]
    tips_formatted = "\n".join([f"- {tip}" for tip in form["tips"]])
    sections_formatted = " → ".join(form["sections"])

    return f"""
## Form: {form["name"]}

### Form Details:
| Field | Value |
|-------|-------|
| Form Number | {form["form_number"]} |
| Number of Pages | {form["pages"]} |
| Download Link | [Click to Download]({form["url"]}) |

### Form Sections:
{sections_formatted}

### Completion Tips:
{tips_formatted}

### How to Access:
1. **Download**: Available in your Member Portal under "Forms & Documents"
2. **Request by Mail**: Call (800) 555-LIFE to request a paper copy
3. **In Person**: Pick up at any Patriot Life office

### Submission:
Once completed, submit through your Member Portal or mail to:
Patriot Life Insurance
PO Box 12345
Arlington, VA 22201
"""


@tool("Explain Form Fields")
def explain_form_fields(form_type: str, field_name: str = "") -> str:
    """
    Explain what specific fields on a form mean and how to fill them out.
    Use this tool when the user is confused about a form field or needs help understanding what information to provide.

    Args:
        form_type: The type of form - "enrollment", "beneficiary", "claim"
        field_name: Optional specific field name to explain. If empty, explains all common fields.
    """
    field_explanations = {
        "enrollment": {
            "coverage_amount": "The total dollar amount of insurance protection you're applying for. For life insurance, this is the death benefit paid to beneficiaries.",
            "effective_date": "The date your coverage begins. Usually the first of the month following approval, or a specific qualifying event date.",
            "military_branch": "Your branch of service: Army, Navy, Air Force, Marine Corps, Coast Guard, or Space Force.",
            "duty_status": "Whether you're Active Duty, Reserve, National Guard, or Veteran. This affects eligibility for certain benefits.",
            "tobacco_use": "Whether you've used tobacco products in the past 12 months. This affects premium rates for many policies.",
            "beneficiary": "The person(s) who will receive the benefit if you pass away. Can be primary (first in line) or contingent (backup).",
        },
        "beneficiary": {
            "primary_beneficiary": "The first person(s) to receive the death benefit. You can name multiple and assign percentages.",
            "contingent_beneficiary": "Backup beneficiary if primary beneficiary is deceased or can't be located.",
            "per_stirpes": "Legal term meaning if a beneficiary dies, their share goes to their children. Alternative is 'per capita' (split among survivors).",
            "irrevocable": "A beneficiary designation that cannot be changed without that beneficiary's consent. Rarely used.",
            "percentage": "The portion of the benefit each beneficiary receives. Must total 100% for each level (primary/contingent).",
        },
        "claim": {
            "cause_of_death": "The medical reason or circumstances of death as listed on the death certificate.",
            "attending_physician": "The doctor who treated the deceased or pronounced death. Include name, address, and phone.",
            "policy_number": "Your unique insurance policy identifier. Found on your policy documents or Member Portal.",
            "claimant": "The person filing the claim. Usually the beneficiary or their legal representative.",
            "payment_method": "How you want to receive the benefit: check, direct deposit, or structured settlement.",
        },
    }

    if form_type.lower() not in field_explanations:
        available = ", ".join(field_explanations.keys())
        return f"Unknown form type '{form_type}'. Available forms: {available}"

    fields = field_explanations[form_type.lower()]

    if field_name and field_name.lower().replace(" ", "_") in fields:
        key = field_name.lower().replace(" ", "_")
        return f"""
## Field Explanation: {field_name.replace("_", " ").title()}

**Form**: {form_type.title()} Form

**What This Field Means**:
{fields[key]}

**Tips for Completing**:
- Be accurate and consistent with other documents
- Use legal names (as they appear on government ID)
- If unsure, contact a benefits specialist before submitting
"""

    # Return all field explanations for the form
    all_fields = "\n\n".join(
        [
            f"**{key.replace('_', ' ').title()}**\n{value}"
            for key, value in fields.items()
        ]
    )

    return f"""
## Form Field Guide: {form_type.title()} Form

{all_fields}

---
*Need help with a specific field? Ask about it by name for more detailed guidance.*
"""


def get_bedrock_agent_runtime_client():
    """Create and return a Bedrock Agent Runtime client for Knowledge Base retrieval."""
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def retrieve_from_knowledge_base(query: str, max_results: int = 5) -> list[dict]:
    """
    Retrieve relevant documents from Bedrock Knowledge Base.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        List of retrieved documents with their content and metadata
    """
    if not settings.bedrock_knowledge_base_id:
        logger.warning("No Knowledge Base ID configured, skipping retrieval")
        return []

    try:
        client = get_bedrock_agent_runtime_client()

        response = client.retrieve(
            knowledgeBaseId=settings.bedrock_knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            },
        )

        results = []
        for result in response.get("retrievalResults", []):
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            location = result.get("location", {})

            results.append(
                {
                    "content": content,
                    "score": score,
                    "source": location.get("s3Location", {}).get("uri", "Unknown"),
                }
            )

        logger.info(f"Retrieved {len(results)} documents from Knowledge Base")
        return results

    except Exception as e:
        logger.error(f"Error retrieving from Knowledge Base: {e}")
        return []


def format_knowledge_base_context(results: list[dict]) -> str:
    """Format Knowledge Base results into a context string for the agent."""
    if not results:
        return ""

    context_parts = ["Here is relevant information from the knowledge base:\n"]

    for i, result in enumerate(results, 1):
        context_parts.append(f"--- Document {i} (relevance: {result['score']:.2f}) ---")
        context_parts.append(result["content"])
        context_parts.append("")

    return "\n".join(context_parts)


def get_bedrock_llm():
    """Create and return a Bedrock LLM instance for CrewAI."""
    return LLM(
        model=f"bedrock/{settings.bedrock_model_id}",
        temperature=0.7,
        max_tokens=4096,
    )


# ============ Agent Definitions ============


def create_profile_agent():
    """Create an agent specialized in member profile queries."""
    llm = get_bedrock_llm()

    return Agent(
        role="Member Profile Specialist",
        goal="Help members access and understand their profile information, military service details, and membership status",
        backstory="""You are a specialized agent that helps members access their personal profile information.
        You have access to the member database and can retrieve profile details, military service information,
        and membership status. You provide accurate, helpful information about the member's account.""",
        llm=llm,
        tools=[get_member_profile],
        verbose=True,
        allow_delegation=False,
    )


def create_benefits_agent():
    """Create an agent specialized in benefits and enrollment queries."""
    llm = get_bedrock_llm()

    return Agent(
        role="Benefits Specialist",
        goal="Help members understand their current benefit enrollments, available plans, and coverage details",
        backstory="""You are a specialized agent that helps members with all benefit-related questions.
        You can retrieve current enrollments, show available benefit plans, and provide coverage summaries.
        You help members understand their insurance portfolio and explore new coverage options.""",
        llm=llm,
        tools=[get_member_benefits, get_available_benefits, get_coverage_summary],
        verbose=True,
        allow_delegation=False,
    )


def create_premium_calculator_agent():
    """Create an agent specialized in premium calculations and plan comparisons."""
    llm = get_bedrock_llm()

    return Agent(
        role="Premium Calculator Specialist",
        goal="Help members understand premium costs, compare different plans, and estimate their coverage needs based on their financial situation",
        backstory="""You are a specialized agent that helps members with premium calculations and financial planning.
        You can calculate premium estimates based on coverage amounts, age, and health factors.
        You help members compare different plans side-by-side and estimate how much coverage they need
        based on their income, dependents, and debts. You provide clear, accurate financial guidance.""",
        llm=llm,
        tools=[calculate_premium, compare_plans, estimate_coverage_needs],
        verbose=True,
        allow_delegation=False,
    )


def create_eligibility_agent():
    """Create an agent specialized in eligibility verification."""
    llm = get_bedrock_llm()

    return Agent(
        role="Eligibility Verification Specialist",
        goal="Help members understand their eligibility for benefits based on their military status, age, and other factors",
        backstory="""You are a specialized agent that helps members verify their eligibility for various benefits.
        You can check specific benefit eligibility, explain military status implications, and detail
        documentation requirements. You ensure members understand what they qualify for and what
        they need to provide to enroll in benefits.""",
        llm=llm,
        tools=[
            check_eligibility,
            get_military_status,
            verify_documentation_requirements,
        ],
        verbose=True,
        allow_delegation=False,
    )


def create_document_assistant_agent():
    """Create an agent specialized in forms and documentation assistance."""
    llm = get_bedrock_llm()

    return Agent(
        role="Document Assistant Specialist",
        goal="Help members with forms, documentation requirements, and paperwork for all insurance-related processes",
        backstory="""You are a specialized agent that helps members navigate forms and documentation.
        You can explain what documents are needed for various actions, provide information about
        specific forms, and help members understand form fields. You make the paperwork process
        simple and clear for members.""",
        llm=llm,
        tools=[get_required_documents, generate_form, explain_form_fields],
        verbose=True,
        allow_delegation=False,
    )


def create_manager_agent():
    """Create the manager agent that coordinates and delegates to specialized agents."""
    llm = get_bedrock_llm()

    return Agent(
        role="AI Assistant Manager",
        goal="Coordinate and delegate user requests to the appropriate specialized agents to provide accurate and helpful responses about military life insurance benefits",
        backstory="""You are the manager and coordinator of a team of specialized insurance agents. 
        You help users by understanding their questions and delegating to the right specialist.
        You are powered by AWS Bedrock and use advanced language models to provide assistance.
        
        Your team of specialized agents includes:
        1. Member Profile Specialist - for profile, personal details, military service, membership status
        2. Benefits Specialist - for current enrollments, available plans, coverage details and summaries
        3. Premium Calculator Specialist - for premium calculations, plan comparisons, coverage needs estimates
        4. Eligibility Verification Specialist - for eligibility checks, military status implications, documentation requirements
        5. Document Assistant Specialist - for forms, required documents, form field explanations
        
        When a user asks a question:
        - For profile or personal information questions, delegate to the Member Profile Specialist
        - For benefits, enrollments, or coverage questions, delegate to the Benefits Specialist
        - For premium quotes, plan comparisons, or coverage needs, delegate to the Premium Calculator Specialist
        - For eligibility or military status questions, delegate to the Eligibility Verification Specialist
        - For forms or documentation questions, delegate to the Document Assistant Specialist
        - For general questions, synthesize information from relevant specialists
        
        Always be helpful, accurate, and coordinate effectively to provide the best response.""",
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=True,
    )


def create_manager_task(
    manager: Agent,
    user_message: str,
    kb_context: str = "",
    has_user_context: bool = False,
) -> Task:
    """Create a task for the manager agent to coordinate the response to a user message."""

    context_section = ""
    if kb_context:
        context_section = f"""
        
{kb_context}

Use the above knowledge base context to help answer the user's question. If the context is relevant, incorporate it into your response."""

    user_context_note = ""
    if has_user_context:
        user_context_note = """
        
Note: A user is currently logged in. Delegate to the appropriate specialist agent to fetch 
their personalized data from the database when they ask about their profile, benefits, 
enrollments, or coverage."""
    else:
        user_context_note = """
        
Note: No user is currently logged in. If the user asks about their personal profile or benefits,
let them know they need to log in first to access that information."""

    return Task(
        description=f"""Coordinate a response to the following user message by delegating to the appropriate specialized agent:
        
        User message: {user_message}
        {context_section}
        {user_context_note}
        
        Delegation guidelines:
        - For profile, personal information, military service, or membership questions: delegate to Member Profile Specialist
        - For current benefits, enrollments, available plans, or coverage summary: delegate to Benefits Specialist  
        - For premium calculations, plan comparisons, or coverage needs estimates: delegate to Premium Calculator Specialist
        - For eligibility checks, military status, or documentation requirements: delegate to Eligibility Verification Specialist
        - For forms, required documents, or form field explanations: delegate to Document Assistant Specialist
        - For general questions, synthesize relevant knowledge base context
        
        Provide a clear, informative, and conversational response based on the specialist's findings.""",
        expected_output="A helpful response to the user's question coordinated from the appropriate specialist agent(s), incorporating personalized member data and/or knowledge base information as appropriate",
        agent=manager,
    )


def create_crew(
    user_message: str, kb_context: str = "", has_user_context: bool = False
) -> Crew:
    """Create a crew with the manager agent and all specialized agents using hierarchical delegation."""
    # Create the manager agent
    manager = create_manager_agent()
    
    # Create all specialized agents
    profile_agent = create_profile_agent()
    benefits_agent = create_benefits_agent()
    premium_calculator_agent = create_premium_calculator_agent()
    eligibility_agent = create_eligibility_agent()
    document_assistant_agent = create_document_assistant_agent()
    
    # Create the manager task
    task = create_manager_task(manager, user_message, kb_context, has_user_context)

    return Crew(
        agents=[
            profile_agent,
            benefits_agent,
            premium_calculator_agent,
            eligibility_agent,
            document_assistant_agent,
        ],
        tasks=[task],
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True,
    )


async def process_message(message: str, user_id: Optional[int] = None) -> str:
    """
    Process a user message through the crew and return the response.

    Args:
        message: The user's message
        user_id: Optional ID of the logged-in user for personalized queries

    Returns:
        The agent's response as a string
    """
    # Set the current user context for the tools
    set_current_user(user_id)

    try:
        # First, retrieve relevant context from Knowledge Base
        kb_results = retrieve_from_knowledge_base(message)
        kb_context = format_knowledge_base_context(kb_results)

        # Create and run the crew with the KB context and user context
        crew = create_crew(message, kb_context, has_user_context=(user_id is not None))
        result = crew.kickoff()
        return str(result)
    finally:
        # Clear the user context after processing
        set_current_user(None)
