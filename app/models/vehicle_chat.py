# app/models/vehicle_chat.py

from uuid import UUID
from pydantic import BaseModel # type: ignore
from typing import List, Optional


class ChatRequest(BaseModel):
    chat_id: UUID                 # session id
    message: str                 # user message
    vehicle_id: Optional[str] = None


class AgentResponse(BaseModel):
    diagnosis: str
    explanation: str
    severity: float
    action: str
    steps: List[str]
    follow_up_question: str
    confidence: float
