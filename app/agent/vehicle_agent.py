import json
from langchain_groq import ChatGroq # type: ignore
from langchain_core.messages import SystemMessage, HumanMessage # type: ignore
from app.config import GROQ_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt
from app.db.db import load_short_term_memory, save_chat_turn

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.2
)


def run_vehicle_agent(
    user_input: str,
    chat_id: str,
    user_id: str,
    vehicle_id: str | None = None
) -> dict:

    # 1️⃣ Load previous conversation (string)
    conversation_history = load_short_term_memory(chat_id, limit=5)
    if not conversation_history:
        conversation_history = "No prior conversation."

    # 2️⃣ Build system prompt
    prompt = vehicle_prompt.format(
        conversation_history=conversation_history,
        user_input=user_input
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content="Respond strictly in JSON.")
    ]

    # 3️⃣ Call LLM
    response = llm.invoke(messages)
    ai_text = response.content

    # 4️⃣ Save this chat turn (user + AI)
    save_chat_turn(
        chat_id=chat_id,
        user_id=user_id,
        vehicle_id=vehicle_id,
        prompt=user_input,
        response_ai=ai_text
    )

    # 5️⃣ Parse AI response safely
    try:
        return json.loads(ai_text)
    except json.JSONDecodeError:
        return {
            "diagnosis": "Unknown issue",
            "explanation": "The issue could not be safely identified.",
            "severity": 0.8,
            "action": "ESCALATE",
            "steps": [],
            "follow_up_question": "",
            "confidence": 0.2
        }
