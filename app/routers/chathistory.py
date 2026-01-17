from fastapi import APIRouter, Depends, HTTPException
from app.db.db import supabase
from app.auth.auth import get_current_user_id

router = APIRouter(prefix="/chat", tags=["Chat History"])

#gives last row for each chat_id for history card in frontend
@router.get("/history")
async def get_chat_history(user=Depends(get_current_user_id)):
    res = supabase.table("ai_chat_history") \
        .select("chat_id, prompt, response_ai, created_at") \
        .eq("user_id", user) \
        .order("created_at", desc=True) \
        .execute()

    if not res.data:
        return []

    conversations = {}

    for row in res.data:
        cid = row["chat_id"]
        if not cid:
            continue

        if cid not in conversations:
            conversations[cid] = {
                "id": cid,
                "title": (row["prompt"] or "")[:60],
                "preview": (row["prompt"] or "")[:120],
                "lastMessage": row["response_ai"],
                "timestamp": row["created_at"],
                "messageCount": 1,
            }
        else:
            conversations[cid]["messageCount"] += 1
            conversations[cid]["lastMessage"] = row["response_ai"]
            conversations[cid]["timestamp"] = row["created_at"]

    return list(conversations.values())


#loads all messages for a specific chat_id
@router.get("/{chat_id}")
async def get_chat(chat_id: str, user=Depends(get_current_user_id)):
    res = supabase.table("ai_chat_history") \
        .select("prompt, response_ai, created_at") \
        .eq("chat_id", chat_id) \
        .eq("user_id", user) \
        .order("created_at") \
        .execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Chat not found")

    return res.data
