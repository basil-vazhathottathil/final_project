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

# Diagnostic memory
from app.db.ai_memory import (
    load_chat_summary,
    upsert_chat_summary,
    load_open_issues,
    upsert_issue_from_summary,
)

from app.agent.prompts.summary_prompt import build_summary_prompt
from app.agent.prompts.issue_prompt import build_issue_prompt


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


def compute_cumulative_confidence(previous: float | None, current: float) -> float:
    if previous is None:
        return round(current, 2)
    return round((previous * 0.6) + (current * 0.4), 2)


def is_persistent_issue(chat_summary: str | None, open_issues: list) -> bool:
    if not chat_summary or not open_issues:
        return False

    summary_lower = chat_summary.lower()
    for issue in open_issues:
        title = issue.get("title", "").lower()
        if title and title in summary_lower:
            return True

    return False


def get_last_agent_action(history: List[Dict[str, Any]]) -> str | None:
    for turn in reversed(history):
        agent = turn.get("agent")
        if agent:
            return agent.get("action")
    return None


def get_active_diagnosis(history: List[Dict[str, Any]]) -> str | None:
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

    if chat_id is None or chat_id == SWAGGER_DUMMY_UUID:
        chat_id = uuid4()

    history_text = load_short_term_memory(chat_id, limit=10)
    history_structured = load_short_term_memory_structured(chat_id, limit=10)

    last_action = get_last_agent_action(history_structured)
    escalate_count = count_consecutive_escalates(history_structured)
    active_diagnosis = get_active_diagnosis(history_structured)

    chat_summary = load_chat_summary(vehicle_id)
    open_issues = load_open_issues(vehicle_id)

    text = user_input.lower()

    # --------------------------------------------------
    # Direct workshop intent
    # --------------------------------------------------
    if any(k in text for k in WORKSHOP_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(chat_id, user_id, vehicle_id, user_input, response)
        return response

    # --------------------------------------------------
    # LLM flow
    # --------------------------------------------------

    context_blocks = []

    if chat_summary:
        context_blocks.append(f"Conversation summary:\n{chat_summary}")

    if open_issues:
        issues_text = "\n".join(
            f"- {i['title']} (severity: {i['severity']})"
            for i in open_issues
        )
        context_blocks.append(f"Known unresolved issues:\n{issues_text}")

    if active_diagnosis:
        context_blocks.append(f"Current diagnosis: {active_diagnosis}")

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
            raise ValueError("Invalid JSON from model")

        parsed = normalize_agent_response(parsed)

        # --------------------------------------------------
        # 🔥 UPGRADE 1: CUMULATIVE CONFIDENCE
        # --------------------------------------------------

        previous_confidence = None
        if history_structured:
            last_agent = history_structured[-1].get("agent")
            if isinstance(last_agent, dict):
                previous_confidence = last_agent.get("confidence")

        parsed["confidence"] = compute_cumulative_confidence(
            previous_confidence,
            parsed["confidence"]
        )

        # --------------------------------------------------
        # 🔥 UPGRADE 2: PERSISTENCE-BASED ESCALATION
        # --------------------------------------------------

        if is_persistent_issue(chat_summary, open_issues):
            parsed["confidence"] = min(1.0, parsed["confidence"] + 0.15)

            if parsed["action"] == "ASK":
                parsed["action"] = "ESCALATE"

        # --------------------------------------------------
        # HARD STATE ENFORCEMENT
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Diagnostic memory updates
        # --------------------------------------------------

        summary_text = chat_summary

        if parsed["confidence"] >= 0.6 or parsed["action"] in {"DIY", "ESCALATE", "CONFIRM_WORKSHOP"}:
            summary_prompt = build_summary_prompt(
                history_structured + [{"user": user_input, "agent": parsed}]
            )
            summary_text = llm.invoke(summary_prompt).content
            upsert_chat_summary(vehicle_id, summary_text)

        if (
            summary_text
            and parsed["confidence"] >= 0.7
            and parsed["action"] in {"DIY", "ESCALATE", "CONFIRM_WORKSHOP"}
        ):
            issue_prompt = build_issue_prompt(summary_text)
            issue_json = safe_json_extract(llm.invoke(issue_prompt).content)
            if issue_json:
                upsert_issue_from_summary(vehicle_id, issue_json)

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
