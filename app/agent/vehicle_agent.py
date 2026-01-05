import json
import re
from uuid import UUID
from typing import List, Tuple

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import GROQ_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.agent.vehicle_symptom import SYMPTOM_GUARDS
from app.agent.tools import get_tools
from app.db.db import load_short_term_memory, save_chat_turn
from app.data import OBD_CODES


DIY_CONFIDENCE_MIN = 0.7

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
]

ALLOWED_ACTIONS = {"DIY", "ASK", "ESCALATE", "FIND_WORKSHOPS"}


tools = get_tools()

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.2,
).bind_tools(tools)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", vehicle_prompt),
        (
            "human",
            "Conversation history:\n{conversation_history}\n\nUser issue:\n{user_input}",
        ),
    ]
)


def extract_obd_codes(text: str) -> List[str]:
    return re.findall(r"\b[PBCU]\d{4}\b", text.upper())


def normalize_agent_response(resp: dict) -> dict:
    resp.setdefault("diagnosis", "")
    resp.setdefault("explanation", "")
    resp.setdefault("severity", 0.5)
    resp.setdefault("action", "ASK")
    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", [])
    resp.setdefault("youtube_urls", [])
    resp.setdefault("confidence", 0.5)

    if resp["action"] not in ALLOWED_ACTIONS:
        resp["action"] = "ASK"

    if resp["action"] == "ASK" and not resp["follow_up_questions"]:
        resp["follow_up_questions"] = GENERIC_FOLLOW_UP_QUESTIONS

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


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


def apply_symptom_guard(resp: dict, user_input: str) -> Tuple[dict, bool]:
    text = user_input.lower()
    for s in SYMPTOM_GUARDS.values():
        if any(k in text for k in s["keywords"]):
            resp["diagnosis"] = s["diagnosis"]
            resp["explanation"] = s["explanation"]
            resp["follow_up_questions"] = s["questions"]
            resp["confidence"] = max(resp.get("confidence", 0.3), s["confidence"])
            resp["action"] = "ASK"
            return resp, True
    return resp, False


def run_vehicle_agent(
    user_input: str,
    chat_id: UUID,
    user_id: str,
    vehicle_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:

    history = load_short_term_memory(chat_id, limit=5) or ""

    location_context = ""
    if latitude is not None and longitude is not None:
        location_context = (
            f"\nUser location:\nlatitude={latitude}\nlongitude={longitude}\n"
        )

    messages = prompt.format_messages(
        conversation_history=history + location_context,
        user_input=user_input,
    )

    try:
        ai_msg = llm.invoke(messages)

        tool_calls = getattr(ai_msg, "additional_kwargs", {}).get("tool_calls", [])

        if tool_calls:
            tool_output = ai_msg.content or ""
            save_chat_turn(chat_id, user_id, vehicle_id, user_input, tool_output)
            return normalize_agent_response(
                {
                    "diagnosis": "",
                    "explanation": tool_output,
                    "severity": 0.0,
                    "action": "FIND_WORKSHOPS",
                    "confidence": 0.6,
                }
            )

        ai_text = ai_msg.content
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, ai_text)

        parsed = normalize_agent_response(json.loads(ai_text))

        workshop_intent = any(
            k in user_input.lower()
            for k in ["workshop", "garage", "mechanic", "service center"]
        )

        if workshop_intent:
            if latitude is None or longitude is None:
                parsed["action"] = "ASK"
                parsed["follow_up_questions"] = [
                    "Please allow location access so I can find nearby workshops."
                ]
            else:
                parsed["action"] = "FIND_WORKSHOPS"
                parsed["severity"] = 0.0
                parsed["diagnosis"] = ""
            return normalize_agent_response(parsed)

        parsed = apply_obd_logic(parsed, user_input)
        parsed, _ = apply_symptom_guard(parsed, user_input)

        if parsed["action"] == "DIY" and parsed["confidence"] < DIY_CONFIDENCE_MIN:
            parsed["action"] = "ESCALATE"
            parsed["steps"] = []
            parsed["youtube_urls"] = []
            parsed["explanation"] += (
                "\n\nI’m not confident this can be safely fixed at home."
            )

        return normalize_agent_response(parsed)

    except Exception:
        return {
            "diagnosis": "Vehicle issue detected (needs clarification)",
            "explanation": "I may not have understood everything correctly yet. Let’s continue step by step.",
            "severity": 0.4,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": GENERIC_FOLLOW_UP_QUESTIONS,
            "youtube_urls": [],
            "confidence": 0.4,
        }
