import json
import re
from uuid import UUID
from typing import List, Tuple

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

from app.config import GROQ_API_KEY, TAVILY_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.agent.vehicle_symptom import SYMPTOM_GUARDS
from app.db.db import load_short_term_memory, save_chat_turn
from app.data import OBD_CODES


# -----------------------------
# Configuration
# -----------------------------

WEB_SEARCH_CONFIDENCE_THRESHOLD = 0.65
RAW_QUERY_CONFIDENCE_THRESHOLD = 0.35

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
]

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


def web_search_possible_causes(query: str) -> List[str]:
    try:
        response = tavily.search(
            query=f"car {query} causes",
            max_results=5,
        )
        return [
            r.get("content", "").strip()
            for r in response.get("results", [])
            if r.get("content")
        ]
    except Exception:
        return []


def web_search_from_raw_query(query: str) -> List[str]:
    try:
        response = tavily.search(
            query=f"car problem {query}",
            max_results=5,
        )
        return [
            r.get("content", "").strip()
            for r in response.get("results", [])
            if r.get("content")
        ]
    except Exception:
        return []


# -----------------------------
# Helpers
# -----------------------------

def extract_obd_codes(text: str) -> List[str]:
    return re.findall(r"\b[PBCU]\d{4}\b", text.upper())


def normalize_agent_response(resp: dict, history: str) -> dict:
    resp.setdefault("diagnosis", "")
    resp.setdefault("explanation", "")
    resp.setdefault("severity", 0.5)
    resp.setdefault("action", "ASK")
    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", [])
    resp.setdefault("youtube_urls", [])
    resp.setdefault("confidence", 0.5)

    if resp["action"] == "ASK" and not resp["follow_up_questions"]:
        resp["follow_up_questions"] = GENERIC_FOLLOW_UP_QUESTIONS

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


# -----------------------------
# OBD logic
# -----------------------------

def apply_obd_logic(resp: dict, user_input: str) -> dict:
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
        return resp

    if obd["multi_cause"]:
        resp["action"] = "ASK"

    return resp


# -----------------------------
# Symptom guard
# -----------------------------

def apply_symptom_guard(resp: dict, user_input: str) -> Tuple[dict, bool]:
    text = user_input.lower()

    for symptom in SYMPTOM_GUARDS.values():
        if any(k in text for k in symptom["keywords"]):
            resp["diagnosis"] = symptom["diagnosis"]
            resp["explanation"] = symptom["explanation"]
            resp["follow_up_questions"] = symptom["questions"]
            resp["confidence"] = max(resp.get("confidence", 0.3), symptom["confidence"])
            resp["action"] = "ASK"
            return resp, True

    return resp, False


# -----------------------------
# Web enrichment
# -----------------------------

def enrich_with_snippets(resp: dict, snippets: List[str]) -> dict:
    if not snippets:
        return resp

    resp["explanation"] += "\n\nPossible causes seen in real-world cases:\n"
    for s in snippets[:4]:
        resp["explanation"] += f"- {s}\n"

    resp["confidence"] = max(resp.get("confidence", 0.4), 0.6)
    return resp


# -----------------------------
# Main agent entry
# -----------------------------

def run_vehicle_agent(
    user_input: str,
    chat_id: UUID,
    user_id: str,
    vehicle_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:

    history = load_short_term_memory(chat_id, limit=5) or ""

    messages = prompt.format_messages(
        conversation_history=history,
        user_input=user_input,
    )

    try:
        ai_text = llm.invoke(messages).content
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, ai_text)

        parsed = json.loads(ai_text)

        parsed = normalize_agent_response(parsed, history)
        parsed = apply_obd_logic(parsed, user_input)
        parsed, symptom_matched = apply_symptom_guard(parsed, user_input)

        # 🔍 Symptom-based web search
        if (
            symptom_matched
            and parsed["action"] == "ASK"
            and parsed["confidence"] < WEB_SEARCH_CONFIDENCE_THRESHOLD
            and not extract_obd_codes(user_input)
        ):
            snippets = web_search_possible_causes(parsed["diagnosis"])
            parsed = enrich_with_snippets(parsed, snippets)

        # 🌐 Raw-query fallback search
        if (
            not symptom_matched
            and parsed["action"] == "ASK"
            and parsed["confidence"] < RAW_QUERY_CONFIDENCE_THRESHOLD
            and not extract_obd_codes(user_input)
            and len(user_input.split()) >= 4
        ):
            snippets = web_search_from_raw_query(user_input)
            parsed["diagnosis"] = "Vehicle issue detected (needs clarification)"
            parsed["explanation"] = (
                "Based on similar real-world cases, possible causes include:"
            )
            parsed = enrich_with_snippets(parsed, snippets)

        return normalize_agent_response(parsed, history)

    except Exception:
        return {
            "diagnosis": "Vehicle issue detected (needs clarification)",
            "explanation": (
                "I may not have understood everything correctly yet. "
                "Let’s continue step by step to narrow this down."
            ),
            "severity": 0.4,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": GENERIC_FOLLOW_UP_QUESTIONS,
            "youtube_urls": [],
            "confidence": 0.4,
        }
