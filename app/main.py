from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from app.agent.vehicle_agent import run_vehicle_agent

app = FastAPI(title="Vehicle Repair AI Agent")

class ChatRequest(BaseModel):
    message: str
    conversation_history: str | None = ""

class AgentResponse(BaseModel):
    diagnosis: str
    explanation: str
    severity: float
    action: str
    steps: List[str]
    follow_up_question: str
    confidence: float

@app.post("/vehicle/chat", response_model=AgentResponse)
def chat_vehicle(req: ChatRequest):
    return run_vehicle_agent(
        user_input=req.message,
        conversation_history=req.conversation_history
    )
