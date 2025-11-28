"""CrewAI agent configuration and crew setup."""

import logging
import boto3
from crewai import Agent, Crew, Process, Task, LLM

from config import settings

logger = logging.getLogger(__name__)


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


def create_assistant_agent():
    """Create the main assistant agent."""
    llm = get_bedrock_llm()

    return Agent(
        role="AI Assistant",
        goal="Help users with their questions about military life insurance benefits and provide helpful, accurate responses based on the knowledge base",
        backstory="""You are a friendly and knowledgeable AI assistant specializing in military life insurance benefits. 
        You help users by answering their questions clearly and concisely using information from the knowledge base.
        You are powered by AWS Bedrock and use advanced language models to provide assistance.
        When you have relevant context from the knowledge base, use it to provide accurate and detailed answers.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_chat_task(agent: Agent, user_message: str, kb_context: str = "") -> Task:
    """Create a task for the agent to respond to a user message."""

    context_section = ""
    if kb_context:
        context_section = f"""
        
{kb_context}

Use the above knowledge base context to help answer the user's question. If the context is relevant, incorporate it into your response. If the context is not relevant to the question, you can still provide a helpful general response."""

    return Task(
        description=f"""Respond to the following user message in a helpful and friendly manner:
        
        User message: {user_message}
        {context_section}
        
        Provide a clear, informative, and conversational response.""",
        expected_output="A helpful response to the user's question or message, incorporating relevant knowledge base information when available",
        agent=agent,
    )


def create_crew(user_message: str, kb_context: str = "") -> Crew:
    """Create a crew with the assistant agent and a chat task."""
    assistant = create_assistant_agent()
    task = create_chat_task(assistant, user_message, kb_context)

    return Crew(
        agents=[assistant],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


async def process_message(message: str) -> str:
    """Process a user message through the crew and return the response."""
    # First, retrieve relevant context from Knowledge Base
    kb_results = retrieve_from_knowledge_base(message)
    kb_context = format_knowledge_base_context(kb_results)

    # Create and run the crew with the KB context
    crew = create_crew(message, kb_context)
    result = crew.kickoff()
    return str(result)
