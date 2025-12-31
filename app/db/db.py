# Database helpers for AI chat sessions (short-term memory)

from uuid import UUID
from supabase import create_client  # type: ignore
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Create Supabase client
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)


def save_chat_turn(
    chat_id: UUID,               # ✅ UUID here
    user_id: str,
    vehicle_id: str | None,
    prompt: str,
    response_ai: str
) -> None:
    """
    Save one user + AI exchange
    """
    supabase.table("ai_chat_history").insert({
        "chat_id": str(chat_id),  # ✅ convert ONLY here
        "user_id": user_id,
        "vehicle_id": vehicle_id,
        "prompt": prompt,
        "response_ai": response_ai
    }).execute()


def load_short_term_memory(chat_id: UUID, limit: int = 5) -> str:
    """
    Load recent conversation for a session
    """
    response = (
        supabase
        .table("ai_chat_history")
        .select("prompt, response_ai")
        .eq("chat_id", str(chat_id))   # ✅ convert ONLY here
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    rows = response.data or []
    rows.reverse()  # oldest → newest

    history = []
    for row in rows:
        history.append(f"user: {row['prompt']}")
        history.append(f"assistant: {row['response_ai']}")

    return "\n".join(history)


def get_user_sessions(user_id: str):
    """
    Get all chat sessions for a user
    """
    response = (
        supabase
        .table("ai_chat_history")
        .select("chat_id")
        .eq("user_id", user_id)
        .execute()
    )

    return list({row["chat_id"] for row in response.data or []})

def ensure_user_exists(user_id: str, email: str | None = None):
    supabase.table("users").upsert({
        "id": user_id,
        "email": email
    }).execute()
