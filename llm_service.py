import json
import logging

from openai import OpenAI
from openai import APITimeoutError
from pydantic import ValidationError

from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from schemas import TicketClassification


# ---------------------------------------------------
# Logging
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# OpenAI Client
# ---------------------------------------------------

client = OpenAI(
    api_key="YOUR_OPENAI_API_KEY"
)


# ---------------------------------------------------
# Prompt Builder
# ---------------------------------------------------

def create_prompt(ticket_text: str) -> str:
    """
    Builds a structured prompt for ticket classification.
    """

    return f"""
You are a support ticket classification assistant.

Analyze the ticket and return ONLY valid JSON.

Ticket:
{ticket_text}

Return this exact schema:

{{
  "priority": "",
  "category": "",
  "sentiment": ""
}}

Rules:
- Return JSON only
- No markdown
- No explanation
- No additional text
"""


# ---------------------------------------------------
# LLM Invocation
# ---------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2),
    reraise=True
)
def invoke_llm(prompt: str):
    """
    Invokes the LLM with:
    - timeout protection
    - retry logic
    - JSON parsing
    - schema validation
    """

    try:

        logger.info("Calling LLM...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            timeout=15,
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON generation assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content

        logger.info(f"Raw Response: {content}")

        # ------------------------------------
        # Parse JSON
        # ------------------------------------

        data = json.loads(content)

        # ------------------------------------
        # Validate Schema
        # ------------------------------------

        validated = TicketClassification(**data)

        logger.info("Schema validation successful")

        return validated.model_dump()

    except APITimeoutError:

        logger.error("LLM request timed out")

        raise

    except json.JSONDecodeError:

        logger.error("Malformed JSON returned by LLM")

        return {
            "status": "error",
            "message": "Malformed LLM response",
            "raw_response": content
        }

    except ValidationError as validation_error:

        logger.error(
            f"Schema validation failed: {validation_error}"
        )

        return {
            "status": "error",
            "message": "Schema validation failed",
            "details": str(validation_error)
        }

    except Exception as e:

        logger.exception("Unexpected error")

        return {
            "status": "error",
            "message": str(e)
        }
