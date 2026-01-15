from datetime import date
from uuid import UUID
from app.db.db import supabase


def _serialize_for_json(data: dict) -> dict:
    """
    Convert non-JSON-serializable objects to safe types
    """
    for k, v in data.items():
        if isinstance(v, UUID):
            data[k] = str(v)
        elif isinstance(v, date):
            data[k] = v.isoformat()
    return data


def create_maintenance_service(user_id: str, payload):
    data = payload.dict()

    # Ensure NOT NULL safety
    if data.get("service_date") is None:
        data["service_date"] = date.today()

    # Trigger safety
    if data.get("odometer_km") == 0:
        data["odometer_km"] = None

    # FK requirement
    data["user_id"] = user_id

    # Never override DB defaults
    data.pop("status", None)

    # 🔴 REQUIRED: serialize UUID + date
    data = _serialize_for_json(data)

    res = (
        supabase
        .table("vehicle_maintenance")
        .insert(data)
        .execute()
    )

    return res.data[0] if res.data else None


def list_maintenance_service(user_id: str):
    res = (
        supabase
        .table("vehicle_maintenance")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


def update_maintenance_service(user_id: str, maintenance_id: str, payload):
    data = payload.dict(exclude_unset=True)

    if data.get("odometer_km") == 0:
        data["odometer_km"] = None

    # 🔴 Serialize here too
    data = _serialize_for_json(data)

    res = (
        supabase
        .table("vehicle_maintenance")
        .update(data)
        .eq("id", maintenance_id)
        .eq("user_id", user_id)
        .execute()
    )

    return res.data[0] if res.data else None


def delete_maintenance_service(user_id: str, maintenance_id: str):
    return (
        supabase
        .table("vehicle_maintenance")
        .delete()
        .eq("id", maintenance_id)
        .execute()
    )
