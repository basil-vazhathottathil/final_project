from pydantic import BaseModel # type: ignore
from typing import List, Optional, Literal


class ChatRequest(BaseModel):
    chat_id: Optional[str] = None
    issue_id: Optional[str] = None
    message: str
    # vehicle_id removed - comes from active session via get_active_vehicle dependency
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
    chat_id: str
    youtube_urls: list[str] = []
