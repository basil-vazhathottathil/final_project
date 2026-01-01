import json
from uuid import UUID
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

from app.config import GROQ_API_KEY, TAVILY_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.db.db import load_short_term_memory, save_chat_turn


if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")


# -----------------------------
# Constants
# -----------------------------

CONFIDENCE_LOCK_THRESHOLD = 0.75

OBD_MULTI_CAUSE_CODES = {
    "P0171",
    "P0174",
}


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

GENERAL_WEB_INTENT_KEYWORDS = [
    "latest",
    "news",
    "recall",
    "price",
    "cost",
    "cause",
    "meaning",
    "why",
    "what is",
    "info",
    "details",
]


def wants_youtube(text: str) -> bool:
    return any(k in text.lower() for k in YOUTUBE_INTENT_KEYWORDS)


def wants_web_search(text: str) -> bool:
    return any(k in text.lower() for k in GENERAL_WEB_INTENT_KEYWORDS)


def web_search_general(query: str) -> str:
    response = tavily.search(query=query, max_results=5)
    results = []

    for r in response.get("results", []):
        title = r.get("title")
        url = r.get("url")
        content = r.get("content")
        if title and url and content:
            results.append(f"- {title}: {content} ({url})")

    return "\n".join(results)


def web_search_youtube(query: str) -> List[str]:
    response = tavily.search(
        query=f"site:youtube.com {query}",
        max_results=5,
    )

    videos = []
    for r in response.get("results", []):
        title = r.get("title")
        url = r.get("url")
        if title and url:
            videos.append(url)

    return videos


# -----------------------------
# Helpers
# -----------------------------

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

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


def enforce_state_machine(resp: dict, user_input: str) -> dict:
    """
    HARD GUARDRails:
    - No DIY without steps
    - OBD multi-cause codes must ASK first
    """

    action = resp.get("action")

    # 🚫 DIY without steps → ASK
    if action == "DIY" and not resp.get("steps"):
        resp["action"] = "ASK"
        resp["steps"] = []
        resp["youtube_urls"] = []

        if not resp.get("follow_up_questions"):
            resp["follow_up_questions"] = [
                "Does the engine idle smoothly or feel rough?",
                "Do you hear any hissing sounds from the engine bay?",
                "Did this issue start suddenly or gradually?",
            ]

    # 🚗 OBD multi-cause codes must ASK first
    if any(code in user_input.upper() for code in OBD_MULTI_CAUSE_CODES):
        if resp["action"] == "DIY" and not resp.get("steps"):
            resp["action"] = "ASK"

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

    # 🌐 Intent-aware web search
    web_context = ""

    if wants_youtube(user_input):
        yt_results = web_search_youtube(user_input)
        if yt_results:
            web_context = (
                "The user asked for video tutorials. "
                "Use ONLY the YouTube links below.\n"
                + "\n".join(yt_results)
            )

    elif wants_web_search(user_input):
        web_results = web_search_general(user_input)
        if web_results:
            web_context = (
                "The following information comes from live internet search results. "
                "Use these facts accurately.\n"
                + web_results
            )

    messages = prompt.format_messages(
        conversation_history=history,
        user_input=f"{user_input}\n\n{web_context}",
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
        parsed = enforce_state_machine(parsed, user_input)

        # 📺 Inject YouTube ONLY when DIY + steps exist
        if parsed["action"] == "DIY" and parsed["steps"] and not parsed["youtube_urls"]:
            parsed["youtube_urls"] = web_search_youtube(parsed["diagnosis"])

        return parsed

    except json.JSONDecodeError:
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
