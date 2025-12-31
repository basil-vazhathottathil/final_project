from fastapi import FastAPI, Depends  # type: ignore
from fastapi.security import HTTPBearer  # type: ignore

from app.agent.vehicle_agent import run_vehicle_agent
from app.auth.auth import verify_token
from app.models.vehicle_chat import ChatRequest, AgentResponse
from app.db.db import ensure_user_exists   # 👈 ADD THIS

app = FastAPI(title="Vehicle Repair AI Agent")

# Swagger auth UI ONLY
security = HTTPBearer()


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/vehicle/chat", response_model=AgentResponse)
async def chat_vehicle(
    req: ChatRequest,
    _=Depends(security),       # 👈 enables Swagger Authorize button
    user=Depends(verify_token) # 👈 real auth (Clerk)
):
    # ✅ Ensure the Clerk user exists in DB (fixes FK error)
    ensure_user_exists(
        user_id=user["sub"],
        email=user.get("email")   # safe even if email is missing
    )

    return run_vehicle_agent(
        user_input=req.message,
        chat_id=req.chat_id,
        user_id=user["sub"],
        vehicle_id=req.vehicle_id
    )
