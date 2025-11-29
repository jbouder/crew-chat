"""CrewAI crew configuration using YAML-based setup."""

from typing import List

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from config import settings
from tools import (
    get_member_profile,
    get_member_benefits,
    get_available_benefits,
    get_coverage_summary,
    calculate_premium,
    compare_plans,
    estimate_coverage_needs,
    check_eligibility,
    get_military_status,
    verify_documentation_requirements,
    get_required_documents,
    generate_form,
    explain_form_fields,
)


def get_bedrock_llm() -> LLM:
    """Create and return a Bedrock LLM instance for CrewAI."""
    return LLM(
        model=f"bedrock/{settings.bedrock_model_id}",
        temperature=0.7,
        max_tokens=4096,
    )


@CrewBase
class MemberCenterCrew:
    """Member Center crew for handling insurance-related queries."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the crew."""
        self._llm = get_bedrock_llm()

    @agent
    def profile_specialist(self) -> Agent:
        """Create the profile specialist agent."""
        return Agent(
            config=self.agents_config["profile_specialist"],
            llm=self._llm,
            tools=[get_member_profile],
        )

    @agent
    def benefits_specialist(self) -> Agent:
        """Create the benefits specialist agent."""
        return Agent(
            config=self.agents_config["benefits_specialist"],
            llm=self._llm,
            tools=[get_member_benefits, get_available_benefits, get_coverage_summary],
        )

    @agent
    def premium_calculator_specialist(self) -> Agent:
        """Create the premium calculator specialist agent."""
        return Agent(
            config=self.agents_config["premium_calculator_specialist"],
            llm=self._llm,
            tools=[calculate_premium, compare_plans, estimate_coverage_needs],
        )

    @agent
    def eligibility_specialist(self) -> Agent:
        """Create the eligibility specialist agent."""
        return Agent(
            config=self.agents_config["eligibility_specialist"],
            llm=self._llm,
            tools=[
                check_eligibility,
                get_military_status,
                verify_documentation_requirements,
            ],
        )

    @agent
    def document_assistant_specialist(self) -> Agent:
        """Create the document assistant specialist agent."""
        return Agent(
            config=self.agents_config["document_assistant_specialist"],
            llm=self._llm,
            tools=[get_required_documents, generate_form, explain_form_fields],
        )

    @agent
    def manager(self) -> Agent:
        """Create the manager agent that coordinates other agents."""
        return Agent(
            config=self.agents_config["manager"],
            llm=self._llm,
            tools=[],
        )

    @task
    def manager_task(self) -> Task:
        """Create the manager task for coordinating the response."""
        return Task(
            config=self.tasks_config["manager_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create and return the crew with hierarchical process."""
        # Filter out the manager from the agents list (it's set as manager_agent)
        worker_agents = [a for a in self.agents if a.role.strip() != "AI Assistant Manager"]
        return Crew(
            agents=worker_agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager(),
            verbose=True,
        )
