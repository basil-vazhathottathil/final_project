from fastapi import APIRouter, Depends # type: ignore
from fastapi.security import HTTPBearer # type: ignore

from app.agent.vehicle_agent import run_vehicle_agent
from app.auth.auth import verify_token
from app.models.vehicle_chat import ChatRequest, AgentResponse

router = APIRouter(
    prefix="/vehicle",
    tags=["Vehicle Chat"]
)

security = HTTPBearer()


@router.post("/chat", response_model=AgentResponse)
async def chat_vehicle(
    req: ChatRequest,
    _=Depends(security),          # enables Swagger "Authorize"
    user=Depends(verify_token),   # real auth
):
    return run_vehicle_agent(
        user_input=req.message,
        chat_id=req.chat_id,
        user_id=user["sub"],
        vehicle_id=req.vehicle_id,
        latitude=req.latitude,
        longitude=req.longitude,
    )
