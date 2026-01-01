from uuid import UUID
from pydantic import BaseModel # type: ignore
from typing import List, Optional, Literal


class ChatRequest(BaseModel):
    chat_id: UUID                 # session id
    message: str                  # user message
    vehicle_id: Optional[str] = None


class AgentResponse(BaseModel):
    diagnosis: str
    explanation: str
    severity: float
    action: Literal["DIY", "ASK", "ESCALATE"]
    steps: List[str]
    follow_up_questions: List[str]
    confidence: float
