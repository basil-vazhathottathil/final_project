from typing import Optional, List, Dict, Any
from app.db.db import supabase


# Helpers
def make_issue_key(title: str) -> str:
    return (
        title.lower()
        .strip()
        .replace("-", " ")
        .replace("  ", " ")
        .replace(" ", "_")
    )


# ai_chat_summary (one row per chat)
def load_chat_summary(chat_id: Optional[str]) -> Optional[str]:
    if not chat_id:
        return None

    res = (
        supabase
        .table("ai_chat_summary")
        .select("summary")
        .eq("chat_id", chat_id)
        .limit(1)
        .execute()
    )

    return res.data[0]["summary"] if res.data else None


def upsert_chat_summary(
    chat_id: Optional[str],
    vehicle_id: Optional[str],
    summary: str,
) -> None:
    if not chat_id or not vehicle_id:
        return

    supabase.table("ai_chat_summary").upsert(
        {
            "chat_id": chat_id,
            "vehicle_id": vehicle_id,
            "summary": summary,
        },
        on_conflict="chat_id",
    ).execute()


# issues_summary (vehicle-level issues)
def load_open_issues(vehicle_id: Optional[str]) -> List[Dict[str, Any]]:
    if not vehicle_id:
        return []

    res = (
        supabase
        .table("issues_summary")
        .select("id, issue_key, title, summary, severity")
        .eq("vehicle_id", vehicle_id)
        .is_("resolved_at", None)
        .order("updated_at", desc=True)
        .execute()
    )

    return res.data or []


def upsert_issue_from_summary(
    vehicle_id: Optional[str],
    chat_id: Optional[str],
    issue: Dict[str, Any],
) -> None:
    if not vehicle_id or not chat_id:
        return

    title = issue.get("title")
    if not title:
        return

    issue_key = make_issue_key(title)

    existing = (
        supabase
        .table("issues_summary")
        .select("id")
        .eq("chat_id", chat_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        supabase.table("issues_summary").update({
            "title": title,
            "summary": issue.get("summary"),
            "severity": issue.get("severity"),
            "issue_key": issue_key,
            "updated_at": "now()",
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("issues_summary").insert({
            "vehicle_id": vehicle_id,
            "chat_id": chat_id,
            "issue_key": issue_key,
            "title": title,
            "summary": issue.get("summary"),
            "severity": issue.get("severity"),
        }).execute()


# issues_summary (chat-scoped view)
def load_chat_issue_summary(chat_id: Optional[str]) -> Optional[str]:
    if not chat_id:
        return None

    res = (
        supabase
        .table("issues_summary")
        .select("summary")
        .eq("chat_id", chat_id)
        .limit(1)
        .execute()
    )

    return res.data[0]["summary"] if res.data else None
