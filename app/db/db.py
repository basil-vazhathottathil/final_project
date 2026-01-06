# Database helpers for AI chat sessions (short-term memory)

from uuid import UUID
from typing import List, Dict, Any

from supabase import create_client  # type: ignore
from app.config import SUPABASE_URL, SUPABASE_SERVICE_KEY


# --------------------------------------------------
# Supabase client
# --------------------------------------------------

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)


# --------------------------------------------------
# Save one chat turn (STRUCTURED)
# --------------------------------------------------

def save_chat_turn(
    chat_id: UUID,
    user_id: str,
    vehicle_id: str | None,
    prompt: str,
    response_ai: Dict[str, Any],   # 👈 structured JSON
) -> None:
    """
    Save one user + AI exchange.
    `response_ai` MUST be a parsed JSON dict.
    """
    supabase.table("ai_chat_history").insert({
        "chat_id": str(chat_id),
        "user_id": user_id,
        "vehicle_id": vehicle_id,
        "prompt": prompt,
        "response_ai": response_ai,   # stored as jsonb
    }).execute()


# --------------------------------------------------
# Load short-term memory (TEXT, for LLM context)
# --------------------------------------------------

def load_short_term_memory(chat_id: UUID, limit: int = 5) -> str:
    """
    Returns conversation history as plain text.
    Used ONLY for LLM conversational context.
    """
    response = (
        supabase
        .table("ai_chat_history")
        .select("prompt, response_ai")
        .eq("chat_id", str(chat_id))
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    rows = response.data or []
    rows.reverse()  # oldest → newest

    history_lines: List[str] = []

    for row in rows:
        history_lines.append(f"User: {row['prompt']}")

        agent = row.get("response_ai")
        if isinstance(agent, dict):
            history_lines.append(
                f"Agent: diagnosis={agent.get('diagnosis')}, action={agent.get('action')}"
            )
        else:
            history_lines.append("Agent: (response unavailable)")

    return "\n".join(history_lines)


# --------------------------------------------------
# Load short-term memory (STRUCTURED, for agent logic)
# --------------------------------------------------

def load_short_term_memory_structured(
    chat_id: UUID,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Returns structured chat history for agent reasoning.

    Example:
    [
      {
        "user": "...",
        "agent": {
            "diagnosis": "...",
            "action": "ASK",
            "confidence": 0.7
        }
      }
    ]
    """
    response = (
        supabase
        .table("ai_chat_history")
        .select("prompt, response_ai")
        .eq("chat_id", str(chat_id))
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    rows = response.data or []
    rows.reverse()  # oldest → newest

    history: List[Dict[str, Any]] = []

    for row in rows:
        history.append({
            "user": row["prompt"],
            "agent": row["response_ai"]
            if isinstance(row.get("response_ai"), dict)
            else None
        })

    return history


# --------------------------------------------------
# User session helpers
# --------------------------------------------------

def get_user_sessions(user_id: str):
    """
    Get all unique chat sessions for a user.
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
    """
    Ensure user exists in users table.
    """
    supabase.table("users").upsert({
        "id": user_id,
        "email": email
    }).execute()
