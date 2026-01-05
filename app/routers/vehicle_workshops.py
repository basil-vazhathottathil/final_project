from fastapi import APIRouter, Depends, Query # type: ignore
from fastapi.security import HTTPBearer # type: ignore

from app.auth.auth import verify_token
from app.agent.services.workshop_giver import get_workshop_tool
from app.models.workshop import WorkshopResponse

router = APIRouter(
    prefix="/vehicle",
    tags=["Vehicle Workshops"]
)

security = HTTPBearer()


@router.get("/workshops", response_model=WorkshopResponse)
async def get_nearby_workshops(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    _=Depends(security),
    user=Depends(verify_token),
):
    workshop_tool = get_workshop_tool()

    result = workshop_tool.func(
        {"latitude": latitude, "longitude": longitude}
    )

    return {
        "maps_urls": result.get("maps_urls", [])
    }
