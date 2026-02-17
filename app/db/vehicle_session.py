# app/db/vehicle_session.py
"""
Vehicle session management for multi-vehicle support.
Handles active vehicle tracking and session lifecycle.
"""

from typing import Dict, Any, List
from app.db.db import supabase
from postgrest.exceptions import APIError


def get_active_vehicle_id(user_id: str) -> str | None:
    """
    Get the currently active vehicle for a user.
    Returns vehicle_id or None if no active session.
    """
    try:
        response = (
            supabase
            .table("vehicle_sessions")
            .select("vehicle_id")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .single()
            .execute()
        )
        
        if response.data:
            return response.data["vehicle_id"]
        return None
    except APIError:
        # No active session found
        return None


def close_active_sessions(user_id: str) -> None:
    """
    Close all active vehicle sessions for a user.
    Sets is_active=false and ended_at=now().
    """
    from datetime import datetime, timezone
    
    supabase.table("vehicle_sessions").update({
        "is_active": False,
        "ended_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user_id).eq("is_active", True).execute()


def create_vehicle_session(user_id: str, vehicle_id: str) -> Dict[str, Any]:
    """
    Create a new active vehicle session.
    Automatically closes any existing active sessions first.
    """
    # Close any existing active sessions
    close_active_sessions(user_id)
    
    # Create new active session
    response = supabase.table("vehicle_sessions").insert({
        "user_id": user_id,
        "vehicle_id": vehicle_id,
        "is_active": True
    }).execute()
    
    return response.data[0] if response.data else {}


def get_vehicle_by_vin(vin: str) -> Dict[str, Any] | None:
    """
    Find a vehicle by its VIN number.
    Returns vehicle record or None if not found.
    """
    try:
        response = (
            supabase
            .table("vehicles")
            .select("*")
            .eq("vin", vin)
            .single()
            .execute()
        )
        
        return response.data if response.data else None
    except APIError:
        # Vehicle not found
        return None


def create_vehicle(user_id: str, vin: str, model: str | None = None) -> Dict[str, Any]:
    """
    Create a new vehicle record.
    """
    vehicle_data = {
        "user_id": user_id,
        "vin": vin
    }
    
    # Only add model if provided (column is nullable in DB)
    if model:
        vehicle_data["model"] = model
    
    response = supabase.table("vehicles").insert(vehicle_data).execute()
    
    return response.data[0] if response.data else {}


def get_user_vehicles(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all vehicles owned by a user.
    """
    response = (
        supabase
        .table("vehicles")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    
    return response.data or []


def get_vehicle_by_id(vehicle_id: str, user_id: str) -> Dict[str, Any] | None:
    """
    Get a specific vehicle, ensuring it belongs to the user.
    """
    try:
        response = (
            supabase
            .table("vehicles")
            .select("*")
            .eq("id", vehicle_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        
        return response.data if response.data else None
    except APIError:
        # Vehicle not found
        return None
