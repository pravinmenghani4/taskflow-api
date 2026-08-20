from fastapi import FastAPI
from pydantic import BaseModel

from llm_service import create_prompt
from llm_service import invoke_llm

app = FastAPI()


class TicketRequest(BaseModel):
    text: str


@app.post("/classify")
def classify(ticket: TicketRequest):

    prompt = create_prompt(ticket.text)

    result = invoke_llm(prompt)

    return result
