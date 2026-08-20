from pydantic import BaseModel

class TicketClassification(BaseModel):
    priority: str
    category: str
    sentiment: str

