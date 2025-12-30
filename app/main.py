from fastapi import FastAPI, Depends
from app.agent.vehicle_agent import run_vehicle_agent
from app.auth.auth import verify_token
from app.models.vehicle_chat import ChatRequest, AgentResponse

app = FastAPI(title="Vehicle Repair AI Agent")


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/vehicle/chat", response_model=AgentResponse)
async def chat_vehicle(
    req: ChatRequest,
    user=Depends(verify_token),  # 🔐 Clerk protected
):
    return run_vehicle_agent(
        user_input=req.message,
        chat_id=req.chat_id,          # ✅ session id
        user_id=user["sub"],          # Clerk user id
        #vehicle_id=req.vehicle_id     # optional
    )
