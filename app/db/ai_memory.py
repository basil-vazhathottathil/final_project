from typing import Optional, List, Dict, Any

from app.db.db import supabase


# --------------------------------------------------
# Chat summary (ai_reply_summary)
# --------------------------------------------------

def load_chat_summary(vehicle_id: Optional[str]) -> Optional[str]:
    if not vehicle_id:
        return None

    response = (
        supabase
        .table("ai_reply_summary")
        .select("summary")
        .eq("vehicle_id", vehicle_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["summary"]

    return None


def upsert_chat_summary(vehicle_id: Optional[str], summary: str) -> None:
    if not vehicle_id:
        return

    supabase.table("ai_reply_summary").insert({
        "vehicle_id": vehicle_id,
        "summary": summary,
    }).execute()


# --------------------------------------------------
# Issues (issues_summary)
# --------------------------------------------------

def load_open_issues(vehicle_id: Optional[str]) -> List[Dict[str, Any]]:
    if not vehicle_id:
        return []

    response = (
        supabase
        .table("issues_summary")
        .select("id, title, summary, severity")
        .eq("vehicle_id", vehicle_id)
        .is_("resolved_at", None)
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def upsert_issue_from_summary(vehicle_id: Optional[str], issue: Dict[str, Any]) -> None:
    if not vehicle_id:
        return

    supabase.table("issues_summary").insert({
        "vehicle_id": vehicle_id,
        "title": issue.get("title"),
        "summary": issue.get("summary"),
        "severity": issue.get("severity"),
    }).execute()
