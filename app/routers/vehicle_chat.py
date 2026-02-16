from fastapi import APIRouter, Depends  # type: ignore
from fastapi.security import HTTPBearer  # type: ignore

from app.agent.vehicle_agent import run_vehicle_agent
from app.auth.auth import verify_token, get_active_vehicle
from app.models.vehicle_chat import ChatRequest, AgentResponse
from app.db.users import ensure_user_exists

router = APIRouter(
    prefix="/vehicle",
    tags=["Vehicle Chat"]
)

security = HTTPBearer()


@router.post("/chat", response_model=AgentResponse)
async def chat_vehicle(
    req: ChatRequest,
    _=Depends(security),
    user=Depends(verify_token),
    vehicle_id: str = Depends(get_active_vehicle),  # Auto-fetch from active session
):
    """
    Chat with AI agent about vehicle issues.
    Vehicle context is automatically determined from active session.
    """
    # Ensure FK-safe user record
    ensure_user_exists(
        user_id=user["sub"],
        email=user.get("email"),
        name=user.get("name"),
    )

    return run_vehicle_agent(
        user_input=req.message,
        chat_id=req.chat_id,
        user_id=user["sub"],
        vehicle_id=vehicle_id,  # From active session
        latitude=req.latitude,
        longitude=req.longitude,
    )
