"""Create the TaskFlow triage agent in Azure AI Foundry.

Run once, then save the printed agent ID to your .env as AZURE_AGENT_ID.

Uses AgentsClient directly (recommended for azure-ai-agents >= 1.1.0).

Usage:
    python scripts/create_agent.py
    (Cloud Shell is already authenticated — no az login needed)
"""
import os
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import CodeInterpreterTool
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = "https://myfndryq.services.ai.azure.com/api/projects/proj-default"

# Use AgentsClient directly — avoids the AIProjectClient.agents sub-resource
# which points to a different (deployment) API surface
agents_client = AgentsClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

with agents_client:
    agent = agents_client.create_agent(
        model="gpt-4o",  # must match a deployed model name in your Foundry project
        name="taskflow-triage-agent",
        instructions="""You are a task planning and triage assistant for TaskFlow.
Help users:
- Break down vague requests into concrete tasks with clear titles and descriptions
- Suggest priority (todo / in_progress / done) and effort estimates
- Identify blockers and dependencies between tasks
- Summarise the current task list and flag overdue or stalled items
Always return structured suggestions the app can act on.""",
        tools=CodeInterpreterTool().definitions,
    )

    print(f"\nAgent created successfully!")
    print(f"Agent ID : {agent.id}")
    print(f"Agent name: {agent.name}")
    print(f"\nAdd to your .env / Container App env vars:")
    print(f"AZURE_FOUNDRY_ENDPOINT={PROJECT_ENDPOINT}")
    print(f"AZURE_AGENT_ID={agent.id}")
