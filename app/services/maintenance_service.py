from datetime import date
from app.db.db import supabase


def create_maintenance_service(user_id: str, payload):
    data = payload.dict()

    # ✅ Ensure NOT NULL column safety
    if data.get("service_date") is None:
        data["service_date"] = date.today()

    # ✅ Never send 0 (breaks enforce_odometer trigger)
    if data.get("odometer_km") == 0:
        data["odometer_km"] = None

    # ✅ Required FK
    data["user_id"] = user_id

    # ❌ NEVER override DB defaults
    data.pop("status", None)

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

    # ✅ Prevent trigger failure
    if data.get("odometer_km") == 0:
        data["odometer_km"] = None

    res = (
        supabase
        .table("vehicle_maintenance")
        .update(data)
        .eq("id", maintenance_id)
        .eq("user_id", user_id)  # ownership enforced
        .execute()
    )

    return res.data[0] if res.data else None


def delete_maintenance_service(user_id: str, maintenance_id: str):
    (
        supabase
        .table("vehicle_maintenance")
        .delete()
        .eq("id", maintenance_id)
        .eq("user_id", user_id)
        .execute()
    )

    return {"deleted": True}
