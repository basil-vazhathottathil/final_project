import json
import re
from uuid import UUID, uuid4
from typing import List, Dict, Any

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import GROQ_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.db.db import (
    load_short_term_memory,
    load_short_term_memory_structured,
    save_chat_turn,
)

# --------------------------------------------------
# Constants
# --------------------------------------------------

SWAGGER_DUMMY_UUID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
]

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
            "Conversation history:\n{conversation_history}\n\nUser update:\n{user_input}",
        ),
    ]
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def safe_json_extract(text: str) -> Dict[str, Any] | None:
    """
    Tolerant JSON extractor – handles extra text before/after JSON.
    """
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
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

    resp["severity"] = float(resp["severity"])
    resp["confidence"] = float(resp["confidence"])

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


def get_last_agent_action(history: List[Dict[str, Any]]) -> str | None:
    for turn in reversed(history):
        agent = turn.get("agent")
        if agent:
            return agent.get("action")
    return None


def get_active_diagnosis(history: List[Dict[str, Any]]) -> str | None:
    """
    Retrieves the most recent diagnosis to maintain continuity.
    """
    for turn in reversed(history):
        agent = turn.get("agent")
        if agent and agent.get("diagnosis"):
            return agent["diagnosis"]
    return None


def count_consecutive_escalates(history: List[Dict[str, Any]], limit: int = 5) -> int:
    count = 0
    for turn in reversed(history[-limit:]):
        agent = turn.get("agent")
        if agent and agent.get("action") == "ESCALATE":
            count += 1
        else:
            break
    return count


# --------------------------------------------------
# Workshop response
# --------------------------------------------------

def build_workshop_response(chat_id: UUID) -> Dict[str, Any]:
    return {
        "diagnosis": "Professional assistance recommended",
        "explanation": "Here are nearby workshops that can help with this issue.",
        "severity": 1.0,
        "action": "WORKSHOP_RESULTS",
        "steps": [],
        "follow_up_questions": [],
        "confidence": 0.9,
        "chat_id": str(chat_id),
    }


# --------------------------------------------------
# Main agent entry
# --------------------------------------------------

def run_vehicle_agent(
    user_input: str,
    chat_id: UUID | None,
    user_id: str,
    vehicle_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Dict[str, Any]:

    # Backend owns chat_id
    if chat_id is None or chat_id == SWAGGER_DUMMY_UUID:
        chat_id = uuid4()

    history_text = load_short_term_memory(chat_id, limit=10)
    history_structured = load_short_term_memory_structured(chat_id, limit=10)

    last_action = get_last_agent_action(history_structured)
    escalate_count = count_consecutive_escalates(history_structured)
    active_diagnosis = get_active_diagnosis(history_structured)

    text = user_input.lower()

    # --------------------------------------------------
    # Direct workshop intent
    # --------------------------------------------------
    if any(k in text for k in WORKSHOP_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    # --------------------------------------------------
    # YES handling
    # --------------------------------------------------
    if last_action == "ESCALATE" and any(y in text for y in YES_PATTERNS):
        response = {
            "diagnosis": active_diagnosis or "Professional help recommended",
            "explanation": "Based on the issue, a professional inspection is advisable.",
            "severity": 0.85,
            "action": "CONFIRM_WORKSHOP",
            "steps": [],
            "follow_up_questions": [
                "This issue might be severe. I recommend a workshop. Would you like me to find nearby workshops?"
            ],
            "confidence": 0.85,
            "chat_id": str(chat_id),
        }
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    if last_action == "CONFIRM_WORKSHOP" and any(y in text for y in YES_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    # --------------------------------------------------
    # DIY SHORT-CIRCUIT: Battery corrosion
    # --------------------------------------------------
    if "corrosion" in text and "battery" in text:
        response = {
            "diagnosis": "Battery terminal corrosion",
            "explanation": "Corrosion can block electrical flow and prevent starting.",
            "severity": 0.4,
            "action": "DIY",
            "steps": [
                "Turn off the car and remove the keys",
                "Disconnect the negative terminal first",
                "Clean corrosion using baking soda and water",
                "Reconnect terminals securely"
            ],
            "follow_up_questions": [],
            "youtube_urls": [
                "https://www.youtube.com/watch?v=YC--MLNIbik"
            ],
            "confidence": 0.9,
            "chat_id": str(chat_id),
        }
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    # --------------------------------------------------
    # LLM flow with context injection
    # --------------------------------------------------

    combined_input = user_input
    if active_diagnosis:
        combined_input = f"Current diagnosis: {active_diagnosis}\nUser update: {user_input}"

    messages = prompt.format_messages(
        conversation_history=history_text,
        user_input=combined_input,
    )

    try:
        ai_text = llm.invoke(messages).content
        parsed = safe_json_extract(ai_text)
        if not parsed:
            raise ValueError("Invalid JSON from model")

        parsed = normalize_agent_response(parsed)

        # --------------------------------------------------
        # HARD STATE ENFORCEMENT
        # --------------------------------------------------

        # Auto-upgrade ESCALATE → CONFIRM_WORKSHOP after 3 turns
        if parsed["action"] == "ESCALATE" and escalate_count >= 2:
            parsed["action"] = "CONFIRM_WORKSHOP"
            parsed["follow_up_questions"] = [
                "This issue has persisted and likely needs professional help. I recommend a workshop. Would you like me to find nearby workshops?"
            ]

        elif parsed["action"] == "ESCALATE":
            parsed["follow_up_questions"] = [
                "Would you like me to find nearby workshops?"
            ]

        elif parsed["action"] == "CONFIRM_WORKSHOP":
            parsed["follow_up_questions"] = [
                "This issue might be severe. I recommend a workshop. Would you like me to find nearby workshops?"
            ]

        parsed["chat_id"] = str(chat_id)

        save_chat_turn(chat_id, user_id, vehicle_id, user_input, parsed)
        return parsed

    except Exception:
        fallback = {
            "diagnosis": active_diagnosis or "Vehicle issue detected",
            "explanation": "Thanks for the update. Let’s continue step by step.",
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
