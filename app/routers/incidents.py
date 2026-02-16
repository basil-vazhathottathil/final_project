from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

from app.auth.auth import verify_token, get_active_vehicle
from app.db.db import supabase

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)

security = HTTPBearer()


class UpdateStatusRequest(BaseModel):
    status: str  # "open" or "resolved"


@router.get("/history")
async def get_incidents_history(
    _=Depends(security),
    user=Depends(verify_token),
    vehicle_id: str = Depends(get_active_vehicle),  # Auto-fetch from active session
):
    """
    Get all incidents for the active vehicle.
    Returns incidents sorted by severity (high first) and created_at (newest first).
    """
    user_id = user["sub"]
    
    try:
        # Fetch incidents for active vehicle only
        res = supabase.table("vehicle_incidents") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("vehicle_id", vehicle_id) \
            .order("created_at", desc=True) \
            .execute()
        
        if not res.data:
            return []
        
        # Sort by severity (high > medium > low) then by date
        severity_order = {"high": 0, "medium": 1, "low": 2}
        
        sorted_incidents = sorted(
            res.data,
            key=lambda x: (
                severity_order.get(x.get("severity", "low"), 3),
                -1 * (len(x.get("created_at", "")) or 0)  # Newest first
            )
        )
        
        return sorted_incidents
    
    except Exception as e:
        print(f"Error fetching incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch incidents")


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    _=Depends(security),
    user=Depends(verify_token),
    vehicle_id: str = Depends(get_active_vehicle),  # Auto-fetch from active session
):
    """
    Get details for a specific incident.
    Ensures incident belongs to active vehicle.
    """
    user_id = user["sub"]
    
    try:
        res = supabase.table("vehicle_incidents") \
            .select("*") \
            .eq("id", incident_id) \
            .eq("user_id", user_id) \
            .eq("vehicle_id", vehicle_id) \
            .single() \
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return res.data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch incident")


@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    req: UpdateStatusRequest,
    _=Depends(security),
    user=Depends(verify_token),
    vehicle_id: str = Depends(get_active_vehicle),  # Auto-fetch from active session
):
    """
    Update the status of an incident (open/resolved).
    Ensures incident belongs to active vehicle.
    """
    user_id = user["sub"]
    
    # Validate status
    if req.status not in ["open", "resolved"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be 'open' or 'resolved'"
        )
    
    try:
        # Verify the incident belongs to the user and active vehicle
        check = supabase.table("vehicle_incidents") \
            .select("id") \
            .eq("id", incident_id) \
            .eq("user_id", user_id) \
            .eq("vehicle_id", vehicle_id) \
            .single() \
            .execute()
        
        if not check.data:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Update the status
        res = supabase.table("vehicle_incidents") \
            .update({"status": req.status}) \
            .eq("id", incident_id) \
            .execute()
        
        return {
            "success": True,
            "incident_id": incident_id,
            "status": req.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating incident status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update incident status")
