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
