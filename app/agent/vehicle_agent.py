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

# Swagger auto-injected UUID (must never be trusted)
SWAGGER_DUMMY_UUID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
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
# Progression logic
# --------------------------------------------------

def reduces_uncertainty(user_input: str) -> bool:
    text = user_input.lower()
    markers = [
        "yes", "no", "only", "when", "while",
        "manual", "automatic",
        "stiff", "loose", "hard", "soft",
        "noise", "grind", "grinding",
        "won't", "can't",
    ]
    return any(k in text for k in markers)


def remove_redundant_questions(questions: List[str], user_input: str) -> List[str]:
    text = user_input.lower()
    return [
        q for q in questions
        if not any(word in text for word in q.lower().split())
    ]


def get_active_context(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    for turn in reversed(history):
        agent = turn.get("agent")
        if agent and agent.get("action") == "ASK":
            return {
                "diagnosis": agent.get("diagnosis"),
                "confidence": agent.get("confidence", 0.5),
            }
    return {}


# --------------------------------------------------
# OBD logic
# --------------------------------------------------

def apply_obd_logic(resp: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    codes = extract_obd_codes(user_input)
    if not codes:
        return resp

    obd = OBD_CODES.get(codes[0])
    if not obd:
        return resp

    resp["diagnosis"] = f"{codes[0]}: {obd['meaning']}"
    resp["explanation"] = obd["description"]

    if not obd["diy_possible"]:
        resp["action"] = "ESCALATE"
        resp["confidence"] = 0.9
    elif obd["multi_cause"]:
        resp["action"] = "ASK"

    return resp


# --------------------------------------------------
# Symptom guard
# --------------------------------------------------

def apply_symptom_guard(resp: Dict[str, Any], text: str) -> Tuple[Dict[str, Any], bool]:
    text = text.lower()

    for symptom in SYMPTOM_GUARDS.values():
        if any(k in text for k in symptom["keywords"]):
            resp["diagnosis"] = symptom["diagnosis"]
            resp["explanation"] = symptom["explanation"]
            resp["follow_up_questions"] = symptom["questions"]
            resp["confidence"] = max(resp["confidence"], symptom["confidence"])
            resp["action"] = "ASK"
            return resp, True

    return resp, False


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

    # 🔐 BACKEND OWNS CHAT ID
    if chat_id is None or chat_id == SWAGGER_DUMMY_UUID:
        chat_id = uuid4()

    history_text = load_short_term_memory(chat_id, limit=5)
    history_structured = load_short_term_memory_structured(chat_id, limit=5)

    active = get_active_context(history_structured)

    combined_input = user_input
    if active.get("diagnosis"):
        combined_input = f"{active['diagnosis']}\n{user_input}"

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
        parsed = apply_obd_logic(parsed, user_input)
        parsed, _ = apply_symptom_guard(parsed, combined_input)

        if parsed["action"] == "ASK" and reduces_uncertainty(user_input):
            parsed["confidence"] = min(parsed["confidence"] + 0.15, 0.95)
            parsed["follow_up_questions"] = remove_redundant_questions(
                parsed["follow_up_questions"],
                user_input,
            )

        if parsed["confidence"] > 0.85 and parsed["action"] == "ASK":
            parsed["action"] = "ESCALATE"

        parsed["chat_id"] = str(chat_id)

        save_chat_turn(chat_id, user_id, vehicle_id, user_input, parsed)
        return parsed

    except Exception:
        fallback = {
            "diagnosis": active.get("diagnosis", "Vehicle issue detected"),
            "explanation": "Thanks for the details. Let’s continue step by step.",
            "severity": 0.6,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": GENERIC_FOLLOW_UP_QUESTIONS,
            "youtube_urls": [],
            "confidence": active.get("confidence", 0.6),
            "chat_id": str(chat_id),
        }

        save_chat_turn(chat_id, user_id, vehicle_id, user_input, fallback)
        return fallback
