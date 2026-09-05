# Azure AI Foundry Agent Integration

Step-by-step guide to wiring an Azure AI Foundry agent into the TaskFlow API.
Covers agent definition, Prompt Flow prototyping, API exposure, and monitoring.

---

## Prerequisites

- Azure AI Foundry resource already created
- TaskFlow API deployed to Azure Container Apps (`taskflow-api` in `rg1`)
- ACR image pushed (`myacrshw.azurecr.io/taskflow-api:v1`)

---

## Step 1 — Install the SDK

```bash
pip install azure-ai-projects azure-ai-agents azure-identity
```

Add to `requirements.txt`:
```
azure-ai-projects==1.0.0b11
azure-ai-agents==1.0.0b11
azure-identity==1.19.0
```

---

## Step 2 — Define the Agent

### 2a — Create the agent (run once, save the agent ID)

> Uses `AgentsClient` directly from `azure.ai.agents` — **not** `AIProjectClient.agents`
> which points to a different deployment-management API surface and does not have
> `create_agent`. Compatible with `azure-ai-agents >= 1.1.0`.

```python
# scripts/create_agent.py
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import CodeInterpreterTool
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = "https://myfndryq.services.ai.azure.com/api/projects/proj-default"

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
```

```bash
# Cloud Shell is already authenticated — no az login needed
python scripts/create_agent.py
```

Expected output:
```
Agent created successfully!
Agent ID : asst_xxxxxxxxxxxxxxxxxx
Agent name: taskflow-triage-agent

Add to your .env / Container App env vars:
AZURE_FOUNDRY_ENDPOINT=https://myfndryq.services.ai.azure.com/api/projects/proj-default
AZURE_AGENT_ID=asst_xxxxxxxxxxxxxxxxxx
```

> **Why not `AIProjectClient.agents`?**  
> `AIProjectClient.agents` is the Foundry *deployment management* API (list, enable,
> disable agents-as-services). `AgentsClient` from `azure.ai.agents` is the
> conversational Agents SDK with `create_agent`, threads, messages, and runs.

---

## Step 3 — Prototype in Prompt Flow

### 3a — Install Prompt Flow

```bash
pip install promptflow promptflow-azure
```

### 3b — Create the flow

```bash
mkdir -p promptflow/taskflow-triage
```

**`promptflow/taskflow-triage/flow.dag.yaml`**
```yaml
inputs:
  user_message:
    type: string
  task_context:
    type: string
    default: "[]"

outputs:
  agent_reply:
    type: string
    reference: ${triage_agent.output}

nodes:
  - name: triage_agent
    type: python
    source:
      type: code
      path: triage_node.py
    inputs:
      user_message: ${inputs.user_message}
      task_context: ${inputs.task_context}
```

**`promptflow/taskflow-triage/triage_node.py`**
```python
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import MessageRole
from azure.identity import DefaultAzureCredential
import os, json

def triage_agent(user_message: str, task_context: str) -> str:
    client = AIProjectClient(
        endpoint=os.environ["AZURE_FOUNDRY_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    thread = client.agents.threads.create()
    client.agents.messages.create(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=f"Current tasks:\n{task_context}\n\nUser request:\n{user_message}",
    )
    run = client.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=os.environ["AZURE_AGENT_ID"],
    )
    messages = client.agents.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
```

### 3c — Run test prompts and evaluators

```bash
# Single test run
pf flow test \
  --flow promptflow/taskflow-triage \
  --inputs user_message="I need to build a login page" task_context="[]"

# Batch evaluation
pf run create \
  --flow promptflow/taskflow-triage \
  --data promptflow/test_data.jsonl \
  --stream \
  --name taskflow-triage-eval-1
```

**`promptflow/test_data.jsonl`** (sample eval data):
```jsonl
{"user_message": "Set up CI/CD pipeline", "task_context": "[]"}
{"user_message": "Fix login bug reported by 3 users", "task_context": "[{\"title\": \"Login page\", \"status\": \"in_progress\"}]"}
{"user_message": "What should I work on next?", "task_context": "[{\"title\": \"Write tests\", \"status\": \"todo\"}, {\"title\": \"Deploy\", \"status\": \"todo\"}]"}
```

```bash
# Run built-in quality evaluators
pf run create \
  --flow azure:azureml://registries/azureml/models/gpt-coherence \
  --run taskflow-triage-eval-1 \
  --column-mapping groundtruth="\${data.expected}" prediction="\${run.outputs.agent_reply}"
```

---

## Step 4 — Deploy & Expose as an API

### 4a — Add config vars to `app/core/config.py`

```python
# Add inside the Settings class
azure_foundry_endpoint: str = ""
azure_agent_id: str = ""
```

### 4b — Create `app/services/agent_service.py`

```python
"""Azure AI Foundry agent integration.

Wraps the Foundry Agents SDK so routes stay thin.
Uses DefaultAzureCredential — works with managed identity in Container Apps
and az login locally with no secrets to manage.
"""
import json
import logging
from functools import lru_cache

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import MessageRole
from azure.identity import DefaultAzureCredential

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> AIProjectClient:
    return AIProjectClient(
        endpoint=settings.azure_foundry_endpoint,
        credential=DefaultAzureCredential(),
    )


def triage_tasks(user_message: str, tasks: list[dict]) -> str:
    """Send a user message + current task list to the agent; return its reply."""
    client = _get_client()
    task_context = json.dumps(tasks, default=str, indent=2)

    thread = client.agents.threads.create()
    try:
        client.agents.messages.create(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=(
                f"Current TaskFlow tasks:\n{task_context}\n\n"
                f"User request:\n{user_message}"
            ),
        )
        run = client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=settings.azure_agent_id,
        )
        if run.status == "failed":
            logger.error("Agent run failed: %s", run.last_error)
            return "Agent run failed. Please try again."

        messages = client.agents.messages.list(thread_id=thread.id)
        return messages.data[0].content[0].text.value
    finally:
        # Clean up thread to avoid orphaned state
        client.agents.threads.delete(thread.id)
```

### 4c — Create `app/api/routes/agent.py`

```python
"""Agent triage route — thin HTTP wrapper around agent_service."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import agent_service, task_service

router = APIRouter(prefix="/agent", tags=["agent"])


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TriageResponse(BaseModel):
    reply: str


@router.post("/triage", response_model=TriageResponse)
def triage(payload: TriageRequest, db: Session = Depends(get_db)):
    """Send a natural-language request to the AI agent.
    The agent sees the current task list and returns planning suggestions.
    """
    tasks = [
        {"id": t.id, "title": t.title, "status": t.status, "description": t.description}
        for t in task_service.list_tasks(db)
    ]
    try:
        reply = agent_service.triage_tasks(payload.message, tasks)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent error: {exc}",
        )
    return TriageResponse(reply=reply)
```

### 4d — Wire the router into `app/main.py`

```python
# Add this import alongside the others
from app.api.routes import health, projects, tasks, agent

# Add this line alongside the other include_router calls
app.include_router(agent.router)
```

### 4e — Grant managed identity access

```bash
# Enable system-assigned identity on the container app
az containerapp identity assign \
  --name taskflow-api \
  --resource-group rg1 \
  --system-assigned

# Get the principal ID
PRINCIPAL_ID=$(az containerapp show \
  --name taskflow-api \
  --resource-group rg1 \
  --query "identity.principalId" -o tsv)

# Grant it the Azure AI Developer role on your Foundry resource
FOUNDRY_RESOURCE_ID=$(az cognitiveservices account show \
  --name <your-foundry-resource-name> \
  --resource-group rg1 \
  --query id -o tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Azure AI Developer" \
  --scope $FOUNDRY_RESOURCE_ID
```

### 4f — Set env vars on the Container App

```bash
az containerapp update \
  --name taskflow-api \
  --resource-group rg1 \
  --set-env-vars \
      "AZURE_FOUNDRY_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project>" \
      "AZURE_AGENT_ID=<agent-id-from-step-2>"
```

### 4g — Test the endpoint

```bash
APP_URL=$(az containerapp show \
  --name taskflow-api \
  --resource-group rg1 \
  --query "properties.configuration.ingress.fqdn" -o tsv)

curl -X POST "https://$APP_URL/agent/triage" \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I work on next?"}'
```

---

## Step 5 — Trace & Monitor

### 5a — Enable Application Insights

```bash
# Get your App Insights connection string
AI_CONN=$(az monitor app-insights component show \
  --app <your-appinsights-name> \
  --resource-group rg1 \
  --query connectionString -o tsv)

az containerapp update \
  --name taskflow-api \
  --resource-group rg1 \
  --set-env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=$AI_CONN"
```

### 5b — Add tracing to the app

```bash
pip install azure-monitor-opentelemetry
```

Add to `requirements.txt`:
```
azure-monitor-opentelemetry==1.6.4
```

At the top of `app/main.py`, before any other imports:

```python
import os
if conn_str := os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=conn_str)
```

### 5c — Monitor in the portal

| What to check | Where |
|---|---|
| Live agent traces (inputs, outputs, latency) | AI Foundry portal → Tracing tab |
| Request logs, exceptions, latency | Azure Monitor → Application Insights → Transaction search |
| Agent quality scores (coherence, relevance) | AI Foundry portal → Evaluations → Online evaluations |
| Responsible AI content filter hits | AI Foundry portal → Content filters → View logs |

### 5d — Sample Log Analytics queries

```kusto
// Agent call latency over time
traces
| where message contains "agent"
| summarize avg(todouble(customDimensions.duration_ms)) by bin(timestamp, 5m)
| render timechart

// Error rate
exceptions
| where outerMessage contains "Agent"
| summarize count() by bin(timestamp, 1h)
```

---

## Local Development

Add to your `.env` file:

```bash
AZURE_FOUNDRY_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_AGENT_ID=<id-from-step-2>
# APPLICATIONINSIGHTS_CONNECTION_STRING=  # optional locally
```

Run `az login` — `DefaultAzureCredential` picks it up automatically. No secrets needed in local dev.

---

## Order of Operations (Quick Reference)

| # | Action |
|---|---|
| 1 | `python scripts/create_agent.py` → save the agent ID |
| 2 | Add `agent_service.py` and `agent.py` route, wire into `main.py` |
| 3 | Prototype and evaluate in Prompt Flow |
| 4 | `az containerapp update` with `AZURE_FOUNDRY_ENDPOINT` and `AZURE_AGENT_ID` |
| 5 | `curl https://$APP_URL/agent/triage` to verify |
| 6 | Check traces in AI Foundry portal and Application Insights |
