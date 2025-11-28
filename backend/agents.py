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


def create_assistant_agent():
    """Create the main assistant agent that coordinates responses."""
    llm = get_bedrock_llm()

    return Agent(
        role="AI Assistant Coordinator",
        goal="Help users with their questions about military life insurance benefits, their profile, and their current coverage by coordinating with specialized agents and using the knowledge base",
        backstory="""You are a friendly and knowledgeable AI assistant specializing in military life insurance benefits. 
        You help users by answering their questions clearly and concisely.
        You are powered by AWS Bedrock and use advanced language models to provide assistance.
        
        You have access to specialized tools to:
        1. Look up the member's profile information (personal details, military service, membership status)
        2. Check their current benefit enrollments and coverage
        3. Show available benefit plans they can enroll in
        4. Provide coverage summaries
        
        When a user asks about their personal information, profile, benefits, coverage, or enrollments,
        use the appropriate tools to fetch their data. When they ask general questions about insurance
        products or policies, use the knowledge base context provided.
        
        Always be helpful, accurate, and provide personalized responses when member data is available.""",
        llm=llm,
        tools=[
            get_member_profile,
            get_member_benefits,
            get_available_benefits,
            get_coverage_summary,
        ],
        verbose=True,
        allow_delegation=False,
    )


def create_chat_task(
    agent: Agent,
    user_message: str,
    kb_context: str = "",
    has_user_context: bool = False,
) -> Task:
    """Create a task for the agent to respond to a user message."""

    context_section = ""
    if kb_context:
        context_section = f"""
        
{kb_context}

Use the above knowledge base context to help answer the user's question. If the context is relevant, incorporate it into your response."""

    user_context_note = ""
    if has_user_context:
        user_context_note = """
        
Note: A user is currently logged in. If the user asks about their profile, benefits, enrollments, 
or coverage, use the available tools to fetch their personalized data from the database."""
    else:
        user_context_note = """
        
Note: No user is currently logged in. If the user asks about their personal profile or benefits,
let them know they need to log in first to access that information."""

    return Task(
        description=f"""Respond to the following user message in a helpful and friendly manner:
        
        User message: {user_message}
        {context_section}
        {user_context_note}
        
        If the user is asking about their personal information, profile, current benefits, enrollments,
        or coverage details, use the appropriate tools to fetch their data.
        
        If the user is asking general questions about insurance products, use the knowledge base context.
        
        Provide a clear, informative, and conversational response.""",
        expected_output="A helpful response to the user's question or message, incorporating personalized member data and/or knowledge base information as appropriate",
        agent=agent,
    )


def create_crew(
    user_message: str, kb_context: str = "", has_user_context: bool = False
) -> Crew:
    """Create a crew with the assistant agent and a chat task."""
    assistant = create_assistant_agent()
    task = create_chat_task(assistant, user_message, kb_context, has_user_context)

    return Crew(
        agents=[assistant],
        tasks=[task],
        process=Process.sequential,
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
