"""CrewAI agent configuration and crew setup."""

from crewai import Agent, Crew, Process, Task, LLM

from config import settings


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
        goal="Help users with their questions and provide helpful, accurate responses",
        backstory="""You are a friendly and knowledgeable AI assistant. 
        You help users by answering their questions clearly and concisely.
        You are powered by AWS Bedrock and use advanced language models to provide assistance.""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_chat_task(agent: Agent, user_message: str) -> Task:
    """Create a task for the agent to respond to a user message."""
    return Task(
        description=f"""Respond to the following user message in a helpful and friendly manner:
        
        User message: {user_message}
        
        Provide a clear, informative, and conversational response.""",
        expected_output="A helpful response to the user's question or message",
        agent=agent,
    )


def create_crew(user_message: str) -> Crew:
    """Create a crew with the assistant agent and a chat task."""
    assistant = create_assistant_agent()
    task = create_chat_task(assistant, user_message)

    return Crew(
        agents=[assistant],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


async def process_message(message: str) -> str:
    """Process a user message through the crew and return the response."""
    crew = create_crew(message)
    result = crew.kickoff()
    return str(result)
