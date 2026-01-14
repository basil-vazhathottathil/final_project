from app.db.db import supabase

def ensure_user_exists(user_id: str, email: str | None = None, name: str | None = None):
    supabase.table("users").upsert(
        {
            "id": user_id,
            "email": email,
            "name": name,
        },
        on_conflict="id",
    ).execute()
