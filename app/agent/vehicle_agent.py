import json
import re
from uuid import UUID
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient

from app.config import GROQ_API_KEY, TAVILY_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.agent.vehicle_symptom import SYMPTOM_GUARDS
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
    return re.findall(r"\b[PBCU]\d{4}\b", text.upper())


def remove_duplicate_questions(questions: List[str], history: str) -> List[str]:
    return [q for q in questions if q.lower() not in history.lower()]


def normalize_agent_response(resp: dict, history: str) -> dict:
    action = resp.get("action", "ASK")

    if action not in {"DIY", "ASK", "ESCALATE"}:
        resp["action"] = "ASK"

    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", [])
    resp.setdefault("youtube_urls", [])
    resp.setdefault("severity", 0.5)
    resp.setdefault("confidence", 0.5)

    if resp["action"] == "ASK":
        resp["steps"] = []
        resp["youtube_urls"] = []
        resp["follow_up_questions"] = remove_duplicate_questions(
            resp["follow_up_questions"], history
        )

        if not resp["follow_up_questions"]:
            resp["follow_up_questions"] = [
                "Can you describe what the car is doing right now?",
                "Are there any warning lights on the dashboard?",
                "Does this happen while starting, idling, or driving?",
            ]

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


# -----------------------------
# OBD logic (facts layer)
# -----------------------------

def apply_obd_logic(resp: dict, user_input: str) -> dict:
    codes = extract_obd_codes(user_input)
    if not codes:
        return resp

    code = codes[0]
    obd = OBD_CODES.get(code)
    if not obd:
        return resp

    resp["diagnosis"] = f"{code}: {obd['meaning']}"
    resp["explanation"] = obd["description"]

    # 🚨 Safety-critical → hard ESCALATE
    if not obd["diy_possible"]:
        resp["action"] = "ESCALATE"
        resp["steps"] = []
        resp["follow_up_questions"] = []
        resp["youtube_urls"] = []
        resp["confidence"] = max(resp.get("confidence", 0.5), 0.8)
        return resp

    # 🧠 Multi-cause → ASK
    if obd["multi_cause"]:
        resp["action"] = "ASK"
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


# -----------------------------
# Symptom guard (understanding layer)
# -----------------------------

def apply_symptom_guard(resp: dict, user_input: str) -> dict:
    text = user_input.lower()

    for symptom in SYMPTOM_GUARDS.values():
        if any(k in text for k in symptom["keywords"]):
            resp["diagnosis"] = symptom["diagnosis"]
            resp["explanation"] = symptom["explanation"]
            resp["action"] = "ASK"
            resp["steps"] = []
            resp["youtube_urls"] = []
            resp["follow_up_questions"] = symptom["questions"]
            resp["confidence"] = max(
                resp.get("confidence", 0.3),
                symptom["confidence"]
            )
            return resp

    return resp


# -----------------------------
# State enforcement
# -----------------------------

def enforce_state_machine(resp: dict) -> dict:
    if resp["action"] == "DIY" and not resp["steps"]:
        resp["action"] = "ASK"
        resp["steps"] = []
        resp["youtube_urls"] = []

        if not resp.get("follow_up_questions"):
            resp["follow_up_questions"] = [
                "Can you share any other symptoms you notice?",
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

    try:
        ai_text = llm.invoke(messages).content

        save_chat_turn(
            chat_id=chat_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            prompt=user_input,
            response_ai=ai_text,
        )

        parsed = json.loads(ai_text)

        parsed = normalize_agent_response(parsed, history)
        parsed = apply_obd_logic(parsed, user_input)      # facts
        parsed = apply_symptom_guard(parsed, user_input) # symptoms
        parsed = enforce_state_machine(parsed)

        # 🛑 Never block conversation due to understanding failure
        if parsed["action"] == "ESCALATE" and parsed.get("confidence", 1) < 0.4:
            parsed["action"] = "ASK"
            parsed["steps"] = []
            parsed["youtube_urls"] = []
            parsed["follow_up_questions"] = [
                "Can you explain the issue in a bit more detail?",
                "When did this problem first start?",
                "Is the car still drivable right now?",
            ]

        # 📺 YouTube ONLY when DIY + steps exist
        if parsed["action"] == "DIY" and parsed["steps"] and not parsed["youtube_urls"]:
            parsed["youtube_urls"] = web_search_youtube(parsed["diagnosis"])

        return parsed

    except Exception:
        # ⚠️ True understanding failure → ASK, never ESCALATE
        return {
            "diagnosis": "I couldn’t clearly understand the issue yet",
            "explanation": "Let’s try again with a bit more detail so I can help you properly.",
            "severity": 0.3,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": [
                "Can you describe what the car is doing right now?",
                "Are there any warning lights on the dashboard?",
                "Does this happen while starting, idling, or driving?",
            ],
            "youtube_urls": [],
            "confidence": 0.3,
        }
