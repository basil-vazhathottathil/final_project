from typing import Optional, List, Dict, Any

from app.db.db import supabase


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def make_issue_key(title: str) -> str:
    """
    Create a stable, deterministic key for an issue.
    This MUST NOT depend on severity or wording intensity.
    """
    return (
        title.lower()
        .strip()
        .replace("-", " ")
        .replace("  ", " ")
        .replace(" ", "_")
    )


# --------------------------------------------------
# Chat summary (ai_chat_summary)
# --------------------------------------------------

def load_chat_summary(vehicle_id: Optional[str]) -> Optional[str]:
    if not vehicle_id:
        return None

    response = (
        supabase
        .table("ai_chat_summary")
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

    # Chat summary is intentionally append-only (historical)
    supabase.table("ai_chat_summary").insert({
        "vehicle_id": vehicle_id,
        "summary": summary,
    }).execute()


# --------------------------------------------------
# Issues (issues_summary) — STABLE UPSERT
# --------------------------------------------------

def load_open_issues(vehicle_id: Optional[str]) -> List[Dict[str, Any]]:
    if not vehicle_id:
        return []

    response = (
        supabase
        .table("issues_summary")
        .select("id, issue_key, title, summary, severity")
        .eq("vehicle_id", vehicle_id)
        .is_("resolved_at", None)
        .order("updated_at", desc=True)
        .execute()
    )

    return response.data or []


def upsert_issue_from_summary(vehicle_id: Optional[str], issue: Dict[str, Any]) -> None:
    if not vehicle_id:
        return

    title = issue.get("title")
    if not title:
        return

    issue_key = make_issue_key(title)

    # --------------------------------------------------
    # Check if this issue already exists
    # --------------------------------------------------
    existing = (
        supabase
        .table("issues_summary")
        .select("id")
        .eq("vehicle_id", vehicle_id)
        .eq("issue_key", issue_key)
        .limit(1)
        .execute()
    )

    if existing.data:
        # -----------------------------
        # UPDATE existing issue
        # -----------------------------
        issue_id = existing.data[0]["id"]

        supabase.table("issues_summary").update({
            "severity": issue.get("severity"),
            "summary": issue.get("summary"),
            "updated_at": "now()",
        }).eq("id", issue_id).execute()

    else:
        # -----------------------------
        # INSERT new issue
        # -----------------------------
        supabase.table("issues_summary").insert({
            "vehicle_id": vehicle_id,
            "issue_key": issue_key,
            "title": title,
            "summary": issue.get("summary"),
            "severity": issue.get("severity"),
        }).execute()

# --------------------------------------------------
# Chat-scoped issue summary (per chat_id)
# --------------------------------------------------

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

    if res.data:
        return res.data[0]["summary"]

    return None


def upsert_chat_issue_summary(
    chat_id: Optional[str],
    vehicle_id: Optional[str],
    summary: str,
    severity: Optional[str] = None,
    title: str = "Active diagnostic issue",
) -> None:
    """
    Upsert a SINGLE evolving issue row per chat.
    """
    if not chat_id or not vehicle_id:
        return

    supabase.table("issues_summary").upsert({
        "chat_id": chat_id,
        "vehicle_id": vehicle_id,
        "title": title,
        "summary": summary,
        "severity": severity or "UNKNOWN",
        "updated_at": "now()",
    }).execute()
