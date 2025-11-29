"""CrewAI agent configuration and crew setup using YAML-based configuration."""

import logging
from typing import Optional

from crew import MemberCenterCrew
from tools import (
    set_current_user,
    retrieve_from_knowledge_base,
    format_knowledge_base_context,
)

logger = logging.getLogger(__name__)


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

        # Build context section for the task
        kb_context_section = ""
        if kb_context:
            kb_context_section = f"""

{kb_context}

Use the above knowledge base context to help answer the user's question. If the context is relevant, incorporate it into your response."""

        # Build user context note
        if user_id is not None:
            user_context_note = """

Note: A user is currently logged in. Delegate to the appropriate specialist agent to fetch 
their personalized data from the database when they ask about their profile, benefits, 
enrollments, or coverage."""
        else:
            user_context_note = """

Note: No user is currently logged in. If the user asks about their personal profile or benefits,
let them know they need to log in first to access that information."""

        # Create and run the crew with inputs for template interpolation
        crew_instance = MemberCenterCrew()
        result = crew_instance.crew().kickoff(
            inputs={
                "user_message": message,
                "kb_context": kb_context_section,
                "user_context_note": user_context_note,
            }
        )
        return str(result)
    finally:
        # Clear the user context after processing
        set_current_user(None)
