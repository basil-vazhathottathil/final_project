from datetime import date
from uuid import UUID
from app.core.database import supabase


def create_maintenance(user_id: str, payload):
    data = payload.dict()
    data["user_id"] = user_id

    if data.get("service_date") is None:
        data["service_date"] = date.today()

    return (
        supabase.table("vehicle_maintenance")
        .insert(data)
        .execute()
    )


def list_maintenance(user_id: str):
    return (
        supabase.table("vehicle_maintenance")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )


def list_maintenance_by_vehicle(user_id: str, vehicle_id: UUID):
    return (
        supabase.table("vehicle_maintenance")
        .select("*")
        .eq("user_id", user_id)
        .eq("vehicle_id", vehicle_id)
        .execute()
    )


def update_maintenance(user_id: str, maintenance_id: UUID, payload):
    return (
        supabase.table("vehicle_maintenance")
        .update(payload.dict(exclude_unset=True))
        .eq("id", maintenance_id)
        .eq("user_id", user_id)
        .execute()
    )


def delete_maintenance(user_id: str, maintenance_id: UUID):
    return (
        supabase.table("vehicle_maintenance")
        .delete()
        .eq("id", maintenance_id)
        .eq("user_id", user_id)
        .execute()
    )
