import json
import re
from uuid import UUID
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

from app.config import GROQ_API_KEY, TAVILY_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.db.db import load_short_term_memory, save_chat_turn
from app.data import OBD_CODES


if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")


# -----------------------------
# LLM setup
# -----------------------------

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.2,
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", vehicle_prompt),
        (
            "human",
            """Conversation history:
{conversation_history}

User issue:
{user_input}
"""
        ),
    ]
)


# -----------------------------
# Web search setup
# -----------------------------

tavily = TavilyClient(api_key=TAVILY_API_KEY)

YOUTUBE_INTENT_KEYWORDS = [
    "youtube",
    "video",
    "tutorial",
    "how to",
    "guide",
    "watch",
]


def wants_youtube(text: str) -> bool:
    return any(k in text.lower() for k in YOUTUBE_INTENT_KEYWORDS)


def web_search_youtube(query: str) -> List[str]:
    response = tavily.search(
        query=f"site:youtube.com {query}",
        max_results=5,
    )
    return [r["url"] for r in response.get("results", []) if "url" in r]


# -----------------------------
# Helpers
# -----------------------------

def extract_obd_codes(text: str) -> List[str]:
    """
    Extract P / B / C / U OBD-II codes from text
    """
    return re.findall(r"\b[PBCU]\d{4}\b", text.upper())


def remove_duplicate_questions(questions: List[str], history: str) -> List[str]:
    return [q for q in questions if q.lower() not in history.lower()]


def normalize_agent_response(resp: dict, history: str) -> dict:
    action = resp.get("action", "ESCALATE")

    if action not in {"DIY", "ASK", "ESCALATE"}:
        resp["action"] = "ESCALATE"

    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", [])
    resp.setdefault("youtube_urls", [])
    resp.setdefault("severity", 0.7)
    resp.setdefault("confidence", 0.5)

    if resp["action"] == "ASK":
        resp["steps"] = []
        resp["youtube_urls"] = []
        resp["follow_up_questions"] = remove_duplicate_questions(
            resp["follow_up_questions"], history
        )

        # 🚨 ASK must always ask something
        if not resp["follow_up_questions"]:
            resp["follow_up_questions"] = [
                "Does the engine idle smoothly or feel rough?",
                "Do you hear any unusual hissing or air-leak sounds?",
                "Has fuel consumption changed recently?",
            ]

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


# -----------------------------
# OBD logic (DATA-DRIVEN)
# -----------------------------

def apply_obd_logic(resp: dict, user_input: str) -> dict:
    codes = extract_obd_codes(user_input)
    if not codes:
        return resp

    code = codes[0]
    obd = OBD_CODES.get(code)
    if not obd:
        return resp

    # 🔒 Deterministic diagnosis
    resp["diagnosis"] = f"{code}: {obd['meaning']}"
    resp["explanation"] = obd["description"]

    # 🚨 Safety first
    if not obd["diy_possible"]:
        resp["action"] = "ESCALATE"
        resp["steps"] = []
        resp["follow_up_questions"] = []
        resp["youtube_urls"] = []
        return resp

    # 🧠 Multi-cause → ASK
    if obd["multi_cause"]:
        resp["action"] = "ASK"
        resp["steps"] = []
        resp["youtube_urls"] = []

        if not resp.get("follow_up_questions"):
            resp["follow_up_questions"] = [
                "Does the engine idle smoothly or feel rough?",
                "Do you hear any hissing sounds from the engine bay?",
                "Did this issue start suddenly or gradually?",
            ]

    return resp


# -----------------------------
# State enforcement
# -----------------------------

def enforce_state_machine(resp: dict) -> dict:
    # 🚫 DIY without steps is forbidden
    if resp["action"] == "DIY" and not resp["steps"]:
        resp["action"] = "ASK"
        resp["steps"] = []
        resp["youtube_urls"] = []

        if not resp["follow_up_questions"]:
            resp["follow_up_questions"] = [
                "Can you describe any other symptoms you notice?",
                "Does the issue happen all the time or only sometimes?",
            ]

    return resp


# -----------------------------
# Main entry point
# -----------------------------

def run_vehicle_agent(
    user_input: str,
    chat_id: UUID,
    user_id: str,
    vehicle_id: str | None = None,
) -> dict:

    history = load_short_term_memory(chat_id, limit=5) or "No prior conversation."

    messages = prompt.format_messages(
        conversation_history=history,
        user_input=user_input,
    )

    ai_text = llm.invoke(messages).content

    save_chat_turn(
        chat_id=chat_id,
        user_id=user_id,
        vehicle_id=vehicle_id,
        prompt=user_input,
        response_ai=ai_text,
    )

    try:
        parsed = json.loads(ai_text)

        parsed = normalize_agent_response(parsed, history)
        parsed = apply_obd_logic(parsed, user_input)
        parsed = enforce_state_machine(parsed)

        # 📺 YouTube ONLY when DIY + steps exist
        if parsed["action"] == "DIY" and parsed["steps"] and not parsed["youtube_urls"]:
            parsed["youtube_urls"] = web_search_youtube(parsed["diagnosis"])

        return parsed

    except Exception:
        return {
            "diagnosis": "Unable to safely identify the issue",
            "explanation": "I could not clearly understand the problem.",
            "severity": 0.8,
            "action": "ESCALATE",
            "steps": [],
            "follow_up_questions": [],
            "youtube_urls": [],
            "confidence": 0.2,
        }
