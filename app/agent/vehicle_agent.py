import json
from uuid import UUID, uuid4
from typing import List, Dict, Any

from langchain_groq import ChatGroq  # type: ignore
from langchain_core.prompts import ChatPromptTemplate  # type: ignore

from app.config import GROQ_API_KEY
from app.agent.prompts.vehicle_prompt import vehicle_prompt
from app.db.db import (
    load_short_term_memory,
    load_short_term_memory_structured,
    save_chat_turn,
)

# AI memory helpers
from app.db.ai_memory import (
    load_chat_summary,                 # ai_chat_summary (chat-level)
    load_chat_issue_summary,           # issues_summary (chat-level)
    upsert_chat_issue_summary,         # ai_chat_summary upsert
    load_open_issues,
    upsert_issue_from_summary,         # vehicle-level issues_summary
)

from app.agent.prompts.summary_prompt import build_summary_prompt
from app.agent.prompts.issue_prompt import build_issue_prompt


# Constants
SWAGGER_DUMMY_UUID = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")

GENERIC_FOLLOW_UP_QUESTIONS = [
    "Can you describe the issue in your own words?",
    "When did you first notice this?",
    "Does it happen all the time or only in certain situations?",
]

WORKSHOP_PATTERNS = [
    "workshop", "garage", "service center",
    "mechanic", "repair shop", "nearby garage"
]


# LLM setup
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.2,
)

SYSTEM_PROMPT = f"""
{vehicle_prompt}

CRITICAL INSTRUCTION:
- You MUST respond in valid JSON ONLY
- Do NOT add explanations outside JSON
- Do NOT use markdown
- JSON must match the required schema exactly
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Conversation history:\n{conversation_history}\n\nUser update:\n{user_input}",
        ),
    ]
)


# Helper functions
def safe_json_extract(text: str) -> Dict[str, Any] | None:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None


def normalize_agent_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    resp.setdefault("diagnosis", "Vehicle issue detected")
    resp.setdefault("explanation", "Let’s continue step by step.")
    resp.setdefault("severity", 0.5)
    resp.setdefault("action", "ASK")
    resp.setdefault("steps", [])
    resp.setdefault("follow_up_questions", GENERIC_FOLLOW_UP_QUESTIONS)
    resp.setdefault("youtube_urls", [])
    resp.setdefault("confidence", 0.5)

    resp["severity"] = float(resp["severity"])
    resp["confidence"] = float(resp["confidence"])

    if resp["action"] != "DIY":
        resp["steps"] = []
        resp["youtube_urls"] = []

    return resp


def compute_cumulative_confidence(previous: float | None, current: float) -> float:
    if previous is None:
        return round(current, 2)
    return round((previous * 0.6) + (current * 0.4), 2)


def count_consecutive_escalates(history: List[Dict[str, Any]], limit: int = 5) -> int:
    count = 0
    for turn in reversed(history[-limit:]):
        agent = turn.get("agent")
        if agent and agent.get("action") == "ESCALATE":
            count += 1
        else:
            break
    return count


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


# Main agent entry
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

    history_text = load_short_term_memory(chat_id, limit=10)
    history_structured = load_short_term_memory_structured(chat_id, limit=10)
    escalate_count = count_consecutive_escalates(history_structured)

    vehicle_chat_summary = load_chat_summary(vehicle_id)
    chat_conversation_summary = load_chat_summary(str(chat_id))
    if not chat_conversation_summary:
        chat_conversation_summary = ""  # Default to an empty string if None or invalid

    chat_issue_summary = load_chat_issue_summary(str(chat_id))
    open_issues = load_open_issues(vehicle_id)

    text = user_input.lower()
    if any(k in text for k in WORKSHOP_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    context_blocks = []

    if vehicle_chat_summary:
        context_blocks.append(f"Vehicle history:\n{vehicle_chat_summary}")

    if chat_conversation_summary:
        context_blocks.append(f"Conversation summary:\n{chat_conversation_summary}")

    if chat_issue_summary:
        context_blocks.append(f"Current diagnosed issue:\n{chat_issue_summary}")

    if open_issues:
        context_blocks.append(
            "Known unresolved issues:\n"
            + "\n".join(f"- {i['title']} (severity: {i['severity']})" for i in open_issues)
        )

    combined_input = user_input
    if context_blocks:
        combined_input = "\n\n".join(context_blocks) + f"\n\nUser update:\n{user_input}"

    messages = prompt.format_messages(
        conversation_history=history_text,
        user_input=combined_input,
    )

    try:
        ai_text = llm.invoke(messages).content
        parsed = safe_json_extract(ai_text)

        if not parsed:
            raise ValueError("Model did not return JSON")

        parsed = normalize_agent_response(parsed)

        previous_confidence = None
        if history_structured:
            last_agent = history_structured[-1].get("agent")
            if isinstance(last_agent, dict):
                previous_confidence = last_agent.get("confidence")

        parsed["confidence"] = compute_cumulative_confidence(
            previous_confidence,
            parsed["confidence"]
        )

        if parsed["action"] == "ESCALATE" and escalate_count >= 2:
            parsed["action"] = "CONFIRM_WORKSHOP"
            parsed["follow_up_questions"] = [
                "This issue has persisted and likely needs professional help. Would you like me to find nearby workshops?"
            ]

        parsed["chat_id"] = str(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, parsed)

        # Update ai_chat_summary incrementally
        new_turn_text = f"User: {user_input}\nAgent: {parsed['explanation']}"

        summary_prompt = build_summary_prompt(
            previous_summary=chat_conversation_summary,
            new_turn=new_turn_text,
        )

        updated_chat_summary = llm.invoke(summary_prompt).content.strip()

        if updated_chat_summary and len(updated_chat_summary) > 20:
            upsert_chat_issue_summary(
                chat_id=str(chat_id),
                vehicle_id=vehicle_id,
                summary=updated_chat_summary,
                severity=None,
            )

        # Promote to issues_summary when confident
        if (
            updated_chat_summary
            and parsed["confidence"] >= 0.7
            and parsed["action"] in {"ESCALATE", "CONFIRM_WORKSHOP"}
        ):
            issue_prompt = build_issue_prompt(updated_chat_summary)
            issue_json = safe_json_extract(llm.invoke(issue_prompt).content)
            if issue_json:
                upsert_issue_from_summary(vehicle_id, issue_json)

        return parsed

    except Exception:
        fallback = {
            "diagnosis": "Vehicle issue detected",
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
