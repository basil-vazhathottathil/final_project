from app.db.db import supabase


def create_maintenance_service(user_id: str, payload):
    data = payload.dict()
    data["user_id"] = user_id

    return (
        supabase
        .table("vehicle_maintenance")
        .insert(data)
        .execute()
    )


def list_maintenance_service(user_id: str):
    return (
        supabase
        .table("vehicle_maintenance")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )


def update_maintenance_service(user_id: str, maintenance_id: str, payload):
    data = payload.dict(exclude_unset=True)

    return (
        supabase
        .table("vehicle_maintenance")
        .update(data)
        .eq("id", maintenance_id)
        .eq("user_id", user_id)  # ownership enforced
        .execute()
    )


def delete_maintenance_service(user_id: str, maintenance_id: str):
    return (
        supabase
        .table("vehicle_maintenance")
        .delete()
        .eq("id", maintenance_id)
        .eq("user_id", user_id)  # ownership enforced
        .execute()
    )
