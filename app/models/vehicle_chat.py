# app/models/vehicle_chat.py

from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    chat_id: str                 # session id
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
