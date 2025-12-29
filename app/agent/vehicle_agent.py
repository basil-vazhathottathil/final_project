import json
from langchain_groq import ChatGroq # type: ignore
from langchain_core.messages import SystemMessage, HumanMessage # type: ignore
from app.config import GROQ_API_KEY
from app.agent.vehicle_prompt import vehicle_prompt

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.2
)

def run_vehicle_agent(user_input: str, conversation_history: str = "") -> dict:
    prompt = vehicle_prompt.format(
        conversation_history=conversation_history or "None",
        user_input=user_input
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content="Respond strictly in JSON.")
    ]

    response = llm.invoke(messages)

    try:
        return json.loads(response.content)
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
