# app/routers/vehicle_router.py
"""
Vehicle management endpoints for multi-vehicle support.
Handles vehicle identification, switching, and listing.
"""

from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from fastapi.security import HTTPBearer  # type: ignore

from app.auth.auth import verify_token
from app.models.vehicle_models import (
    VehicleIdentifyRequest,
    VehicleIdentifyResponse,
    VehicleSwitchRequest,
    VehicleResponse,
    VehicleListResponse,
)
from app.db.vehicle_session import (
    get_vehicle_by_vin,
    create_vehicle,
    create_vehicle_session,
    get_user_vehicles,
    get_active_vehicle_id,
    get_vehicle_by_id,
)

router = APIRouter(
    prefix="/vehicle",
    tags=["Vehicle Management"]
)

security = HTTPBearer()


@router.post("/identify", response_model=VehicleIdentifyResponse)
async def identify_vehicle(
    req: VehicleIdentifyRequest,
    _=Depends(security),
    user=Depends(verify_token),
):
    """
    Identify or register a vehicle by VIN.
    
    If vehicle exists:
        - Ensure it belongs to user
        - Create new active session
        - Return vehicle_id and is_new=false
    
    If vehicle doesn't exist:
        - Create vehicle record
        - Create active session
        - Return vehicle_id and is_new=true
    """
    user_id = user["sub"]
    vin = req.vin.upper()  # Normalize VIN to uppercase
    
    # Check if vehicle already exists
    existing_vehicle = get_vehicle_by_vin(vin)
    
    if existing_vehicle:
        # Verify ownership
        if existing_vehicle["user_id"] != user_id:
            raise HTTPException(
                status_code=403,
                detail="This vehicle is registered to another user"
            )
        
        # Create new session for existing vehicle
        create_vehicle_session(user_id, existing_vehicle["id"])
        
        return VehicleIdentifyResponse(
            vehicle_id=existing_vehicle["id"],
            is_new=False,
            vin=existing_vehicle["vin"],
            model=existing_vehicle.get("model")
        )
    
    else:
        # Create new vehicle
        new_vehicle = create_vehicle(user_id, vin, req.model)
        
        # Create active session
        create_vehicle_session(user_id, new_vehicle["id"])
        
        return VehicleIdentifyResponse(
            vehicle_id=new_vehicle["id"],
            is_new=True,
            vin=new_vehicle["vin"],
            model=new_vehicle.get("model")
        )


@router.get("/current", response_model=VehicleResponse)
async def get_current_vehicle(
    _=Depends(security),
    user=Depends(verify_token),
):
    """
    Get the currently active vehicle for the user.
    Returns 404 if no active vehicle session.
    """
    user_id = user["sub"]
    
    vehicle_id = get_active_vehicle_id(user_id)
    
    if not vehicle_id:
        raise HTTPException(
            status_code=404,
            detail="No active vehicle session"
        )
    
    vehicle = get_vehicle_by_id(vehicle_id, user_id)
    
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Active vehicle not found"
        )
    
    return VehicleResponse(**vehicle)


@router.get("/list", response_model=VehicleListResponse)
async def list_vehicles(
    _=Depends(security),
    user=Depends(verify_token),
):
    """
    List all vehicles owned by the user.
    """
    user_id = user["sub"]
    vehicles = get_user_vehicles(user_id)
    
    return VehicleListResponse(
        vehicles=[VehicleResponse(**v) for v in vehicles]
    )


@router.post("/switch")
async def switch_vehicle(
    req: VehicleSwitchRequest,
    _=Depends(security),
    user=Depends(verify_token),
):
    """
    Switch to a different vehicle.
    Closes current active session and creates new one.
    """
    user_id = user["sub"]
    
    # Verify the vehicle belongs to the user
    vehicle = get_vehicle_by_id(req.vehicle_id, user_id)
    
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found or does not belong to user"
        )
    
    # Create new session (automatically closes existing ones)
    create_vehicle_session(user_id, req.vehicle_id)
    
    return {"success": True, "vehicle_id": req.vehicle_id}
