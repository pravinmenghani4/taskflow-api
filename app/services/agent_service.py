"""Azure AI Foundry agent integration.

Uses AgentsClient directly (not AIProjectClient.agents which points to
a different deployment-management API surface).

Compatible with azure-ai-agents >= 1.1.0.
Uses DefaultAzureCredential — works with managed identity in Container Apps
and Cloud Shell / az login locally.
"""
import json
import logging
from functools import lru_cache

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, ListSortOrder
from azure.identity import DefaultAzureCredential

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> AgentsClient:
    return AgentsClient(
        endpoint=settings.azure_foundry_endpoint,
        credential=DefaultAzureCredential(),
    )


def triage_tasks(user_message: str, tasks: list[dict]) -> str:
    """Send a user message + current task list to the agent; return its reply."""
    client = _get_client()
    task_context = json.dumps(tasks, default=str, indent=2)

    thread = client.threads.create()
    try:
        client.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=(
                f"Current TaskFlow tasks:\n{task_context}\n\n"
                f"User request:\n{user_message}"
            ),
        )

        run = client.runs.create_and_process(
            thread_id=thread.id,
            agent_id=settings.azure_agent_id,
        )

        if run.status == "failed":
            logger.error("Agent run failed: %s", run.last_error)
            return "Agent run failed. Please try again."

        messages = client.messages.list(
            thread_id=thread.id,
            order=ListSortOrder.ASCENDING,
        )
        for msg in messages:
            if msg.role == MessageRole.AGENT and msg.text_messages:
                return msg.text_messages[-1].text.value

        return "No response from agent."
    finally:
        client.threads.delete(thread.id)
