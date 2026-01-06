import json
import re
from uuid import UUID, uuid4
from typing import List, Tuple, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

from app.config import GROQ_API_KEY, TAVILY_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.agent.vehicle_symptom import SYMPTOM_GUARDS
from app.db.db import (
    load_short_term_memory,
    load_short_term_memory_structured,
    save_chat_turn,
)
from app.data import OBD_CODES


# --------------------------------------------------
# Constants
# --------------------------------------------------

SWAGGER_DUMMY_UUID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
]

### 🔥 NEW: intent patterns
YES_PATTERNS = [
    "yes", "yeah", "yep", "sure", "ok", "okay", "please do", "go ahead"
]

WORKSHOP_PATTERNS = [
    "workshop", "garage", "service center",
    "mechanic", "repair shop", "nearby garage"
]


# --------------------------------------------------
# LLM setup
# --------------------------------------------------

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
            "Conversation history:\n{conversation_history}\n\nUser issue:\n{user_input}",
        ),
    ]
)


# --------------------------------------------------
# Web search
# --------------------------------------------------

tavily = TavilyClient(api_key=TAVILY_API_KEY)


def web_search_possible_causes(query: str) -> List[str]:
    try:
        response = tavily.search(query=f"car {query} causes", max_results=5)
        return [r["content"] for r in response.get("results", []) if r.get("content")]
    except Exception:
        return []


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def extract_obd_codes(text: str) -> List[str]:
    return re.findall(r"\b[PBCU]\d{4}\b", text.upper())


def safe_json_extract(text: str) -> Dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def normalize_agent_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    resp.setdefault("diagnosis", "")
    resp.setdefault("explanation", "")
    resp.setdefault("severity", 0.5)
    resp.setdefault("action", "ASK")
    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", [])
    resp.setdefault("youtube_urls", [])
    resp.setdefault("confidence", 0.5)

    resp["severity"] = float(resp.get("severity", 0.5))
    resp["confidence"] = float(resp.get("confidence", 0.5))

    if resp["action"] == "ASK" and not resp["follow_up_questions"]:
        resp["follow_up_questions"] = GENERIC_FOLLOW_UP_QUESTIONS

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


# --------------------------------------------------
# Context helpers
# --------------------------------------------------

def get_last_agent_action(history: List[Dict[str, Any]]) -> str | None:
    for turn in reversed(history):
        agent = turn.get("agent")
        if agent:
            return agent.get("action")
    return None


# --------------------------------------------------
# Workshop response
# --------------------------------------------------

def build_workshop_response(chat_id: UUID) -> Dict[str, Any]:
    # 🔧 This intentionally does NOT call Google Maps directly here
    # Your existing /vehicle/workshops endpoint should be used by frontend
    return {
        "diagnosis": "Professional assistance recommended",
        "explanation": "I can help you find nearby workshops if you want.",
        "severity": 1.0,
        "action": "WORKSHOP_RESULTS",
        "steps": [],
        "follow_up_questions": [],
        "confidence": 0.9,
        "chat_id": str(chat_id),
    }


# --------------------------------------------------
# Main agent entry (PRODUCTION SAFE)
# --------------------------------------------------

def run_vehicle_agent(
    user_input: str,
    chat_id: UUID | None,
    user_id: str,
    vehicle_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Dict[str, Any]:

    if chat_id is None or chat_id == SWAGGER_DUMMY_UUID:
        chat_id = uuid4()

    history_text = load_short_term_memory(chat_id, limit=5)
    history_structured = load_short_term_memory_structured(chat_id, limit=5)

    last_action = get_last_agent_action(history_structured)
    text = user_input.lower()

    # --------------------------------------------------
    # 🔥 DIRECT WORKSHOP INTENT (skip LLM)
    # --------------------------------------------------
    if any(k in text for k in WORKSHOP_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    # --------------------------------------------------
    # 🔥 CONFIRMATION AFTER ESCALATION
    # --------------------------------------------------
    if last_action in {"ESCALATE", "CONFIRM_WORKSHOP"}:
        if any(y in text for y in YES_PATTERNS):
            response = build_workshop_response(chat_id)
            save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
            return response

    # --------------------------------------------------
    # Normal LLM flow
    # --------------------------------------------------

    messages = prompt.format_messages(
        conversation_history=history_text,
        user_input=user_input,
    )

    try:
        ai_text = llm.invoke(messages).content
        parsed = safe_json_extract(ai_text)
        if not parsed:
            raise ValueError("Invalid JSON from model")

        parsed = normalize_agent_response(parsed)

        # Escalation → confirmation question
        if parsed["action"] == "ESCALATE":
            parsed["action"] = "CONFIRM_WORKSHOP"
            parsed["follow_up_questions"] = [
                "Would you like me to find nearby workshops?"
            ]

        parsed["chat_id"] = str(chat_id)

        save_chat_turn(chat_id, user_id, vehicle_id, user_input, parsed)
        return parsed

    except Exception:
        fallback = {
            "diagnosis": "Vehicle issue detected",
            "explanation": "Thanks for the details. Let’s continue step by step.",
            "severity": 0.6,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": GENERIC_FOLLOW_UP_QUESTIONS,
            "youtube_urls": [],
            "confidence": 0.6,
            "chat_id": str(chat_id),
        }

        save_chat_turn(chat_id, user_id, vehicle_id, user_input, fallback)
        return fallback
