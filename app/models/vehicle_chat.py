from uuid import UUID
from pydantic import BaseModel # type: ignore
from typing import List, Optional, Literal


class ChatRequest(BaseModel):
    chat_id: UUID                 # session id
    message: str                  # user message
    vehicle_id: Optional[str] = None
    latitude: float | None = None
    longitude: float | None = None

class AgentResponse(BaseModel):
    diagnosis: str
    explanation: str
    severity: float
    action: str
    steps: list[str]
    follow_up_questions: list[str]
    confidence: float
    chat_id: UUID  

