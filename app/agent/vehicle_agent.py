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

from app.db.ai_memory import (
    load_chat_summary,
    upsert_chat_summary,
    load_chat_issue_summary,
    load_open_issues,
    upsert_issue_from_summary,
)

from app.agent.prompts.summary_prompt import build_summary_prompt
from app.agent.prompts.issue_prompt import build_issue_prompt
from app.agent.tools.youtube_search import search_youtube_videos
from app.agent.tools.web_search import get_web_search_tool


# Dummy UUID used by Swagger
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
    model="moonshotai/kimi-k2-instruct-0905",
    temperature=0.2,
)

SYSTEM_PROMPT = f"""
{vehicle_prompt}

CRITICAL INSTRUCTION:
- JSON ONLY
- No markdown
- No extra text
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


# -------------------- Helpers --------------------

def safe_json_extract(text: str) -> Dict[str, Any] | None:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end])
    except Exception:
        return None


def json_safe(obj: Any) -> Any:
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj


def normalize_agent_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    resp.setdefault("internal_reasoning", "Diagnostic logic performed.")
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


def build_workshop_response(chat_id: str) -> Dict[str, Any]:
    return {
        "diagnosis": "Professional assistance recommended",
        "explanation": "Here are nearby workshops that can help with this issue.",
        "severity": 1.0,
        "action": "WORKSHOP_RESULTS",
        "steps": [],
        "follow_up_questions": [],
        "confidence": 0.9,
        "chat_id": chat_id,
    }


# -------------------- Main Agent --------------------

def run_vehicle_agent(
    user_input: str,
    chat_id: str | None,
    user_id: str,
    vehicle_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Dict[str, Any]:

    if chat_id is None or chat_id == str(SWAGGER_DUMMY_UUID):
        chat_id = str(uuid4())

    history_text = load_short_term_memory(chat_id, limit=10)
    history_structured = load_short_term_memory_structured(chat_id, limit=10)

    chat_summary = load_chat_summary(chat_id) or ""
    chat_issue_summary = load_chat_issue_summary(chat_id)
    open_issues = load_open_issues(vehicle_id)

    if any(k in user_input.lower() for k in WORKSHOP_PATTERNS):
        response = build_workshop_response(chat_id)
        save_chat_turn(
            chat_id,
            user_id,
            vehicle_id,
            user_input,
            json_safe(response),
        )
        return response

    context_blocks = []

    if chat_summary:
        context_blocks.append(f"Conversation summary:\n{chat_summary}")

    if chat_issue_summary:
        context_blocks.append(f"Current issue:\n{chat_issue_summary}")

    if open_issues:
        context_blocks.append(
            "Known unresolved issues:\n"
            + "\n".join(f"- {i['title']} (severity: {i['severity']})" for i in open_issues)
        )

    combined_input = (
        "\n\n".join(context_blocks) + f"\n\nUser update:\n{user_input}"
        if context_blocks
        else user_input
    )

    messages = prompt.format_messages(
        conversation_history=history_text,
        user_input=combined_input,
    )

    try:
        ai_text = llm.invoke(messages).content

        parsed = safe_json_extract(ai_text) or {}
        parsed = normalize_agent_response(parsed)

        # Cross-Verification Search (Enhancement Option 3)
        if parsed.get("confidence", 0) < 0.7 and parsed.get("diagnosis"):
            search_tool = get_web_search_tool()
            query = f"{parsed['diagnosis']} car symptoms verification repair guide"
            
            try:
                search_results = search_tool.invoke(query)
                # Extract snippets for the LLM
                results_text = "\n".join(
                    [f"- {r.get('content', r.get('url'))}" for r in search_results[:3]]
                )
                
                verification_input = (
                    f"{combined_input}\n\n"
                    f"ADDITIONAL VERIFIED DATA FROM WEB SEARCH:\n{results_text}\n\n"
                    f"Please re-evaluate your diagnosis and confidence based on this new data."
                )
                
                messages_v2 = prompt.format_messages(
                    conversation_history=history_text,
                    user_input=verification_input,
                )
                ai_text_v2 = llm.invoke(messages_v2).content
                parsed_v2 = safe_json_extract(ai_text_v2) or {}
                parsed = normalize_agent_response(parsed_v2)
            except Exception as e:
                print(f"Verification search failed: {e}")

        previous_confidence = None
        if history_structured:
            last_agent = history_structured[-1].get("agent")
            if isinstance(last_agent, dict):
                previous_confidence = last_agent.get("confidence")

        parsed["confidence"] = compute_cumulative_confidence(
            previous_confidence,
            parsed["confidence"]
        )

        # YouTube DIY Search
        if parsed["action"] == "DIY" and parsed["confidence"] >= 0.7:
            diagnosis = parsed.get("diagnosis", "")
            if diagnosis:
                videos = search_youtube_videos(diagnosis)
                parsed["youtube_urls"] = videos

        parsed["chat_id"] = chat_id

        save_chat_turn(
            chat_id,
            user_id,
            vehicle_id,
            user_input,
            json_safe(parsed),
        )

        new_turn = f"User: {user_input}\nAgent: {parsed['explanation']}"

        summary_prompt = build_summary_prompt(
            previous_summary=chat_summary,
            new_turn=new_turn,
        )

        updated_summary = llm.invoke(summary_prompt).content.strip()

        if updated_summary and len(updated_summary) > 20:
            upsert_chat_summary(
                chat_id=chat_id,
                vehicle_id=vehicle_id,
                summary=updated_summary,
            )

        if (
            updated_summary
            and parsed["confidence"] >= 0.7
            and parsed["action"] in {"ESCALATE", "CONFIRM_WORKSHOP"}
        ):
            issue_prompt = build_issue_prompt(updated_summary)
            issue_json = safe_json_extract(llm.invoke(issue_prompt).content)

            if issue_json:
                upsert_issue_from_summary(
                    vehicle_id=vehicle_id,
                    chat_id=chat_id,
                    issue=issue_json,
                )

        return parsed

    except Exception as e:
        fallback = {
            "diagnosis": "Vehicle issue detected",
            "explanation": "Thanks for the update. Let’s continue step by step.",
            "severity": 0.6,
            "action": "ASK",
            "steps": [],
            "follow_up_questions": GENERIC_FOLLOW_UP_QUESTIONS,
            "youtube_urls": [],
            "confidence": 0.6,
            "chat_id": chat_id,
        }

        save_chat_turn(
            chat_id,
            user_id,
            vehicle_id,
            user_input,
            json_safe(fallback),
        )

        return fallback
